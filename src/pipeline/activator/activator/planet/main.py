import argparse
import json
import logging
import os
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from math import floor
from pathlib import Path
from random import randint
from tempfile import mkdtemp
from time import sleep
from urllib.parse import urlparse

import dateutil.parser
import pystac
import requests
from activator.utils.stac_client import STACClient
from pyproj import CRS
from requests.auth import HTTPBasicAuth

# set a configurable logging level for the entire app
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format=
    '[%(relativeCreated)d|%(levelname)s|%(name)s|%(lineno)d] %(message)s',
    level=LOG_LEVEL)
logger = logging.getLogger(__name__)

GB = 1024**3

COG_COLLECTION_EXTENSIONS = [
    'https://stac-extensions.github.io/eo/v1.0.0/schema.json',
    'https://github.com/azavea/nasa-hyperspectral/tree/master/docs/stac/hsi/json-schema/schema.json'
]

COG_ITEM_EXTENSIONS = COG_COLLECTION_EXTENSIONS + \
    ['https://stac-extensions.github.io/projection/v1.0.0/schema.json']

# https://developers.planet.com/docs/apis/data/sensors/
PLANET_BANDS = [
    {
        "name": "B01",
        "common_name": "Blue",
        "center_wavelength": 0.490,
        "full_width_half_max": 0.05
    },
    {
        "name": "B02",
        "common_name": "Green II",
        "center_wavelength": 0.565,
        "full_width_half_max": 0.036
    },
    {
        "name": "B03",
        "common_name": "Red",
        "center_wavelength": 0.665,
        "full_width_half_max": 0.031
    },
    {
        "name": "B04",
        "common_name": "Red edge I",
        "center_wavelength": 0.705,
        "full_width_half_max": 0.015
    },
    {
        "name": "B05",
        "common_name": "NIR",
        "center_wavelength": 0.865,
        "full_width_half_max": 0.040
    }
]


def source_collection_id(num_bands: int = 4):
    if num_bands == 4:
        return "PSScene4Band"
    elif num_bands == 5:
        return "REOrthoTile"
    else:
        raise Exception(f"Unsupported number of bands {num_bands}")


def activation_output(item_id: str, collection_id: str):
    with open('/tmp/activator-output.json', 'w') as outfile:
        json.dump(
            {
                'sourceCollectionId': collection_id,
                'sourceItemId': item_id
            },
            outfile
        )


def planet_cog_collection_id(num_bands: int = 4):
    return f"planet-{num_bands}band-cogs"


def get_planet_cog_collection(num_bands: int = 4):
    collection = pystac.Collection(
        planet_cog_collection_id(num_bands),
        f'Planet Imagery: {source_collection_id(num_bands)}',
        pystac.Extent(
            pystac.SpatialExtent([[-180, -90, 180, 90]]),
            pystac.TemporalExtent([[
                datetime(1307, 10, 13, tzinfo=timezone.utc),
                datetime(2063, 4, 5, tzinfo=timezone.utc),
            ]]),
        ),
        stac_extensions=COG_COLLECTION_EXTENSIONS)
    collection.links = []
    collection.properties = {}
    if num_bands == 4:
        collection.properties['eo:bands'] = PLANET_BANDS[:3] + PLANET_BANDS[4:5]
    elif num_bands == 5:
        collection.properties['eo:bands'] = PLANET_BANDS
    collection.properties['hsi:wavelength_min'] = 440.0
    collection.properties['hsi:wavelength_max'] = 950.0

    return collection


def cli_parser():
    parser = argparse.ArgumentParser()
    # parser.add_argument("--force", action="store_true", help="If provided, force reingest StacItem even though this it is already present in the catalog.")
    parser.add_argument("--num-bands", type=int, default=4, choices=[4, 5], help="The desired number of bands (PSScene4Band or REOrthoTile)")
    # parser.add_argument("--output-format", type=str, default=os.environ.get("GDAL_OUTPUT_FORMAT", "COG"))
    parser.add_argument("--pipeline", type=str, help="JSON with instructions")
    parser.add_argument("--pipeline-uri", type=str, help="A URI to JSON with instructions")
    parser.add_argument("--planet-api-key", type=str, default=os.environ.get("PLANET_API_KEY", None))
    parser.add_argument("--planet-api-uri", type=str, default="https://api.planet.com/data/v1/item-types/{}/items/{}/assets")
    parser.add_argument("--planet-id", type=str, help="Planet Image ID")
    parser.add_argument("--s3-bucket", type=str, default=os.environ.get("S3_BUCKET", "planet-data-hsi"))
    parser.add_argument("--s3-prefix", type=str, default=os.environ.get("S3_PREFIX", "planet-scene-cogs"))
    parser.add_argument("--stac-api-uri", type=str, default=os.environ.get("STAC_API_URI", "http://franklin:9090"))
    parser.add_argument("--temp-dir", type=str, default='/tmp')

    parser.add_argument('--no-download', required=False, dest='download', action='store_false')
    parser.set_defaults(download=True)

    parser.add_argument('--no-upload', required=False, dest='upload', action='store_false')
    parser.set_defaults(upload=True)

    parser.add_argument('--no-update', required=False, dest='update', action='store_false')
    parser.set_defaults(update=True)

    return parser


def to_snake(word):
    return ''.join(['_' + letter.lower() if letter.isupper() else letter for letter in word])


