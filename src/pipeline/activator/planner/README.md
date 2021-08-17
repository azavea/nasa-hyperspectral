# AVIRIS L2 Reflectance Imagery Activator

Given a STAC Item Id from the AVIRIS Catalog, convert the raw data to a COG and upload to S3.

## Development

### Setup

If you don't have one already, create a development S3 bucket to store your output:

```shell
./scripts/console planner
aws s3api create-bucket --bucket "${S3_BUCKET}"
```

### Run Locally

```shell
docker compose run --rm planner --pipeline-uri ./data/pipeline-test-s3.json
# or for usage instructions
docker compose run --rm planner --help
```

`/data` is a mounted Docker volume that can be reused across container executions for development.
