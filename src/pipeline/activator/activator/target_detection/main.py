import argparse
import json
import logging
import os
import shutil
from datetime import datetime, timezone

import pystac
import requests

from activator.utils.stac_client import STACClient
from .target import cli_parser as inference_parser
from .target import compute


# set a configurable logging level for the entire app
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="[%(relativeCreated)d|%(levelname)s|%(name)s|%(lineno)d] %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger(__name__)

AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-l1-cogs"

COG_COLLECTION_EXTENSIONS = [
    "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
    "https://github.com/azavea/nasa-hyperspectral/tree/master/docs/stac/hsi/json-schema/schema.json",
]

COG_ITEM_EXTENSIONS = COG_COLLECTION_EXTENSIONS + [
    "https://stac-extensions.github.io/projection/v1.0.0/schema.json"
]


def collection_id_to_collection_id(aviris_collection_id, target):
    assert(aviris_collection_id in {'aviris-l1-cogs', 'aviris-l2-cogs'})
    assert(target in {'oil', 'plastic'})
    if aviris_collection_id == "aviris-l1-cogs":
        collection_id = f"aviris-{target}-l1-cogs"
        description = f"{target.capitalize()} Predictions (L1)"
    elif aviris_collection_id == "aviris-l2-cogs":
        collection_id = f"aviris-{target}-l2-cogs"
        description = f"{target.capitalize()} Preditions (L2)"
    return collection_id, description


def get_aviris_cog_collection(aviris_collection_id, target):
    collection_id, description = collection_id_to_collection_id(aviris_collection_id, target)
    collection = pystac.Collection(
        collection_id,
        description,
        pystac.Extent(
            pystac.SpatialExtent([[-180, -90, 180, 90]]),
            pystac.TemporalExtent(
                [
                    [
                        datetime(2014, 1, 1, tzinfo=timezone.utc),
                        datetime(2020, 1, 1, tzinfo=timezone.utc),
                    ]
                ]
            ),
        ),
        stac_extensions=COG_COLLECTION_EXTENSIONS,
    )
    collection.links = []
    collection.properties = {}
    collection.properties["eo:bands"] = [
        {"B1": f"Relative {target.capitalize()}"},
    ]
    return collection


def activation_output(item_id: str, collection_id: str):
    with open("/tmp/activator-output.json", "w") as outfile:
        json.dump(
            {"sourceCollectionId": collection_id, "sourceItemId": item_id}, outfile
        )


def pipeline_arguments(args):
    def to_snake(word):
        return "".join(
            ["_" + letter.lower() if letter.isupper() else letter for letter in word]
        )

    filename_pipeline = None
    if args.pipeline_uri:
        filename_pipeline = "/tmp/pipeline.json"
        os.system(f"aws s3 cp {args.pipeline_uri} {filename_pipeline}")
    elif args.pipeline:
        filename_pipeline = args.pipeline
    if filename_pipeline is not None:
        with open(filename_pipeline, "r") as file:
            args_json = json.loads(file.read().replace("\n", ""))
        for k in args_json:
            k2 = to_snake(k)
            setattr(args, k2, args_json.get(k))
    return args


def cli_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--aviris-collection-id", type=str, default=AVIRIS_ARCHIVE_COLLECTION_ID
    )
    parser.add_argument(
        "--aviris-stac-id",
        type=str,
        default="f100517t01p00r06_sc01",
        help="STAC Item ID to process from the STAC collection",
    )
    parser.add_argument("--pipeline", type=str, help="JSON with instructions")
    parser.add_argument(
        "--pipeline-uri", type=str, help="A URI to JSON with instructions"
    )
    parser.add_argument(
        "--s3-bucket", type=str, default=os.environ.get("S3_BUCKET", "aviris-data")
    )
    parser.add_argument(
        "--s3-prefix", type=str, default=os.environ.get("S3_PREFIX", "target-detection")
    )
    parser.add_argument(
        "--stac-api-uri",
        type=str,
        default=os.environ.get("STAC_API_URI", "http://franklin:9090"),
    )
    parser.add_argument(
        "--temp-dir", type=str, default=os.environ.get("TEMP_DIR", "/tmp")
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="If provided, force reingest StacItem even though this it is already present in the catalog.",
    )
    parser.add_argument(
        "--keep-temp-dir",
        action="store_true",
    )
    parser.add_argument(
        "--skip-compute",
        action="store_true",
        help="Skip downloading and inference (useful for debugging).",
    )
    parser.add_argument(
        "--skip-registration",
        action="store_true",
        help="Skip registration of new item in Franklin (useful for debugging).",
    )
    parser.add_argument(
        "--target", type=str, required=True, choices=['oil', 'plastic'],
    )

    return parser


