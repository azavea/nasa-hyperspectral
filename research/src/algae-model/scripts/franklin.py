#!/usr/bin/env python3

import argparse
import csv
import io
import itertools
import json
from datetime import datetime, timedelta, timezone

import lzip
from shapely.geometry import MultiPoint, Point, mapping


def lzip_or_file(filename):
    if filename.endswith('.lz'):
        return io.StringIO(lzip.decompress_file(filename).decode('utf-8'))
    else:
        return open(filename, 'r')


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, type=str, nargs='+')
    parser.add_argument('--days', required=False, type=int, default=1)
    return parser


if __name__ == '__main__':
    # curl -d @... -H 'Content-Type: application/json' https://franklin.nasa-hsi.azavea.com/search/

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
        return f'{year}_{month}_{day}'

    for key, _group in itertools.groupby(rows, fn):
        group = list(_group)
        ps = [Point(float(r.get('lon')), float(r.get('lat'))) for r in group]
        mp = MultiPoint(ps)
        geojson = mapping(mp)

        year = int(group[0].get('year'))
        month = int(group[0].get('month'))
        day = int(group[0].get('day'))
        # t = datetime(year=year, month=month, day=day, tzinfo=timezone(timedelta(hours=-4)))
        t = datetime(year=year, month=month, day=day)
        dt = timedelta(days=args.days)

        query = {
            'intersects': geojson,
            'datetime': f'{(t-dt).isoformat()}Z/{(t+dt).isoformat()}Z',
            'collections': ['aviris-ng', 'aviris-classic']
        }

        with open(f'{year}_{month}_{day}.query', 'w') as f:
            print(f'date={t} points={len(ps)}')
            f.write(json.dumps(query))
