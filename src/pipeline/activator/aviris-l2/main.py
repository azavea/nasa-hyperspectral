import argparse
from datetime import datetime, timezone
import ftplib
from math import floor
import os
from pathlib import Path
import shutil
import tarfile
from tempfile import mkdtemp
from urllib.parse import urlparse

import boto3
from boto3.s3.transfer import TransferConfig
from osgeo import gdal
import pystac
import requests

from progress import ProgressPercentage, timing, translate_callback
from stac_client import STACClient


GB = 1024 ** 3

AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-classic"
AVIRIS_L2_COG_COLLECTION = pystac.Collection(
    "aviris-l2-cogs",
    "AVIRIS L2 Refl Imagery converted to pixel-interleaved COGs",
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
)
AVIRIS_L2_COG_COLLECTION.links = []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "aviris_stac_id",
        type=str,
        help="STAC Item ID to process from the STAC collection"
    )
    parser.add_argument(
        "--aviris_collection_id",
        type=str,
        default=AVIRIS_ARCHIVE_COLLECTION_ID,
    )
    parser.add_argument(
        "--franklin-url",
        type=str,
        default=os.environ.get(
            "FRANKLIN_URL", "http://franklin:9090"
        ),
    )
    parser.add_argument(
        "--s3-bucket", type=str, default=os.environ.get("S3_BUCKET", "aviris-data")
    )
    parser.add_argument(
        "--s3-prefix",
        type=str,
        default=os.environ.get("S3_PREFIX", "aviris-scene-cogs-l2"),
    )
    parser.add_argument(
        "--temp-dir", type=str, default=os.environ.get("TEMP_DIR", None)
    )
    parser.add_argument(
        "--keep-temp-dir",
        action="store_true",
        help="If provided, script does not delete temporary directory before script exits. Useful for debugging.",
    )
    parser.add_argument(
        "--skip-large",
        action="store_true",
        help="If provided, script will not process any COG > 200 MB to keep processing times reasonable. Useful for debugging.",
    )
    # TODO: replace it with parser.parse_args() later
    args, unknown = parser.parse_known_args()

    if unknown is not None:
        print(f"WARN: Unknown arguments passed: {unknown}")

    s3 = boto3.client("s3")
    stac_client = STACClient(args.franklin_url)

    # GET STAC Item from AVIRIS Catalog
    item = stac_client.get_collection_item(
        args.aviris_collection_id, args.aviris_stac_id
    )
    l2_asset = item.assets.get("ftp_refl", None)
    if l2_asset is None:
        raise ValueError(
            "STAC Item {} from {} has no asset 'ftp_refl'!".format(
                args.aviris_stac_id, args.franklin_url
            )
        )
    scene_name = item.properties.get("Name")

    # Create new COG STAC Item
    cog_item_id = "{}-{}_{}".format(
        AVIRIS_L2_COG_COLLECTION.id,
        item.properties.get("Name"),
        item.properties.get("Scene"),
    )
    cog_item = pystac.Item(
        cog_item_id,
        item.geometry,
        item.bbox,
        item.datetime,
        item.properties,
        collection=AVIRIS_L2_COG_COLLECTION.id,
    )

    # Create COG Collection if it doesn't exist
    if not stac_client.has_collection(AVIRIS_L2_COG_COLLECTION.id):
        stac_client.post_collection(AVIRIS_L2_COG_COLLECTION)

    # Exit early if COG STAC Item already exists
    try:
        stac_client.get_collection_item(AVIRIS_L2_COG_COLLECTION.id, cog_item_id)
        print("STAC Item {} already exists. Exiting.".format(cog_item_id))
        return
    except requests.exceptions.HTTPError:
        pass

    # Create tmpdir
    temp_dir = Path(args.temp_dir if args.temp_dir is not None else mkdtemp())
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        # Retrieve AVIRIS GZIP for matching scene name
        local_archive = Path(temp_dir, Path(l2_asset.href).name)
        if local_archive.exists():
            print("Using existing archive: {}".format(local_archive))
        else:
            with open(local_archive, "wb") as fp:
                gzip_ftp_url = urlparse(l2_asset.href)
                username_password, ftp_hostname = gzip_ftp_url.netloc.split("@")
                ftp_username, ftp_password = username_password.split(":")
                ftp_path = gzip_ftp_url.path.lstrip("/")
                print("FTP RETR {}".format(ftp_path))
                with timing("FTP RETR"):
                    with ftplib.FTP(ftp_hostname) as ftp:
                        ftp.login(ftp_username, ftp_password)
                        ftp.retrbinary("RETR {}".format(ftp_path), fp.write)

        # Retrieve file names from archive and extract if not already extracted to temp_dir
        extract_path = Path(temp_dir, scene_name)
        with tarfile.open(local_archive, mode="r") as tar_gz_fp:
            print("Retrieving filenames from {}".format(local_archive))
            with timing("Query archive"):
                tar_files = tar_gz_fp.getnames()
            # print("Files: {}".format(tar_files))

            if extract_path.exists():
                print("Skipping extract, exists at {}".format(extract_path))
            else:
                print("Extracting {} to {}".format(local_archive, extract_path))
                with timing("Extract"):
                    tar_gz_fp.extractall(extract_path)

        # Find HDR data files in unzipped package
        hdr_files = list(filter(lambda x: x.endswith(".hdr"), tar_files))
        print("HDR Files: {}".format(hdr_files))
        for idx, hdr_file_w_ext in enumerate(hdr_files):
            hdr_file_w_ext_path = Path(hdr_file_w_ext)
            hdr_path = Path(extract_path, hdr_file_w_ext_path.with_suffix(""))
            cog_path = hdr_path.with_suffix(".tiff")

            if args.skip_large and os.path.getsize(hdr_path) > 0.2 * GB:
                file_mb = floor(os.path.getsize(hdr_path) / 1024 / 1024)
                print(
                    "--skip-large provided. Skipping {} with size {}mb".format(
                        hdr_path, file_mb
                    )
                )
                continue

            # Convert HDR data to pixel interleaved COG with GDAL
            # NUM_THREADS only speeds up compression and overview generation
            translate_opts = gdal.TranslateOptions(
                callback=translate_callback,
                creationOptions=["NUM_THREADS=ALL_CPUS", "COMPRESS=DEFLATE"],
                format="COG",
            )
            print("Converting {} to {}...".format(hdr_path, cog_path))
            with timing("GDAL Translate"):
                gdal.Translate(str(cog_path), str(hdr_path), options=translate_opts)

            # Upload  COG and metadata, if written, to S3 bucket + key
            key = Path(
                args.s3_prefix,
                str(item.properties.get("Year")),
                str(item.properties.get("Name")),
                cog_path.name,
            )
            s3_uri = "s3://{}/{}".format(args.s3_bucket, key)
            print("Uploading {} to {}".format(cog_path, s3_uri))
            s3.upload_file(
                str(cog_path),
                args.s3_bucket,
                str(key),
                Callback=ProgressPercentage(str(cog_path)),
                Config=TransferConfig(multipart_threshold=1 * GB),
            )
            cog_metadata_path = cog_path.with_suffix(".tiff.aux.xml")
            if cog_metadata_path.exists():
                metadata_key = Path(args.s3_prefix, cog_metadata_path.name)
                metadata_s3_uri = "s3://{}/{}".format(args.s3_bucket, metadata_key)
                print("Uploading {} to {}".format(cog_metadata_path, metadata_s3_uri))
                s3.upload_file(
                    str(cog_metadata_path), args.s3_bucket, str(metadata_key)
                )

            # Add assets to COG STAC Item
            cog_item.add_asset(
                "cog_{}".format(idx),
                pystac.Asset(s3_uri, media_type=pystac.MediaType.COG, roles=["data"]),
            )
            if cog_metadata_path.exists():
                cog_item.add_asset(
                    "metadata_{}".format(idx),
                    pystac.Asset(
                        metadata_s3_uri,
                        media_type=pystac.MediaType.XML,
                        roles=["metadata"],
                    ),
                )
    finally:
        if not args.keep_temp_dir:
            print("Removing temp dir: {}".format(temp_dir))
            shutil.rmtree(temp_dir, ignore_errors=True)

    # Add COG Item to AVIRIS L2 STAC Collection
    print("POST Item {} to {}".format(cog_item.id, args.franklin_url))
    item_data = stac_client.post_collection_item(AVIRIS_L2_COG_COLLECTION.id, cog_item)
    print("Success: {}".format(item_data["id"]))


if __name__ == "__main__":
    main()
