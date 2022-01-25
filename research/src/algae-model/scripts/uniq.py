#!/usr/bin/env python3

import argparse
import copy
import json


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subresults', required=True, type=str, nargs='+')
    parser.add_argument('--result', required=True, type=str)
    return parser


if __name__ == '__main__':

    args = cli_parser().parse_args()

    ids = set()
    with open(args.subresults[0], 'r') as f:
        results = json.load(f)
    results['features'] = []

    for _subresult in args.subresults:
        with open(_subresult, 'r') as f:
            subresult = json.load(f)
            for feature in subresult.get('features'):
                id0 = feature.get('id')
                if not id0 in ids:
                    results.get('features').append(feature)
                    ids.add(id0)

    with open(args.result, 'w') as f:
        json.dump(results, f, indent=4, separators=(',', ': '))
