import argparse
import os
from urllib.parse import urlparse
import logging
from .config import CliConfig

import boto3
import pystac
import requests
import urllib.request
import json

from activator.utils.stac_client import STACClient

from random import randint
from time import sleep

# set a configurable logging level for the entire app
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='[%(relativeCreated)d|%(levelname)s|%(name)s|%(lineno)d] %(message)s', level=LOG_LEVEL)
logger = logging.getLogger(__name__)

def save_output(scene_ids):
    with open('/tmp/planner-output.json', 'w') as outfile:
        json.dump({'scene_ids': scene_ids}, outfile)


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
        "--collection",
        type=str,
        default="aviris-classic",
        help="Collection to query"
    )
    parser.add_argument(
        "--stac-api-uri",
        type=str,
        default=os.environ.get('STAC_API_URI', 'http://franklin:9090'),
        help="STAC API URI"
    )
    parser.add_argument(
        "--geometry", 
        type=str,
        help="AOI"
    )
    parser.add_argument(
        "--datetime", 
        type=str,
        help="Datetime"
    )
    parser.add_argument(
        "--wavelengths", 
        type=str,
        help="Desired bands range"
    )

    # TODO: replace it with parser.parse_args() later
    cli_args, cli_unknown = parser.parse_known_args()

    # parse all cli arguments
    args = CliConfig(cli_args, cli_unknown)

    s3 = boto3.client("s3")
    stac_client = STACClient(args.stac_api_uri)

    scene_ids = [item['id'] for item in stac_client.search_items(args.geometry, args.datetime, None, args.collection)]

    print(f'scene_ids: {scene_ids}')

    save_output(scene_ids)


if __name__ == "__main__":
    main()
