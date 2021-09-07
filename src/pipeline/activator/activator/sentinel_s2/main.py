import argparse
from datetime import datetime, timezone
from math import floor
import os
from pathlib import Path
import shutil
import tarfile
from tempfile import mkdtemp
from urllib.parse import urlparse
import logging
from .config import CliConfig

import boto3
from boto3.s3.transfer import TransferConfig
from osgeo import gdal, osr
import pystac
import requests
import urllib.request
import json
import dateutil.parser

from activator.utils.progress import ProgressPercentage, timing, warp_callback, DownloadProgressBar
from activator.utils.stac_client import STACClient

from random import randint
from time import sleep

from gather import gather_sentinel

# set a configurable logging level for the entire app
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='[%(relativeCreated)d|%(levelname)s|%(name)s|%(lineno)d] %(message)s', level=LOG_LEVEL)
logger = logging.getLogger(__name__)

GB = 1024 ** 3

SENTINEL_ARCHIVE_COLLECTION_ID = "sentinel-s2-l2a"
SENTINEL_COG_COLLECTION_ID = "sentinel-s2-l2a-cogs"

COG_COLLECTION_EXTENSIONS = [
    'https://stac-extensions.github.io/eo/v1.0.0/schema.json',
    'https://github.com/azavea/nasa-hyperspectral/tree/master/docs/stac/hsi/json-schema/schema.json'
]

COG_ITEM_EXTENSIONS = COG_COLLECTION_EXTENSIONS + \
    ['https://stac-extensions.github.io/projection/v1.0.0/schema.json']


SENTINEL_WAVELENGTH_MIN = 0.4439
SENTINEL_WAVELENGTH_MAX = 2.22024

SENTINEL_BANDS = [
    {
        "name": "B01",
        "common_name": "coastal",
        "center_wavelength": 0.4439,
        "full_width_half_max": 0.027
    },
    {
        "name": "B02",
        "common_name": "blue",
        "center_wavelength": 0.4966,
        "full_width_half_max": 0.098
    },
    {
        "name": "B03",
        "common_name": "green",
        "center_wavelength": 0.56,
        "full_width_half_max": 0.045
    },
    {
        "name": "B04",
        "common_name": "red",
        "center_wavelength": 0.6645,
        "full_width_half_max": 0.038
    },
    {
        "name": "B05",
        "center_wavelength": 0.7039,
        "full_width_half_max": 0.019
    },
    {
        "name": "B06",
        "center_wavelength": 0.7402,
        "full_width_half_max": 0.018
    },
    {
        "name": "B07",
        "center_wavelength": 0.7825,
        "full_width_half_max": 0.028
    },
    {
        "name": "B08",
        "common_name": "nir",
        "center_wavelength": 0.8351,
        "full_width_half_max": 0.145
    },
    {
        "name": "B8A",
        "center_wavelength": 0.8648,
        "full_width_half_max": 0.033
    },
    {
        "name": "B09",
        "center_wavelength": 0.945,
        "full_width_half_max": 0.026
    },
    {
        "name": "B11",
        "common_name": "swir16",
        "center_wavelength": 1.6137,
        "full_width_half_max": 0.143
    },
    {
        "name": "B12",
        "common_name": "swir22",
        "center_wavelength": 2.22024,
        "full_width_half_max": 0.242
    }
]

def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)

def vsis3(path: str) -> str:
    return f'/vsis3/{path}'

