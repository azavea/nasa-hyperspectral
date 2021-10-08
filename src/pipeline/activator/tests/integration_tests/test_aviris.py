import os
from os.path import dirname, abspath, join
import unittest 
import json
import filecmp

import requests
import boto3

from .utils import run_command

data_dir = join(dirname(abspath(__file__)), 'data')
s3 = boto3.client('s3')


def open_json(path):
    with open(path) as file:
        return json.dumps(json.load(file))

class AvirisTest(unittest.TestCase):
    def test_l1(self):
        # Populate Franklin with the AVIRIS collection and the tiny_scene item.
        # This is an item with a tiny GeoTIFF file that will allow the test to 
        # run quickly.
        requests.post(
            'http://franklin:9090/collections/', 
            data=open_json(join(data_dir, 'collection.json')), 
            headers={'Content-Type':'application/json'})
        
        requests.post(
            'http://franklin:9090/collections/aviris-classic/items/',
            data=open_json(join(data_dir, 'item.json')),
            headers={'Content-Type':'application/json'})

        # Delete the item and COG from S3 which may have been created during a 
        # previous run of this test.
        requests.delete(
            'http://franklin:9090/collections/aviris-l1-cogs/items/'
            'aviris-l1-cogs_tiny_scene_sc01')
        img_bucket = 'aviris-data-dev'
        img_object = 'aviris-scene-cogs-l1/2013/tiny_scene/ort_img_cog.tiff'
        s3.delete_object(Bucket=img_bucket, Key=img_object)

        # Run the main AVIRIS script and check that it exited normally.
        cmd = [
            'python', '-m', 'activator.aviris.main',
            '--pipeline-uri', join(data_dir, 'pipeline-test.json')
        ]
        retcode = run_command(cmd)
        self.assertEqual(retcode, 0)

        # Check that the COG item was posted to Franklin and the COG is 
        # on S3 and matches the expected COG.
        scene_dict = requests.get(
            'http://franklin:9090/collections/aviris-l1-cogs/items/'
            'aviris-l1-cogs_tiny_scene_sc01').json()
        exp_scene_dict = json.loads(open_json(join(data_dir, 'aviris_l1_cog_item.json')))
        self.assertDictEqual(scene_dict, exp_scene_dict)

        img_path = '/data/ort_img_cog.tiff'
        s3.download_file(img_bucket, img_object, img_path)

        exp_img_path = '/data/exp_ort_img_cog.tiff'
        s3.download_file(
            'nasahyperspectral-test', 
            'integration-tests/aviris/exp_ort_img_cog.tiff',
            '/data/exp_ort_img_cog.tiff')
        self.assertTrue(
            filecmp.cmp(img_path, exp_img_path), 
            'Generated COG file not the same as expected.')


if __name__ == '__main__':
    unittest.main()