def pipeline_arguments(args):
    filename_pipeline = None
    if args.pipeline_uri:
        filename_pipeline = '/tmp/pipeline.json'
        os.system(f'aws s3 cp {args.pipeline_uri} {filename_pipeline}')
    elif args.pipeline:
        filename_pipeline = args.pipeline

    if filename_pipeline is not None:
        with open(filename_pipeline, 'r') as file:
            args_json = json.loads(file.read().replace('\n', ''))
        for k in args_json:
            k2 = to_snake(k)
            setattr(args, k2, args_json.get(k))

    return args


def get_download_link(num_bands, planet_id, planet_api_uri, planet_api_key):
    logger.info('Requesting status of imagery')
    result = requests.get(planet_api_uri.format(
        source_collection_id(num_bands), planet_id),
                          auth=HTTPBasicAuth(planet_api_key, ''))
    result = result.json()

    logger.info('(Re)activating and getting download link')
    links = result['analytic']['_links']
    self_link = links['_self']
    activation_link = links['activate']
    result = requests.get(activation_link,
                          auth=HTTPBasicAuth(planet_api_key, ''))
    result = requests.get(self_link, auth=HTTPBasicAuth(planet_api_key, ''))
    result = result.json()
    is_active = result['status'] == 'active'

    if not is_active:
        logger.info('Imagery inactive, exiting with code -42')
        sys.exit(-42)
    else:
        download_link = result['location']

    return download_link


def download_from_planet(download_link,
                         planet_id,
                         planet_api_key,
                         temp_dir,
                         download):
    filename_tiff = f'{temp_dir}/{planet_id}.tiff'
    logger.info(f'Downloading imagery to {filename_tiff}')
    if download:
        data = requests.get(download_link,
                            auth=HTTPBasicAuth(planet_api_key, ''),
                            stream=True)
        with open(filename_tiff, 'wb') as f:
            data.raw.decode_content = True
            shutil.copyfileobj(data.raw, f)
        os.system(f'gdaladdo {filename_tiff}')
    return filename_tiff


def upload_to_s3(filename_tiff, s3_bucket, s3_prefix, upload):
    filename = filename_tiff.split('/')[-1]
    s3_uri = f's3://{s3_bucket}/{s3_prefix}/{filename}'
    logger.info(f'Uploading imagery to {s3_uri}')
    if upload:
        os.system(f'aws s3 cp {filename_tiff} {s3_uri}')
    return s3_uri


def generate_stac_item(filename_tiff, cog_collection, planet_id, s3_uri):
    logger.info(f'Using gdalinfo to get metadata')
    filename_json = filename_tiff.replace('.tiff', '.json')
    os.system(f'gdalinfo -proj4 -json {filename_tiff} > {filename_json}')
    with open(filename_json, 'r') as f:
        data = json.load(f)

    logger.info(f'Organizing metadata')
    tifftag_datetime = data.get('metadata').get('').get('TIFFTAG_DATETIME')
    year, month, day = [
        int(n) for n in tifftag_datetime.split(' ')[0].split(':')
    ]
    dt = datetime(year, month, day, tzinfo=timezone.utc)
    polygon = data.get('wgs84Extent')
    coords = polygon.get('coordinates')
    crs = CRS.from_string(data.get('coordinateSystem').get('proj4'))
    while len(coords) == 1:
        coords = coords[0]
    ys = [y for (y, x) in coords]
    xs = [x for (y, x) in coords]
    bbox = [min(ys), min(xs), max(ys), max(xs)]
    props = {
        'eo:bands': cog_collection.properties['eo:bands'],
        'hsi:wavelength_min': cog_collection.properties['hsi:wavelength_min'],
        'hsi:wavelength_min': cog_collection.properties['hsi:wavelength_min'],
        'proj:epsg': crs.to_authority()[-1],
    }

    logger.info(f'Creating new cog item')
    cog_item = pystac.Item(planet_id,
                           polygon,
                           bbox,
                           dt,
                           props,
                           stac_extensions=COG_ITEM_EXTENSIONS,
                           collection=cog_collection.id)
    cog_item.add_asset(
        'tiff_0',
        pystac.Asset(s3_uri, media_type=pystac.MediaType.COG, roles=['data']))

    return cog_item


def update_franklin(cog_item, cog_collection, stac_api_uri, update):
    logger.info('Updating Franklin')
    stac_client = STACClient(stac_api_uri)
    if update:
        if not stac_client.has_collection(cog_collection.id):
            stac_client.post_collection(cog_collection)
        logger.info(f"POST Item {cog_item.id} to {stac_api_uri}")
        item_data = stac_client.post_collection_item(cog_collection.id,
                                                     cog_item)
        if item_data.get('id', None):
            logger.info(f"Success: {item_data['id']}")
            activation_output(item_data['id'], cog_collection.id)
        else:
            raise Exception(f"Failure: {item_data}")


def main():
    args = cli_parser().parse_args()
    args = pipeline_arguments(args)
    cog_collection = get_planet_cog_collection(args.num_bands)
    download_link = get_download_link(args.num_bands, args.planet_id,
                                      args.planet_api_uri, args.planet_api_key)
    filename_tiff = download_from_planet(download_link, args.planet_id,
                                         args.planet_api_key, args.temp_dir,
                                         args.download)
    s3_uri = upload_to_s3(filename_tiff, args.s3_bucket, args.s3_prefix,
                          args.upload)
    cog_item = generate_stac_item(filename_tiff, cog_collection,
                                  args.planet_id, s3_uri)
    update_franklin(cog_item, cog_collection, args.stac_api_uri, args.update)


if __name__ == "__main__":
    main()
