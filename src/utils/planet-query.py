#!/usr/bin/env python3

import argparse
import json
import logging
import os

import requests
from requests.auth import HTTPBasicAuth

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format=
    '[%(relativeCreated)d|%(levelname)s|%(name)s|%(lineno)d] %(message)s',
    level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def source_collection_id(num_bands: int = 4):
    if num_bands == 4:
        return "PSScene4Band"
    elif num_bands == 5:
        return "REOrthoTile"
    else:
        raise Exception(f"Unsupported number of bands {num_bands}")


def activate_id(num_bands, planet_id, planet_api_uri, planet_api_key):
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

    return {'id': planet_id, 'is_active': is_active}


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dateend", type=str, default="2063-04-05T00:00:00.000Z")
    parser.add_argument("--datestart", type=str, default="1307-10-13T00:00:00.000Z")
    parser.add_argument("--geojson", type=str, required=False)
    parser.add_argument("--id-list", type=str, required=False)
    parser.add_argument("--maxcloud", type=float, default=0.5)
    parser.add_argument("--num-bands", type=int, default=4)
    parser.add_argument("--planet-api-key", type=str, required=True)
    parser.add_argument("--planet-api-uri", type=str, default="https://api.planet.com/data/v1/item-types/{}/items/{}/assets")

    parser.add_argument('--no-activate', required=False, dest='activate', action='store_false')
    parser.set_defaults(activate=True)

    return parser


if __name__ == "__main__":
    args = cli_parser().parse_args()

    if args.geojson is not None:
        with open(args.geojson, 'r') as f:
            geojson = json.load(f)
            geojson = geojson.get('features')[0].get('geometry')
    else:
        geojson = {
            'type':
            'Polygon',
            'coordinates': [[[-118.23276042938231, 33.89282552448263],
                             [-118.22932720184325, 33.888604063723],
                             [-118.22818994522095, 33.88865750124075],
                             [-118.22816848754884, 33.88897812564418],
                             [-118.22610855102538, 33.88908500017752],
                             [-118.22632312774658, 33.892255550420344],
                             [-118.2284688949585, 33.89209524452905],
                             [-118.2284903526306, 33.89229117391085],
                             [-118.22930574417114, 33.892255550420344],
                             [-118.22928428649901, 33.89262959632835],
                             [-118.23042154312132, 33.892540537927616],
                             [-118.23046445846559, 33.892968017403035],
                             [-118.23276042938231, 33.89282552448263]]]
        }

    geometry_filter = {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": geojson,
    }

    date_range_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gte": args.datestart,
            "lte": args.dateend,
        }
    }

    cloud_cover_filter = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {
            "lte": args.maxcloud,
        }
    }

    combined_filter = {
        "type": "AndFilter",
        "config": [geometry_filter, date_range_filter, cloud_cover_filter],
    }

    search_request = {
        "item_types": [source_collection_id(args.num_bands)],
        "filter": combined_filter
    }

    search_result = \
        requests.post(
            "https://api.planet.com/data/v1/quick-search",
            auth=HTTPBasicAuth(args.planet_api_key, ''),
            json=search_request)

    if search_result.status_code != 200:
        raise Exception('Failed query')

    planet_ids = [feature['id'] for feature in search_result.json()['features']]

    def activate_fn(planet_id):
        return activate_id(args.num_bands, planet_id, args.planet_api_uri, args.planet_api_key)

    if args.activate:
        planet_ids = [activate_fn(planet_id) for planet_id in planet_ids]

    if args.id_list:
        with open(args.id_list, "w") as f:
            f.write(json.dumps(planet_ids))

    print(f"Found {len(planet_ids)} images.")