def activation_output(item_id: str):
    with open('/tmp/activator-output.json', 'w') as outfile:
        json.dump({
            'sourceCollectionId': SENTINEL_COG_COLLECTION_ID,
            'sourceItemId': item_id
        }, outfile)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pipeline-uri",
        type=str,
        help="A URI to JSON with instructions"
    )
    parser.add_argument(
        "--pipeline",
        type=str,
        help="JSON with instructions"
    )
    parser.add_argument(
        "--sentinel-stac-id",
        type=str,
        help="STAC Item ID to process from the STAC collection"
    )
    parser.add_argument(
        "--sentinel-collection-id",
        type=str,
        default=SENTINEL_ARCHIVE_COLLECTION_ID,
    )
    parser.add_argument(
        "--stac-api-uri",
        type=str,
        default=os.environ.get(
            "STAC_API_URI", "http://franklin:9090"
        ),
    )
    parser.add_argument(
        "--stac-api-uri-sentinel",
        type=str,
        default=os.environ.get(
            "STAC_API_URI_SENTINEL", "https://earth-search.aws.element84.com/v0"
        ),
    )
    
    parser.add_argument(
        "--s3-bucket", type=str, default=os.environ.get("S3_BUCKET", "sentinel-s2-data")
    )
    parser.add_argument(
        "--s3-prefix",
        type=str,
        default=os.environ.get("S3_PREFIX", "aviris-scene-cogs-l2"),
    )
    parser.add_argument(
        "--temp-dir", 
        type=str, 
        default=os.environ.get("TEMP_DIR", None)
    )
    parser.add_argument(
        "--output-format", 
        type=str, 
        default=os.environ.get("GDAL_OUTPUT_FORMAT", "COG")
    )
    parser.add_argument(
        "--keep-temp-dir",
        action="store_true",
        help="If provided, script does not delete temporary directory before script exits. Useful for debugging.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="If provided, force reingest StacItem even though this it is already present in the catalog.",
    )

    try:
        warpMemoryLimit = int(os.environ.get("GDAL_WARP_MEMORY_LIMIT", None))
    except TypeError:
        warpMemoryLimit = None

    # TODO: replace it with parser.parse_args() later
    cli_args, cli_unknown = parser.parse_known_args()

    # parse all cli arguments
    args = CliConfig(cli_args, cli_unknown)

    s3 = boto3.client("s3")
    stac_client_sentinel = STACClient(args.stac_api_uri_sentinel)
    stac_client = STACClient(args.stac_api_uri)

    collection = stac_client_sentinel.get_collection(args.sentinel_collection_id)

    SENTINEL_COG_COLLECTION = pystac.Collection(
        SENTINEL_COG_COLLECTION_ID,
        "Sentinel-2a and Sentinel-2b imagery, processed to Level 2A (Surface Reflectance) and converted to Cloud-Optimized GeoTIFFs",
        collection.extent,
        stac_extensions=COG_COLLECTION_EXTENSIONS
    )
    SENTINEL_COG_COLLECTION.links = []
    SENTINEL_COG_COLLECTION.properties = {}
    SENTINEL_COG_COLLECTION.properties['eo:bands'] = SENTINEL_BANDS

    SENTINEL_COG_COLLECTION.properties['hsi:wavelength_min'] = SENTINEL_WAVELENGTH_MIN
    SENTINEL_COG_COLLECTION.properties['hsi:wavelength_max'] = SENTINEL_WAVELENGTH_MAX

    # GET STAC Item from SENTINEL Catalog
    item = stac_client_sentinel.get_collection_item(args.sentinel_collection_id, args.sentinel_stac_id)
    assets = item.assets
    bands_map = { 
        'B01': vsis3(strip_scheme(assets['B01'].href)),
        'B02': vsis3(strip_scheme(assets['B02'].href)),
        'B03': vsis3(strip_scheme(assets['B03'].href)),
        'B04': vsis3(strip_scheme(assets['B04'].href)),
        'B05': vsis3(strip_scheme(assets['B05'].href)),
        'B06': vsis3(strip_scheme(assets['B06'].href)),
        'B07': vsis3(strip_scheme(assets['B07'].href)),
        'B08': vsis3(strip_scheme(assets['B08'].href)),
        'B8A': vsis3(strip_scheme(assets['B8A'].href)),
        'B09': vsis3(strip_scheme(assets['B09'].href)),
        'B11': vsis3(strip_scheme(assets['B11'].href)),
        'B12': vsis3(strip_scheme(assets['B12'].href)),
        'AOT': vsis3(strip_scheme(assets['AOT'].href)),
        # 'WVP': vsis3(strip_scheme(assets['WVP'].href)),
        # 'SCL': vsis3(strip_scheme(assets['SCL'].href))
    }

    # we don't need assets here, since the gather scripts knows what and how to download by the sentinel path
    properties = item.properties
    datetime = dateutil.parser.isoparse(properties['datetime'])

    # here "href": "s3://sentinel-s2-l2a/tiles/31/V/CE/2021/8/19/0/R60m/B01.jp2"
    # path is tiles/31/V/CE/2021/8/19/0
    sentintel_path = 'tiles/{}/{}/{}/{}/{}/{}/{}'.format(
        properties['sentinel:utm_zone'],
        properties['sentinel:latitude_band'],
        properties['sentinel:grid_square'],
        str(datetime.year),
        str(datetime.month),
        str(datetime.day), 
        properties['sentinel:sequence']
    )

    # Create new COG STAC Item
    cog_item_id = "{}_{}".format(SENTINEL_COG_COLLECTION.id, item.id)

    cog_item = pystac.Item(
        cog_item_id,
        item.geometry,
        item.bbox,
        item.datetime,
        item.properties,
        stac_extensions=COG_ITEM_EXTENSIONS,
        collection=SENTINEL_COG_COLLECTION.id,
    )

    cog_item.properties['eo:bands'] = SENTINEL_COG_COLLECTION.properties['eo:bands']
    cog_item.properties['hsi:wavelength_min'] = SENTINEL_COG_COLLECTION.properties['hsi:wavelength_min']
    cog_item.properties['hsi:wavelength_max'] = SENTINEL_COG_COLLECTION.properties['hsi:wavelength_max']
    cog_item.properties['proj:epsg'] = '4326'

    # Create COG Collection if it doesn't exist
    if not stac_client.has_collection(SENTINEL_COG_COLLECTION.id):
        stac_client.post_collection(SENTINEL_COG_COLLECTION)

    if not args.force:
        # Exit early if COG STAC Item already exists
        try:
            stac_client.get_collection_item(SENTINEL_COG_COLLECTION.id, cog_item_id)
            logger.info(f'STAC Item {cog_item_id} already exists. Exiting.')
            activation_output(cog_item_id)
            return
        except requests.exceptions.HTTPError:
            pass

    _, s3_uri = gather_sentinel(f'{cog_item_id}.tiff', f's3://{args.s3_bucket}/{args.s3_prefix}/{sentintel_path}/', bands_map)
    
    # Add assets to COG STAC Item
    idx = 0
    cog_item.add_asset(
        f'{args.output_asset_name}_{idx}',
        pystac.Asset(s3_uri, media_type=pystac.MediaType.COG, roles=["data"]),
    )

    # Add COG Item to AVIRIS L2 STAC Collection
    logger.info(f"POST Item {cog_item.id} to {args.stac_api_uri}")
    item_data = stac_client.post_collection_item(SENTINEL_COG_COLLECTION.id, cog_item)
    if item_data.get('id', None):
        logger.info(f"Success: {item_data['id']}")
        activation_output(item_data['id'])
    else:
        logger.error(f"Failure: {item_data}")
        return -1


if __name__ == "__main__":
    main()
