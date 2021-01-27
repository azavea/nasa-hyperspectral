import logging
import json

logger = logging.getLogger(__name__)

class CliConfig:
    AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-classic"

    def __init__(self, args, unknown):
        if unknown is not None:
            logger.info(f"WARN: Unknown arguments passed: {unknown}")

        if args.pipeline: 
            args_json = json.loads(args.pipeline)
            self._type = args_json['_type']
            self.aviris_stac_id = args_json['aviris-stac-id']
            self.aviris_collection_id = args_json.get('aviris-collection-id', self.AVIRIS_ARCHIVE_COLLECTION_ID)
            self.stac_api_uri = args_json.get('stac-api-uri', 'http://franklin:9090')
            self.s3_bucket = args_json.get('s3-bucket', 'aviris-data')
            self.s3_prefix = args_json.get('s3-prefix', 'aviris-scene-cogs-l2')
            self.temp_dir = args_json.get('temp-dir', None)
            self.keep_temp_dir = args_json.get('keep-temp-dir', False)
            self.skip_large = args_json.get('skip-large', False)
            self.force = args_json.get('force', False)
        else:
            self._type = 'activator-aviris-l2'
            self.aviris_stac_id = args.aviris_stac_id
            self.aviris_collection_id = args.aviris_collection_id
            self.stac_api_uri = args.stac_api_uri
            self.s3_bucket = args.s3_bucket
            self.s3_prefix = args.s3_prefix
            self.temp_dir = args.temp_dir
            self.keep_temp_dir = args.keep_temp_dir
            self.skip_large = args.skip_large
            self.force = args.force
    