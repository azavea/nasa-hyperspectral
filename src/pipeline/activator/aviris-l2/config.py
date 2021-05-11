import logging
import json

logger = logging.getLogger(__name__)

class CliConfig:
    AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-classic"

    def __init__(self, args, unknown):
        if unknown is not []:
            logger.info(f"WARN: Unknown arguments passed: {unknown}")

        self._type = 'activator-aviris-l2'

        if args.pipeline: 
            args_json = json.loads(args.pipeline)
            self.aviris_stac_id = args_json['avirisStacId']
            self.aviris_collection_id = args_json.get('avirisCollectionId', self.AVIRIS_ARCHIVE_COLLECTION_ID)
            self.stac_api_uri = args_json.get('stacApiUri', 'http://franklin:9090')
            self.s3_bucket = args_json.get('s3Bucket', 'aviris-data')
            self.s3_prefix = args_json.get('s3Prefix', 'aviris-scene-cogs-l2')
            self.temp_dir = args_json.get('tempDir', None)
            self.keep_temp_dir = args_json.get('keepTempDir', False)
            self.skip_large = args_json.get('skipLarge', False)
            self.force = args_json.get('force', False)
        else:
            self.aviris_stac_id = args.aviris_stac_id
            self.aviris_collection_id = args.aviris_collection_id
            self.stac_api_uri = args.stac_api_uri
            self.s3_bucket = args.s3_bucket
            self.s3_prefix = args.s3_prefix
            self.temp_dir = args.temp_dir
            self.keep_temp_dir = args.keep_temp_dir
            self.skip_large = args.skip_large
            self.force = args.force
    