import logging
import json
from activator.utils.s3uri import S3Uri
import boto3

logger = logging.getLogger(__name__)

L1 = 'l1'
L2 = 'l2'


class CliConfig:
    AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-classic"

    def __init__(self, args, unknown):
        if unknown is not []:
            logger.info(f"WARN: Unknown arguments passed: {unknown}")

        self._type = 'activator-aviris'

        def from_json(json_str):
            args_json = json.loads(json_str)
            self.aviris_stac_id = args_json['avirisStacId']
            self.aviris_collection_id = args_json.get(
                'avirisCollectionId', self.AVIRIS_ARCHIVE_COLLECTION_ID)
            self.stac_api_uri = args_json.get('stacApiUri', 'http://franklin:9090')
            self.s3_bucket = args_json.get('s3Bucket', 'aviris-data')
            self.l2 = args_json.get(L2, False)
            self.level = L2 if self.l2 else L1
            self.s3_prefix = args_json.get('s3Prefix', f'aviris-scene-cogs-{self.level}')
            self.temp_dir = args_json.get('tempDir', None)
            self.keep_temp_dir = args_json.get('keepTempDir', False)
            self.skip_large = args_json.get('skipLarge', False)
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
            self.aviris_stac_id = args.aviris_stac_id
            self.aviris_collection_id = args.aviris_collection_id
            self.stac_api_uri = args.stac_api_uri
            self.l2 = args.l2
            self.level = L2 if self.l2 else L1
            self.s3_bucket = args.s3_bucket
            self.s3_prefix = args.s3_prefix
            self.temp_dir = args.temp_dir
            self.keep_temp_dir = args.keep_temp_dir
            self.skip_large = args.skip_large
            self.force = args.force
            self.output_format = args.output_format
            self.output_asset_name = 'cog'
            if args.output_format != 'COG':
                self.output_asset_name = 'tiff'
