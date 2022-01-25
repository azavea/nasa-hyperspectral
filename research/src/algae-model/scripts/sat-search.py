#!/usr/bin/env python3

import argparse
import copy
import csv
import io
import itertools
import json
from datetime import datetime, timedelta, timezone

import lzip
from satsearch import Search
from shapely.geometry import MultiPoint, Point, mapping, shape


def lzip_or_file(filename):
    if filename.endswith('.lz'):
        return io.StringIO(lzip.decompress_file(filename).decode('utf-8'))
    else:
        return open(filename, 'r')


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, type=str, nargs='+')
    parser.add_argument('--days', required=False, type=int, default=1)
    parser.add_argument('--limit', required=False, type=int, default=800)
    parser.add_argument('--minclouds',
                        required=False,
                        type=float,
                        default=0.0)
    parser.add_argument('--maxclouds',
                        required=False,
                        type=float,
                        default=20.0)
    return parser


if __name__ == '__main__':

    args = cli_parser().parse_args()

    rows = []
    for filename in args.csv:
        with lzip_or_file(filename) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                rows.append(row)

    def fn(r):
        year = r.get('year')
        month = r.get('month')
        day = r.get('day')
        return f'{year}-{month}-{day}'

    launch_date = datetime(year=2015, month=6, day=23)

    for key, _group in itertools.groupby(rows, fn):
        group = list(_group)
        ps = [Point(float(r.get('lon')), float(r.get('lat'))) for r in group]
        mp = MultiPoint(ps)
        geojson = mapping(mp)

        year = int(group[0].get('year'))
        month = int(group[0].get('month'))
        day = int(group[0].get('day'))
        t = datetime(year=year, month=month, day=day)
        if t < launch_date:
            continue
        dt = timedelta(days=args.days)
        mindate1 = f'{(t-dt).year:04}-{(t-dt).month:02}-{(t-dt).day:02}'
        maxdate1 = f'{(t+dt).year:04}-{(t+dt).month:02}-{(t+dt).day:02}'

        geojson = mapping(shape(geojson).buffer(1e-5))
        query = {
            "url": "https://earth-search.aws.element84.com/v0",
            "intersects": copy.copy(geojson),
            "query": {
                "eo:cloud_cover": {
                    "lte": args.maxclouds,
                    "gte": args.minclouds,
                }
            },
            "datetime": f"{mindate1}/{maxdate1}",
            "sort": [
                {
                    "field": "datetime",
                    "direction": ">",
                },
            ],
            "collections": ["sentinel-s2-l2a"],
            "limit": args.limit,
        }

        search = Search(**query)
        if search.found() > 0:
            print(f'*date={t} points={len(ps)}')
            items = search.items(limit=args.limit)
            items.save(f'{year:04}_{month:02}_{day:02}.result')
        else:
            print(f' date={t} points={len(ps)}')
