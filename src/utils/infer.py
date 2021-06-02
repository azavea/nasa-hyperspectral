#!/usr/bin/env python3

import argparse
import copy

import numpy as np
import rasterio as rio
import rasterio.windows
import scipy.signal
from tqdm import tqdm


def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spectrum', required=True, type=str)
    parser.add_argument('--infile', required=True, type=str)
    parser.add_argument('--outfile', required=True, type=str)
    return parser


if __name__ == '__main__':
    args = parser().parse_args()

    spectrum = []
    with open(args.spectrum, 'r') as f:
        f.readline()
        for line in f.readlines():
            spectrum.append(float(line))
        spectrum = np.array(spectrum)
        spectrum = spectrum / np.linalg.norm(spectrum, ord=2)
        spectrum_normalized = scipy.signal.resample(spectrum, 224) - spectrum.mean()

    with rio.open(args.infile, 'r') as in_ds:
        profile = copy.deepcopy(in_ds.profile)
        profile.update(count=1, driver='GTiff', bigtiff='yes', compress='deflate',
                       predictor='2', tiled='yes', dtype=np.float32)
        with rio.open(args.outfile, 'w', **profile) as out_ds:
            for col in tqdm(range(0, in_ds.width, 512), position=0):
                width = min(col+512, in_ds.width) - col
                for row in tqdm(range(0, in_ds.height, 512), position=1, leave=False):
                    height = min(row+512, in_ds.height) - row
                    window = rasterio.windows.Window(col, row, width, height)
                    data = np.transpose(in_ds.read(window=window).astype(np.float32), (1, 2, 0))
                    norm = np.linalg.norm(data, ord=2, axis=2)[..., None].astype(np.float32)
                    data /= norm
                    data -= np.mean(data, axis=2)[..., None]
                    data = np.dot(data, spectrum_normalized)
                    data = data.reshape(1, width, height).astype(np.float32)
                    out_ds.write(data, window=window)
