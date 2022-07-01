#!/usr/bin/env python3

import argparse
import copy
import logging
import sys
import warnings

import numpy as np
import rasterio as rio
import tqdm
from rasterio.windows import Window


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True, type=str, nargs="+")
    parser.add_argument("--outfile", required=True, type=str, nargs="+")
    parser.add_argument("--npz-load", required=True, type=str)
    parser.add_argument("--stride", required=False, type=int, default=512)
    return parser


def whiten(m, W, mean):
    old_shape = m.shape
    m = m.reshape(-1, old_shape[-1])
    m = m - mean
    m = np.matmul(m, W)
    m = m.reshape(*old_shape)
    return m


def compute(args):

    dictionary = np.load(args.npz_load)
    W = dictionary.get('W').astype(np.float32)
    bias = dictionary.get('bias').astype(np.float32)
    spectrum = dictionary.get('spectrum').astype(np.float32)

    for (infile, outfile) in zip(args.infile, args.outfile):
        with rio.open(infile, 'r') as in_ds:
            profile = copy.deepcopy(in_ds.profile)
            profile.update({
                'compress': 'lzw',
                'count': 1,
                'bigtiff': 'yes',
                'driver': 'GTiff',
                'tiled': 'yes',
                'dtype': np.float32,
                'sparse_ok': 'yes'
            })
            with rio.open(outfile, 'w', **profile) as out_ds:
                for col in tqdm.tqdm(range(0, in_ds.width, args.stride), position=0):
                    width = min(col + args.stride, in_ds.width) - col
                    for row in tqdm.tqdm(range(0, in_ds.height, args.stride), position=1, leave=False):
                        height = min(row + args.stride, in_ds.height) - row
                        window = Window(col, row, width, height)
                        data = in_ds.read(window=window)
                        data = np.transpose(data, (1,2,0))
                        data = data.astype(np.float32)
                        norm = np.linalg.norm(data, ord=2, axis=2)[..., None].astype(np.float32)
                        data /= norm
                        data = whiten(data, W, 0)
                        data = np.dot(data, spectrum)
                        data[np.isnan(data)] = 0
                        data = data.reshape(1, height, width).astype(np.float32)
                        out_ds.write(data, window=window)


if __name__ == "__main__":
    args = cli_parser().parse_args()
    compute(args)
