import logging
import json
from s3uri import S3Uri
import boto3
import os

logger = logging.getLogger(__name__)


class CliConfig:
    SENTINEL_ARCHIVE_COLLECTION_ID = "sentinel-s2-l2a"

    def __init__(self, args, unknown):
        if unknown is not []:
            logger.info(f"WARN: Unknown arguments passed: {unknown}")

        self._type = 'sentinel-s2'

        def from_json(json_str):
            args_json = json.loads(json_str)
            self.sentinel_stac_id = args_json['sentinelStacId']
            self.sentinel_collection_id = args_json.get('sentinelCollectionId', self.SENTINEL_ARCHIVE_COLLECTION_ID)
            self.stac_api_uri = args_json.get('stacApiUri', os.environ.get("STAC_API_URI", "http://franklin:9090"))
            self.stac_api_uri_sentinel = args_json.get('stacApiUriSentinel', os.environ.get("STAC_API_URI_SENTINEL", "https://earth-search.aws.element84.com/v0"))
            self.s3_bucket = args_json.get('s3Bucket', 'sentinel-s2-data')
            self.s3_prefix = args_json.get('s3Prefix', 'sentinel-s2-cogs')
            self.temp_dir = args_json.get('tempDir', None)
            self.keep_temp_dir = args_json.get('keepTempDir', False)
            self.force = args_json.get('force', False)
            self.output_format = args_json.get('outputFormat', 'COG')
            self.output_asset_name = 'cog'
            if args.output_format != 'COG':
                self.output_asset_name = 'tiff'

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
            self.sentinel_stac_id = args.sentinel_stac_id
            self.sentinel_collection_id = args.sentinel_collection_id
            self.stac_api_uri = args.stac_api_uri
            self.stac_api_uri_sentinel = args.stac_api_uri_sentinel
            self.s3_bucket = args.s3_bucket
            self.s3_prefix = args.s3_prefix
            self.temp_dir = args.temp_dir
            self.keep_temp_dir = args.keep_temp_dir
            self.force = args.force
            self.output_format = args.output_format
            self.output_asset_name = 'cog'
            if args.output_format != 'COG':
                self.output_asset_name = 'tiff'
