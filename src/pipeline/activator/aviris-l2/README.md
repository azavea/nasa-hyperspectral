# AVIRIS L2 Reflectance Imagery Activator

Given a STAC Item Id from the AVIRIS Catalog, convert the raw data to a COG and upload to S3.

## Development

### Setup

If you don't have one already, create a development S3 bucket to store your output:

```shell
./scripts/console activator-aviris-l2
aws s3api create-bucket --bucket "${S3_BUCKET}"
```

### Run Locally

```shell
docker-compose run --rm activator-aviris-l2 --aviris-stac-id <stac-item-id>
# or for usage instructions
docker-compose run --rm activator-aviris-l2 --help
```

A common set of arguments to use in development, to re-use the same temp dir and skip large files, is:

```shell
docker-compose run --rm activator-aviris-l2 \
  --aviris-stac-id <stac-item-id> \
  --temp-dir /data \
  --skip-large \
  --keep-temp-dir 
```

`/data` is a mounted Docker volume that can be reused across container executions for development.
