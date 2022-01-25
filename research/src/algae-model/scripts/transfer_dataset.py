#!/usr/bin/env python3

import argparse
import copy
import csv
import logging
import math
import sys
import warnings

import numpy as np
import rasterio as rio
import rasterio.windows
import tqdm


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chips-per-scene',
                        required=False,
                        type=int,
                        default=100)
    parser.add_argument('--savez', required=True, type=str)
    parser.add_argument('--scenes', required=True, type=str, nargs='+')
    parser.add_argument('--window-size', required=False, type=int, default=32)

    parser.add_argument('--planet', dest='planet', action='store_true')
    parser.set_defaults(schedule=False)

    return parser


if __name__ == '__main__':

    args = cli_parser().parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    log = logging.getLogger()

    n = args.window_size

    yesno = []

    for infile in tqdm.tqdm(args.scenes, position=0):
        with rio.open(infile, 'r') as ds:
            width = ds.width
            height = ds.height
            for i in tqdm.tqdm(range(0, args.chips_per_scene),
                               position=1,
                               leave=False):
                while True:
                    x = np.random.randint(0, width - n)
                    y = np.random.randint(0, height - n)
                    window = rasterio.windows.Window(x, y, n, n)
                    data = ds.read(window=window).astype(np.float32)
                    if data.sum() != 0:
                        if args.planet and data.shape[0] == 5:
                            data = data[[0, 1, 2, 4]]
                        data = data.transpose((1, 2, 0))
                        yesno.append(data)
                        break

    yesno = np.stack(yesno, axis=3)
    np.savez(args.savez, yesno=yesno)
