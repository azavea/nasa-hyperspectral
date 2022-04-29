#!/usr/bin/env python3

import gzip
import json
import math
import numpy as np
import pickle
import tqdm
from os.path import exists
from shapely.geometry import mapping, shape, Polygon, MultiPolygon
from shapely.ops import cascaded_union
from tqdm.contrib.concurrent import process_map, thread_map


if __name__ == '__main__':

    if not exists('conifer.shapely.pickle'):
        if not exists('conifer.pickle'):
            print('geojson -> dict')
            with gzip.open('conifer.geojson.gz', 'r') as f:
                ds = json.load(f)
            print('dict -> pickle')
            with open('conifer.pickle', 'wb') as f:
                pickle.dump(ds, f)
        else:
            print('pickle -> dict')
            with open('conifer.pickle', 'rb') as f:
                ds = pickle.load(f)
        print('dict -> shapely')
        geoms = [shape(feature.get('geometry')) for feature in tqdm.tqdm(ds.get('features'))]
        print('shapely -> pickle')
        with open('conifer.shapely.pickle', 'wb') as f:
            pickle.dump(geoms, f)
        del ds
    else:
        print('pickle -> shapely')
        with open('conifer.shapely.pickle', 'rb') as f:
            geoms = pickle.load(f)

    print('buffering')
    def buffer(g):
        if isinstance(g, Polygon):
            return g.envelope
        elif isinstance(g, MultiPolygon):
            return MultiPolygon(list(map(lambda g: g.envelope, list(g))))
    max_workers=32
    chunksize=1
    geoms = thread_map(buffer, geoms, max_workers=max_workers, chunksize=chunksize)

    print('sorting')
    bounds = list(map(lambda g: g.bounds, geoms))
    xs = list(map(lambda b: b[0], bounds))
    ys = list(map(lambda b: b[1], bounds))
    xmin = np.min(xs)
    xmax = np.max(xs)
    ymin = np.min(ys)
    ymax = np.max(ys)
    def zorder(s):
        (x, y, _, _) = s.bounds
        x = int((x - xmin)/(xmax - xmin) * (1<<10 - 1))
        y = int((y - ymin)/(ymax - ymin) * (1<<10 - 1))
        value = 0
        for i in range(0, 10):
            digit = 2*(x & (1<<i)) + 1*(y & (1<<i))
            value += (digit<<(i<<1))
        return value
    geoms.sort(key = zorder)

    print('cascaded_unions')
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    while len(geoms) > 1:
        max_workers=32
        chunkss = list(chunks(geoms, 2))
        chunksize = max(1, (len(chunkss)//max_workers)//2)
        geoms = thread_map(cascaded_union, chunkss, max_workers=max_workers, chunksize=chunksize)

    print('shapely -> geojson')
    template = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                -0.3515625,
                                5.487502019076684
                            ],
                            [
                                -0.164794921875,
                                5.487502019076684
                            ],
                            [
                                -0.164794921875,
                                5.662451740971942
                            ],
                            [
                                -0.3515625,
                                5.662451740971942
                            ],
                            [
                                -0.3515625,
                                5.487502019076684
                            ]
                        ]
                    ]
                }
            }
        ]
    }
    template.get('features')[0]['geometry'] = mapping(geoms[0])
    with open('conifers-dissolved.geojson', 'w') as f:
        json.dump(template, f, indent=4)
