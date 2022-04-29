#!/usr/bin/env

import json

if __name__ == '__main__':

    with open('05_2015.geojson', 'r') as f:
        moop = json.load(f)

    new_features = []
    for feature in moop.get('features'):
        if 'Red' in feature.get('properties').get('default'):
            new_features.append(feature)

    moop['features'] = new_features

    with open('05_2015_red.geojson', 'w') as f:
        json.dump(moop, f, indent=4)
