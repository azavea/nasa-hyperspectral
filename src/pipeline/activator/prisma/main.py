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
import logging
from config import CliConfig
from s3uri import S3Uri

import boto3
from boto3.s3.transfer import TransferConfig
from osgeo import gdal, osr
import pystac
import requests
import urllib.request
import json
import h5py
import numpy as np
from pyproj import CRS
import shapely.geometry
import json
import dateutil.parser
import zipfile

from progress import ProgressPercentage, timing, warp_callback, DownloadProgressBar
from stac_client import STACClient

# set a configurable logging level for the entire app
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='[%(relativeCreated)d|%(levelname)s|%(name)s|%(lineno)d] %(message)s', level=LOG_LEVEL)
logger = logging.getLogger(__name__)

GB = 1024 ** 3

PRISMA_ARCHIVE_COLLECTION_ID = "prisma"

COG_COLLECTION_EXTENSIONS = [
    'https://stac-extensions.github.io/eo/v1.0.0/schema.json',
    'https://github.com/azavea/nasa-hyperspectral/tree/master/docs/stac/hsi/json-schema/schema.json'
]

COG_ITEM_EXTENSIONS = COG_COLLECTION_EXTENSIONS + \
    ['https://stac-extensions.github.io/projection/v1.0.0/schema.json']

PRISMA_COG_COLLECTION = pystac.Collection(
    "prisma-cogs",
    "PRISMA Imagery converted to pixel-interleaved COGs",
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
    stac_extensions=COG_COLLECTION_EXTENSIONS
)

PRISMA_COG_COLLECTION.links = []
PRISMA_COG_COLLECTION.properties = {}
# https://directory.eoportal.org/web/eoportal/satellite-missions/p/prisma-hyperspectral


def activation_output(item_id: str):
    with open('/tmp/activator-output.json', 'w') as outfile:
        json.dump({
            'sourceCollectionId': PRISMA_COG_COLLECTION.id,
            'sourceItemId': item_id
        }, outfile)

# returns Extent, (xres, yres), affine_transform


