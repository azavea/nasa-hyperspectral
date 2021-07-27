import json

import pystac
import requests


class STACClient:
    def __init__(self, stac_api_url):
        """ Create a new STACClient for stac_api_url

        stac_api_url should include scheme, hostname, and port if applicable
        Example: http://localhost:9090

        """
        self.stac_api_url = str(stac_api_url)

    def get_collection_item(self, collection_id, item_id):
        """ GET item pystac.Item from STAC API collection_id """
        url = "{}/collections/{}/items/{}".format(
            self.stac_api_url, collection_id, item_id
        )
        response = requests.get(url)
        response.raise_for_status()
        return pystac.Item.from_dict(response.json())

    def has_collection(self, collection_id):
        """ Return True if STAC API has collection_id Collection else False """
        response = requests.get(
            "{}/collections/{}".format(self.stac_api_url, collection_id)
        )
        return True if response.status_code < 300 else False

    def post_collection(self, collection):
        """ POST collection pystac.Collection to STAC API """
        d = collection.to_dict()
        d['type'] = 'Collection'
        response = requests.post(
            "{}/collections".format(self.stac_api_url),
            headers={"Content-Type": "application/json"},
            data=json.dumps(d),
        )
        response.raise_for_status()
        return response.json()

    def post_collection_item(self, collection_id, item):
        """ POST item pystac.Item to collection_id """
        response = requests.post(
            "{}/collections/{}/items".format(self.stac_api_url, collection_id),
            headers={"Content-Type": "application/json"},
            data=json.dumps(item.to_dict()),
        )
        response.raise_for_status()
        return response.json()