def main():

    # PYTHONPATH="." python3 -m activator.target_detection.main --stac-api-uri https://franklin.nasa-hsi.azavea.com --skip-compute --skip-registration --target oil
    try:
        warpMemoryLimit = int(os.environ.get("GDAL_WARP_MEMORY_LIMIT", None))
    except TypeError:
        warpMemoryLimit = None

    args = cli_parser().parse_args()
    args = pipeline_arguments(args)

    if not args.aviris_stac_id.startswith(args.aviris_collection_id):
        args.aviris_stac_id = f"{args.aviris_collection_id}_{args.aviris_stac_id}"

    stac_client = STACClient(args.stac_api_uri)
    cog_collection = get_aviris_cog_collection(args.aviris_collection_id, args.target)

    # GET STAC Item from AVIRIS Catalog
    item = stac_client.get_collection_item(
        args.aviris_collection_id, args.aviris_stac_id
    )

    asset_key = "tiff_0"
    asset = item.assets.get(asset_key, None)
    if asset is None:
        s = f'STAC Item {args.aviris_stac_id} from {args.stac_api_uri} has no asset "{asset_key}"!'
        raise ValueError(s)
    scene_name = item.properties.get("Name")

    # Create new COG STAC Item
    cog_item_id = "{}_{}_{}".format(
        cog_collection.id,
        item.properties.get("Name"),
        item.properties.get("Scene"),
    )

    item.properties["eo:bands"] = cog_collection.properties["eo:bands"]
    item.properties.pop("layer:ids", None)

    cog_item = pystac.Item(
        cog_item_id,
        item.geometry,
        item.bbox,
        item.datetime,
        item.properties,
        stac_extensions=COG_ITEM_EXTENSIONS,
        collection=cog_collection.id,
    )

    # Create COG Collection if it doesn't exist
    if not stac_client.has_collection(cog_collection.id):
        stac_client.post_collection(cog_collection)

    if not args.force:
        # Exit early if COG STAC Item already exists
        try:
            stac_client.get_collection_item(cog_collection.id, cog_item_id)
            print(cog_collection.id)
            print(cog_item_id)
            logger.info(f"STAC Item {cog_item_id} already exists. Exiting.")
            activation_output(cog_item_id, cog_collection.id)
            return
        except requests.exceptions.HTTPError:
            pass

    in_cid = args.aviris_collection_id
    out_cid, _ = collection_id_to_collection_id(in_cid, args.target)
    s3_in = asset.href
    s3_in_splits = s3_in.split("/")[2:]
    s3_in_splits[1] = out_cid
    s3_out = "s3://" + "/".join(s3_in_splits)

    in_filename = f"{args.temp_dir}/in.tiff"
    out_filename = f"{args.temp_dir}/out.tiff"

    if not args.skip_compute:
        if not os.path.exists(in_filename):
            os.system(f"aws s3 cp {s3_in} {in_filename}")
        inference_args = f"--infile={in_filename} --outfile={out_filename} --npz-load /usr/local/src/activator/target_detection/{args.target}.npz"
        args2 = inference_parser().parse_args(inference_args.split())
        compute(args2)
        os.system(f"gdaladdo {out_filename}")
        os.system(f"aws s3 cp {out_filename} {s3_out}")

    # Add assets to COG STAC Item
    cog_item.add_asset(
        asset_key,
        pystac.Asset(s3_out, media_type=pystac.MediaType.COG, roles=["data"]),
    )

    # Delete the temporary directory if not told otherwise
    if not args.keep_temp_dir:
        if not args.temp_dir == "/tmp" and not args.temp_dir == "/tmp/":
            logger.info(f"Removing temp dir: {args.temp_dir}")
            shutil.rmtree(args.temp_dir, ignore_errors=True)

    # This is here for debugging purposes, do not delete.  It is not
    # called anywhere in this code, but can be called from within a
    # debugger.
    def delete_collection_item(collection_id, item_id):
        """DELETE item pystac.Item from STAC API collection_id"""
        url = "{}/collections/{}/items/{}".format(
            args.stac_api_uri, collection_id, item_id
        )
        response = requests.delete(url)
        response.raise_for_status()

    # Add COG Item to AVIRIS L2 STAC Collection
    logger.info(f"POST Item {cog_item.id} to {args.stac_api_uri}")
    if not args.skip_registration:
        item_data = stac_client.post_collection_item(cog_collection.id, cog_item)
        if item_data.get("id", None):
            logger.info(f"Success: {item_data['id']}")
            activation_output(item_data["id"], cog_collection.id)
        else:
            logger.error(f"Failure: {item_data}")
            return -1


if __name__ == "__main__":
    main()
