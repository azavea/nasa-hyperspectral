import logging
import json
from activator.utils.s3uri import S3Uri
import boto3
from shapely.geometry import shape
import os

logger = logging.getLogger(__name__)


class CliConfig:
    AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-classic"

    def __init__(self, args, unknown):
        if unknown is not []:
            logger.info(f"WARN: Unknown arguments passed: {unknown}")

        self._type = 'planner'

        def from_json(json_str):
            args_json = json.loads(json_str)
            self.collection = args_json.get('collection', self.AVIRIS_ARCHIVE_COLLECTION_ID)
            self.stac_api_uri = args_json.get('stacApiUri', os.environ.get("STAC_API_URI", "http://franklin:9090"))
            self.geometry = shape(args_json['geometry'])
            self.wavelengths = args_json['wavelengths']
            self.datetime = args_json['datetime']

        if args.pipeline_uri:
            # right now we support S3 and local FS only
            if args.pipeline_uri.startswith('s3'):
                s3 = boto3.resource('s3')
                uri = S3Uri(args.pipeline_uri)
                obj = s3.Object(uri.bucket, uri.key)
                args_json = obj.get()['Body'].read().decode('utf-8')
                from_json(args_json)
            else:
                with open(args.pipeline_uri, 'r') as file:
                    args_json = file.read().replace('\n', '')
                    from_json(args_json)

        elif args.pipeline:
            args_json = args.pipeline
            from_json(args_json)
        else:
            self.collection_id = args.collection
            self.stac_api_uri = args.stac_api_uri
            self.geometry = shape(args.geometry)
            self.wavelegnths = json.load(args.wavelengths)
            self.datetime = args.datetime
