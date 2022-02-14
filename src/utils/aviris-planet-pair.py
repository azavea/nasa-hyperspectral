#!/usr/bin/env python3

import argparse
import json
import pprint

from datetime import datetime, timedelta
from dateutil import parser
from shapely.geometry import MultiPolygon, shape
from shapely.strtree import STRtree


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aviris-ids', required=False, type=str, default=None)
    parser.add_argument('--aviris-scenes', required=True, type=str)
    parser.add_argument('--output', required=False, type=str, default=None)
    parser.add_argument('--planet-scenes', required=True, type=str)
    parser.add_argument('--timedelta', required=False, type=int, default=33)

    parser.add_argument('--ignore-year', required=False, dest='ignore_year', action='store_true')
    parser.set_defaults(ignore_year=False)
    return parser


def feature_to_shapely(feature):
    s = shape(feature.get('geometry')).buffer(0)
    s.ide = feature.get('id')
    s.dt = parser.parse(feature.get('properties').get('datetime'))
    return s


def shapely_to_dict(s):
    return {'id': s.ide, 'datetime': s.dt.isoformat()}


def predicate(a, b, delta):
    if a.intersects(b):
        return (a.dt - b.dt <= delta) and (b.dt - a.dt <= delta)
    else:
        return False


if __name__ == '__main__':

    args = cli_parser().parse_args()

    delta = timedelta(days=args.timedelta)

    matches = []

    # curl 'https://franklin.nasa-hsi.azavea.com/collections/planet-4band-cogs/items/?limit=1000'
    with open(args.planet_scenes, 'r') as f:
        planet = [feature_to_shapely(feature) for feature in json.load(f).get('features')]
        if args.ignore_year:
            for s in planet:
                s.dt = s.dt.replace(year = 1776)
    strtree = STRtree(planet)

    # curl 'https://franklin.nasa-hsi.azavea.com/collections/aviris-l1-cogs/items/?limit=1000'
    with open(args.aviris_scenes, 'r') as f:
        aviris = [feature_to_shapely(feature) for feature in json.load(f).get('features')]
        if args.ignore_year:
            for s in aviris:
                s.dt = s.dt.replace(year = 1776)
    if args.aviris_ids:
        with open(args.aviris_ids, 'r') as f:
            aviris_ids = json.load(f)
        aviris = list(filter(lambda s: s.ide in aviris_ids, aviris))

    for aviris_scene in aviris:
        planet_scenes = [s for s in strtree.query(aviris_scene) if predicate(s, aviris_scene, delta)]
        for s in planet_scenes:
            s.size = aviris_scene.intersection(s).area
        planet_scenes.sort(key=lambda s: -s.size)
        if planet_scenes:
            match = {
                'id': aviris_scene.ide,
                'datetime': aviris_scene.dt.isoformat(),
                'matches': [shapely_to_dict(s) for s in planet_scenes]
            }
            matches.append(match)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(matches, f, indent=4, separators=(',', ': '))
    else:
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(matches)
