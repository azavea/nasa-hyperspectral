import logging
import json
from activator.utils.s3uri import S3Uri
import boto3
import os

logger = logging.getLogger(__name__)


class CliConfig:
    PRISMA_ARCHIVE_COLLECTION_ID = "prisma"

    def __init__(self, args, unknown):
        if unknown is not []:
            logger.info(f"WARN: Unknown arguments passed: {unknown}")

        self._type = 'activator-prisma'

        def from_json(json_str):
            args_json = json.loads(json_str)
            self.prisma_stac_id = args_json['prismaStacId']
            self.prisma_collection_id = args_json.get(
                'prismaCollectionId', self.AVIRIS_ARCHIVE_COLLECTION_ID)
            self.prisma_path = args_json.get('prismaPath', None)
            self.prisma_uri = args_json.get('prismaUri', None)
            self.stac_api_uri = args_json.get('stacApiUri', os.environ.get('STAC_API_URI', 'http://franklin:9090'))
            self.s3_bucket = args_json.get('s3Bucket', 'aviris-data')
            self.s3_prefix = args_json.get('s3Prefix', 'aviris-scene-cogs-l2')
            self.temp_dir = args_json.get('tempDir', None)
            self.keep_temp_dir = args_json.get('keepTempDir', False)
            self.force = args_json.get('force', False)
            self.skip_upload = args_json.get('skipUpload', False)
            self.output_format = args_json.get('outputFormat', 'COG')

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
            self.prisma_stac_id = args.prisma_stac_id
            self.prisma_collection_id = args.prisma_collection_id
            self.stac_api_uri = args.stac_api_uri
            self.s3_bucket = args.s3_bucket
            self.s3_prefix = args.s3_prefix
            self.temp_dir = args.temp_dir
            self.keep_temp_dir = args.keep_temp_dir
            self.force = args.force
            self.prisma_path = args.prisma_path
            self.prisma_uri = args.prisma_uri
            self.skip_upload = args.skip_upload
            self.output_format = args.output_format
