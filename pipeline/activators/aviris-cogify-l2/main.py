import argparse
from contextlib import contextmanager
import ftplib
import json
from math import floor
import os
from pathlib import Path
import shutil
import sys
import tarfile
from tempfile import mkdtemp
import threading
from time import time
from urllib.parse import urlparse, urlunparse

import boto3
from boto3.s3.transfer import TransferConfig
from osgeo import gdal
import pystac
import requests


GB = 1024 ** 3
s3 = boto3.client("s3")

AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-data"
AVIRIS_L2_COG_COLLECTION_ID = "aviris-l2-cogs"


@contextmanager
def timing(description: str) -> None:
    start = time()
    yield
    elapsed = time() - start
    print("{}: {:.4f}s".format(description, elapsed))


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r{}  {} / {} ({:.2f}%)".format(
                    self._filename, self._seen_so_far, self._size, percentage
                )
            )
            sys.stdout.flush()
            if percentage >= 100:
                print("")


def translate_callback(progress, *args):
    progress_pct = floor(progress * 100)
    if progress_pct % 10 == 0 > progress_pct > 0:
        print("GDAL Translate: {}%".format(progress_pct))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "aviris_stac_id",
        type=str,
        help="STAC Item ID to process from the {} STAC collection".format(
            AVIRIS_ARCHIVE_COLLECTION_ID
        ),
    )
    parser.add_argument(
        "--franklin-hostname",
        type=str,
        default=os.environ.get("FRANKLIN_HOSTNAME", "franklin.nasa-hsi.azavea.com"),
    )
    parser.add_argument(
        "--s3-bucket",
        type=str,
        default=os.environ.get("S3_BUCKET", "aviris-data"),
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
    args = parser.parse_args()

    # TODO: Check if COG item already exists and skip processing?
    #       Maybe separate issue?

    # POST Franklin /search for Name=<scene name> argument, retrieve STAC Item
    franklin_url_path = str(
        Path("collections", AVIRIS_ARCHIVE_COLLECTION_ID, "items", args.aviris_stac_id)
    )
    franklin_url = urlunparse(
        ("https", args.franklin_hostname, franklin_url_path, None, None, None)
    )
    response = requests.get(franklin_url)
    response.raise_for_status()
    item = pystac.Item.from_dict(response.json())
    l2_asset = item.assets.get("ftp_refl", None)
    if l2_asset is None:
        raise ValueError(
            "STAC Item {} from {} has no asset 'ftp_refl'!".format(
                args.aviris_stac_id, franklin_url
            )
        )
    scene_name = item.properties.get("Name")

    gzip_ftp_url = urlparse(l2_asset.href)
    username_password, ftp_hostname = gzip_ftp_url.netloc.split("@")
    ftp_username, ftp_password = username_password.split(":")

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

        # Create new COG STAC Item
        cog_item_id = "{}-{}_{}".format(
            AVIRIS_L2_COG_COLLECTION_ID,
            item.properties.get("Name"),
            item.properties.get("Scene"),
        )
        cog_item = pystac.Item(
            cog_item_id,
            item.geometry,
            item.bbox,
            item.datetime,
            item.properties,
            collection=AVIRIS_L2_COG_COLLECTION_ID,
        )

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
                    str(cog_metadata_path),
                    args.s3_bucket,
                    str(metadata_key),
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

    franklin_url_path = str(Path("collections", AVIRIS_L2_COG_COLLECTION_ID, "items"))
    franklin_url = urlunparse(
        ("https", args.franklin_hostname, franklin_url_path, None, None, None)
    )
    print("POST Item {} to {}".format(cog_item.id, franklin_url))
    response = requests.post(
        franklin_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(cog_item.to_dict()),
    )
    response.raise_for_status()
    post_data = response.json()
    post_url = "/".join([franklin_url, post_data.get("id")])
    print("Success: {}".format(post_url))


if __name__ == "__main__":
    main()
