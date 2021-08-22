#!/usr/bin/env python3

# Based on the source: https://github.com/azavea/cloud-buster/blob/master/cloudbuster/gather.py

import codecs
import copy
import json
import math
import os
from urllib.parse import urlparse
from typing import Optional, List
import logging

import boto3
import numpy as np
import rasterio as rio
import rasterio.enums
import rasterio.transform
import rasterio.warp
import requests
from osgeo import gdal, osr

def gather_sentinel(filename: str, output_s3_uri: str, paths: dict, working_dir: str = '/tmp', delete: bool = True):
    codes = []

    kind = 'L2A'
    num_bands = 13

    # Determine resolution, size, and filename
    info = json.loads(os.popen('gdalinfo -json -proj4 {}'.format(paths['B04'])).read())
    [width, height] = info.get('size')
    [urx, ury] = info.get('cornerCoordinates').get('upperRight')
    [lrx, lry] = info.get('cornerCoordinates').get('lowerRight')
    crs = info.get('coordinateSystem').get('proj4')
    [y1, y2] = rasterio.warp.transform(crs, 'epsg:4326', [urx, lrx], [ury, lry])[1]
    y1 = math.cos(math.radians(y1))
    y2 = math.cos(math.radians(y2))
    geoTransform = info.get('geoTransform')
    xres = (1.0/min(y1, y2)) * (1.0/110000) * geoTransform[1]
    yres = (1.0/110000) * geoTransform[5]
    out_shape = (1, width, height)

    # Build image
    data = np.zeros((num_bands, width, height), dtype=np.uint16)
    with rio.open(paths['B01']) as ds:
        data[0] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B02']) as ds:
        data[1] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B03']) as ds:
        data[2] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B04']) as ds:
        data[3] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
        geoTransform = copy.deepcopy(ds.transform)
        crs = copy.deepcopy(ds.crs)
        profile = copy.deepcopy(ds.profile)
        profile.update(count=num_bands, driver='GTiff',
                       bigtiff='yes', sparse_ok=True, tiled=True)
    with rio.open(paths['B05']) as ds:
        data[4] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B06']) as ds:
        data[5] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B07']) as ds:
        data[6] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B08']) as ds:
        data[7] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B8A']) as ds:
        data[8] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    with rio.open(paths['B09']) as ds:
        data[9] = ds.read(out_shape=out_shape,
                          resampling=rasterio.enums.Resampling.nearest)[0]
    if kind == 'L2A':
        with rio.open(paths['B11']) as ds:
            data[10] = ds.read(out_shape=out_shape,
                               resampling=rasterio.enums.Resampling.nearest)[0]
        with rio.open(paths['B12']) as ds:
            data[11] = ds.read(out_shape=out_shape,
                               resampling=rasterio.enums.Resampling.nearest)[0]
    elif kind == 'L1C':
        with rio.open(paths['B10']) as ds:
            data[10] = ds.read(out_shape=out_shape,
                               resampling=rasterio.enums.Resampling.nearest)[0]
        with rio.open(paths['B11']) as ds:
            data[11] = ds.read(out_shape=out_shape,
                               resampling=rasterio.enums.Resampling.nearest)[0]
        with rio.open(paths['B12']) as ds:
            data[12] = ds.read(out_shape=out_shape,
                               resampling=rasterio.enums.Resampling.nearest)[0]
    def working(filename):
        return os.path.join(working_dir, filename)

    with rio.open(working('scratch.tif'), 'w', **profile) as ds:
        ds.write(data)

    # Warp and compress to create final file
    command = ''.join([
        'gdalwarp {} '.format(working('scratch.tif')),
        '-tr {} {} '.format(xres, yres),
        '-srcnodata 0 -dstnodata 0 ',
        '-t_srs epsg:4326 ',
        '-multi ',
        '-overwrite ',
        '-co NUM_THREADS=ALL_CPUS -wo NUM_THREADS=ALL_CPUS ',
        '-oo NUM_THREADS=ALL_CPUS -doo NUM_THREADS=ALL_CPUS ',
        '-co BIGTIFF=YES -co COMPRESS=DEFLATE -co PREDICTOR=2 -co TILED=YES -co SPARSE_OK=YES ',
        '{}'.format(working(filename))
    ])
    code = os.system(command)
    codes.append(code)
    if delete:
        os.system('rm -f {}'.format(working('scratch.tif')))

    # Upload final file
    s3_uri = f'{output_s3_uri}/{filename}'
    code = os.system('aws s3 cp {} {}'.format(working(filename), s3_uri))
    codes.append(code)

    codes = list(map(lambda c: os.WEXITSTATUS(c) != 0, codes))
    return (codes, s3_uri)