def raster_extent(ll_y, ll_x, lr_y, lr_x, ul_y, ul_x, ur_y, ur_x, cols, rows):
    # X = Lon, Y = Lat
    # LatLon projection, required for the STAC catalog
    xs = [ll_x, lr_x, ul_x, ur_x]
    ys = [ll_y, lr_y, ul_y, ur_y]

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    extent = [xmin, ymin, xmax, ymax]

    xres = abs((xmax - xmin) / cols)
    yres = abs((ymax - ymin) / rows)

    res = (xres, yres)

    affine_transform = [xmin, xres, 0, ymax, 0, -yres]

    return extent, res, affine_transform


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
        "--prisma-path",
        type=str,
        help="PRISMA Scene Local Path"  # TODO: remove
    )
    parser.add_argument(
        "--prisma-uri",
        type=str,
        help="PRISMA Scene S3 URI"  # TODO: remove
    )
    parser.add_argument(
        "--prisma-stac-id",
        type=str,
        help="STAC Item ID to process from the STAC collection"
    )
    parser.add_argument(
        "--prisma-collection-id",
        type=str,
        default=PRISMA_ARCHIVE_COLLECTION_ID,
    )
    parser.add_argument(
        "--stac-api-uri",
        type=str,
        default=os.environ.get(
            "STAC_API_URI", "http://franklin:9090"
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
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skips upload to S3",
        default=False
    )

    try:
        warpMemoryLimit = int(os.environ.get("GDAL_WARP_MEMORY_LIMIT", None))
    except TypeError:
        warpMemoryLimit = None

    # TODO: replace it with parser.parse_args() later
    cli_args, cli_unknown = parser.parse_known_args()

    # parse all cli arguments
    args = CliConfig(cli_args, cli_unknown)

    # Create tmpdir
    temp_dir = Path(args.temp_dir if args.temp_dir is not None else mkdtemp())
    temp_dir.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client("s3")
    stac_client = STACClient(args.stac_api_uri)

    prisma_uri = S3Uri(args.prisma_uri)
    product_name_derived = os.path.splitext(Path(prisma_uri.key).name)[0]
    local_archive = Path(temp_dir, Path(prisma_uri.key).name)

    try:
        if not local_archive.exists():
            logger.info(f'Downloading PRISMA archive {prisma_uri.url} to {str(local_archive)}...')
            s3.download_file(prisma_uri.bucket, prisma_uri.key, str(local_archive))
        else:
            logger.info(
                f'Skipping downloading PRISMA archive {prisma_uri.url}, it already exists {str(local_archive)}')

        h5_path = Path(Path(temp_dir), f'{product_name_derived}.he5')

        if not h5_path.exists():
            logger.info(f'Extracting PRISMA archive {str(local_archive)}...')
            with zipfile.ZipFile(local_archive, 'r') as zip_ref:
                zip_ref.extractall(str(temp_dir))
        else:
            logger.info(
                f'Skipping extraction of the PRISMA archive {str(local_archive)}, file is already extracted {str(h5_path)}')

        logger.info(f'Reading {str(h5_path)}...')
        h5 = h5py.File(str(h5_path))

        data = h5['HDFEOS']['SWATHS']['PRS_L2D_HCO']['Data Fields']

        # UInt16
        swir = data['SWIR_Cube']
        # UInt16
        vnir = data['VNIR_Cube']
        # ERR Matrix is in Bytes
        swir_error = data['SWIR_PIXEL_L2_ERR_MATRIX']
        vnir_error = data['VNIR_PIXEL_L2_ERR_MATRIX']

        swirT = np.swapaxes(swir, 1, 2)
        vnirT = np.swapaxes(vnir, 1, 2)

        swir_errorT = np.swapaxes(swir_error, 1, 2)
        vnir_errorT = np.swapaxes(vnir_error, 1, 2)

        rows, cols = swirT.shape[0], swirT.shape[1]

        product_name = os.path.splitext(str(h5.attrs['Product_Name'].decode()))[0]

        # X = Lon, Y = Lat
        # LatLon projection, required for the STAC catalog
        extent_ll, _, _ = raster_extent(
            ll_y=h5.attrs['Product_LLcorner_lat'],
            ll_x=h5.attrs['Product_LLcorner_long'],

            lr_y=h5.attrs['Product_LRcorner_lat'],
            lr_x=h5.attrs['Product_LRcorner_long'],

            ul_y=h5.attrs['Product_ULcorner_lat'],
            ul_x=h5.attrs['Product_ULcorner_long'],

            ur_y=h5.attrs['Product_URcorner_lat'],
            ur_x=h5.attrs['Product_URcorner_long'],

            cols=cols,
            rows=rows
        )

        # X = easting, Y = northing
        extent, res, affine_transform = raster_extent(
            ll_y=h5.attrs['Product_LLcorner_lat'],
            ll_x=h5.attrs['Product_LLcorner_long'],

            lr_y=h5.attrs['Product_LRcorner_lat'],
            lr_x=h5.attrs['Product_LRcorner_long'],

            ul_y=h5.attrs['Product_ULcorner_lat'],
            ul_x=h5.attrs['Product_ULcorner_long'],

            ur_y=h5.attrs['Product_URcorner_lat'],
            ur_x=h5.attrs['Product_URcorner_long'],

            cols=cols,
            rows=rows
        )

        cog_proj = osr.SpatialReference()
        cog_proj.SetUTM(int(h5.attrs['Projection_Id'].decode()))
        cog_proj.AutoIdentifyEPSG()

        def create_geotiff(path, array, geo_transform=affine_transform, projection=cog_proj, dataType=gdal.GDT_UInt16, driver=gdal.GetDriverByName("GTiff")):
            ds = driver.Create(str(path), array.shape[1], array.shape[0], array.shape[2], dataType, [
                               'COMPRESS=DEFLATE', 'BIGTIFF=YES'])
            ds.SetGeoTransform(geo_transform)
            ds.SetProjection(projection.ExportToWkt())
            for i in range(1, array.shape[2]):
                ds.GetRasterBand(i).WriteArray(array[::, ::, i])
            ds.FlushCache()

            cog_path = str(Path(path.parent, f'cog_{path.name}'))

            warp_opts = gdal.WarpOptions(
                callback=warp_callback,
                warpOptions=["NUM_THREADS=ALL_CPUS"],
                creationOptions=["NUM_THREADS=ALL_CPUS", "COMPRESS=DEFLATE", "BIGTIFF=YES"],
                multithread=True,
                warpMemoryLimit=warpMemoryLimit,
                format=args.output_format
            )
            logger.info(f'Converting {str(path)} to {cog_path}...')
            with timing("GDAL Warp"):
                gdal.Warp(str(cog_path), str(path), options=warp_opts)

            return cog_path

        swir_path = create_geotiff(Path(temp_dir, "SWIR_Cube.tiff"), swirT)
        vnir_path = create_geotiff(Path(temp_dir, "VNIR_Cube.tiff"), vnirT)

        swir_error_path = create_geotiff(
            Path(temp_dir, "SWIR_PIXEL_L2_ERR_MATRIX.tiff"), swir_errorT)
        vnir_error_path = create_geotiff(
            Path(temp_dir, "VNIR_PIXEL_L2_ERR_MATRIX.tiff"), vnir_errorT)

        def key(name):
            return f'prisma-scene-cogs/{product_name}{name}'

        # prep all upload links
        s3_uri_swir = f's3://{args.s3_bucket}/{key(swir_path)}'
        s3_uri_vnir = f's3://{args.s3_bucket}/{key(vnir_path)}'
        s3_uri_swir_error = f's3://{args.s3_bucket}/{key(swir_error_path)}'
        s3_uri_vnir_error = f's3://{args.s3_bucket}/{key(vnir_error_path)}'

        upload_paths = [
            ('SWIR_Cube', swir_path, s3_uri_swir),
            ('VNIR_Cube', vnir_path, s3_uri_vnir),
            ('SWIR_PIXEL_L2_ERR_MATRIX', swir_error_path, s3_uri_swir_error),
            ('VNIR_PIXEL_L2_ERR_MATRIX', vnir_error_path, s3_uri_vnir_error)
        ]

        if(not args.skip_upload):
            for _, local_path, s3_uri in upload_paths:
                logger.info(f'Uploading {local_path} to {s3_uri}')
                s3.upload_file(
                    str(local_path),
                    args.s3_bucket,
                    str(key(local_path)),
                    Callback=ProgressPercentage(str(local_path)),
                    Config=TransferConfig(multipart_threshold=1 * GB),
                )

        swir_λs = h5.attrs['List_Cw_Swir']
        swir_flags = h5.attrs['List_Cw_Swir_Flags']
        swir_freqs = zip(swir_λs[swir_flags == 1], map(
            lambda x: x[0], filter(lambda x: x[1] == 1, enumerate(swir_flags))))
        swir_freqs_sorted = sorted([(b, f * 0.001) for f, b in swir_freqs], key=lambda x: x[0])

        vnir_λs = h5.attrs['List_Cw_Vnir']
        vnir_flags = h5.attrs['List_Cw_Vnir_Flags']
        vnir_freqs = zip(vnir_λs[vnir_flags == 1], map(
            lambda x: x[0], filter(lambda x: x[1] == 1, enumerate(vnir_flags))))
        vnir_freqs_sorted = sorted([(b, f * 0.001) for f, b in vnir_freqs], key=lambda x: x[0])

        λs = np.hstack([swir_λs, vnir_λs])
        flags = np.hstack([swir_flags, vnir_flags])
        band_freqs = sorted(zip(λs[flags == 1], map(
            lambda x: x[0], filter(lambda x: x[1] == 1, enumerate(flags)))))
        sorted_freqs = sorted([(b, f * 0.001) for f, b in band_freqs], key=lambda x: x[0])

        eo_swir_bands = [{'name': str(b), 'center_wavelength': float(f)}
                         for (b, f) in swir_freqs_sorted]
        eo_vnir_bands = [{'name': str(b), 'center_wavelength': float(f)}
                         for (b, f) in vnir_freqs_sorted]

        start_datetime = str(h5.attrs['Product_StartTime'].decode())
        end_datetime = str(h5.attrs['Product_StopTime'].decode())

        wavelength_min = float(min(sorted_freqs, key=lambda e: e[1])[1])
        wavelength_max = float(max(sorted_freqs, key=lambda e: e[1])[1])

        cog_item_id = f'{PRISMA_COG_COLLECTION.id}_{product_name}'

        cog_item = pystac.Item(
            id=cog_item_id,
            stac_extensions=COG_ITEM_EXTENSIONS,
            geometry=shapely.geometry.mapping(shapely.geometry.box(*extent_ll)),
            datetime=dateutil.parser.isoparse(start_datetime),
            bbox=list(map(lambda c: float(c), extent_ll)),
            collection=PRISMA_COG_COLLECTION.id,
            properties={
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'hsi:wavelength_min': wavelength_min,
                'hsi:wavelength_max': wavelength_max,
                'proj:epsg': int(cog_proj.GetAttrValue('AUTHORITY', 1))
            }
        )

        # add item assets
        for eo_bands, (key, _, uri) in zip([eo_swir_bands, eo_swir_bands, eo_swir_bands, eo_swir_bands], upload_paths):
            cog_item.add_asset(
                key=key,
                asset=pystac.Asset(
                    href=uri,
                    media_type=pystac.MediaType.GEOTIFF,
                    properties={
                        'eo:bands': eo_bands
                    }
                )
            )

    finally:
        if not args.keep_temp_dir:
            logger.info(f'Removing temp dir: {temp_dir}')
            shutil.rmtree(temp_dir, ignore_errors=True)

    # Create COG Collection if it doesn't exist
    if not stac_client.has_collection(PRISMA_COG_COLLECTION.id):
        stac_client.post_collection(PRISMA_COG_COLLECTION)

    # Add COG Item to AVIRIS L2 STAC Collection
    logger.info(f'POST Item {cog_item.id} to {args.stac_api_uri}')
    item_data = stac_client.post_collection_item(PRISMA_COG_COLLECTION.id, cog_item)
    if item_data.get('id', None):
        logger.info(f"Success: {item_data['id']}")
        activation_output(item_data['id'])
    else:
        logger.error(f'Failure: {item_data}')
        return -1

if __name__ == "__main__":
    main()
