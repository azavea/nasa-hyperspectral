import json

import pystac
import requests
import shapely


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
        collection_dict = collection.to_dict()
        collection_dict['type'] = 'Collection'
        response = requests.post(
            "{}/collections".format(self.stac_api_url),
            headers={"Content-Type": "application/json"},
            data=json.dumps(collection_dict),
        )
        response.raise_for_status()
        return response.json()

    def post_collection_item(self, collection_id, item):
        """ POST item pystac.Item to collection_id """
        item_dict = item.to_dict()
        item_dict['stac_version'] = '1.0.0'
        response = requests.post(
            "{}/collections/{}/items".format(self.stac_api_url, collection_id),
            headers={"Content-Type": "application/json"},
            data=json.dumps(item_dict),
        )
        response.raise_for_status()
        return response.json()


    def search_items(self, geometry, datetime, wavelengths, collection_id):
        stac_api_url = "{}/search/".format(self.stac_api_url)
        
        count = 0
        has_next = True
        while has_next:
            feature_collection = self.search_items_page(geometry, datetime, wavelengths, collection_id, stac_api_url)

            for item in feature_collection['features']: 
                yield item
            
            count += len(feature_collection['features'])

            links = feature_collection.get('links', None)
            if links == None:
                has_next = False
            else:
                next_links = [link['href'] for link in links if link['rel'] == 'next']
                if len(next_links) == 0:
                    has_next = False
                else:
                    stac_api_url = next_links[0]

    def search_items_page(self, geometry, datetime, wavelengths, collection_id, stac_api_url):
        """ POST search items by aoi, datetime, wavelengths and collection_id """
        data = {
            'datetime': datetime,
            'collections': [collection_id]
        }

        if geometry != None:
            data['intersects'] = shapely.geometry.mapping(geometry)

        if wavelengths is not None:
            data['query'] = {
                'hsi:wavelength_min': {
                    'gte': wavelengths['min']
                },
                'hsi:wavelength_max': {
                    'lte': wavelengths['max']
                }
            }

        response = requests.post(
            stac_api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        response.raise_for_status()
        return response.json()