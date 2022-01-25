#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, type=str, nargs='+')
    return parser


if __name__ == '__main__':

    args = cli_parser().parse_args()

    print(f'year,month,day,lat,lon,genus_species,cellcount')
    for filename in args.csv:
        with open(filename, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:

                date_str = row.get('datecollec')
                date_obj = None
                # https://docs.python.org/3/library/time.html#time.strftime
                for fmt in ['%Y-%m-%d']:
                    try:
                        date_obj = datetime.strptime(
                            date_str.split(' ')[0], fmt).date()
                        break
                    except:
                        continue
                if date_obj is None:
                    print(date_str)

                lat = float(row.get('latitude'))
                lon = float(row.get('longitude'))
                genus = '?'
                species = '?'
                genus_species = row.get('spec_name').replace(' ', '_').lower()
                cellcount = {
                    'present': 1,
                    'common': 2,
                    'abundant': 3,
                    'bloom': 4,
                }.get(row.get('abundance').lower())
                if cellcount is None:
                    cellcount = int(float(row.get('count')))
                month = date_obj.month
                day = date_obj.day
                year = date_obj.year

                if date_obj.year < 1993 or date_obj.year > 2021:
                    continue

                print(
                    f'{year},{month},{day},{lat},{lon},{genus_species},{cellcount}'
                )
