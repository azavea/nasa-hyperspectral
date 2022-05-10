# Processing Planner

By the input messages schedules the further processing if necessary.

## Development

### Setup

If you don't have one already, create a development S3 bucket to store your output:

```shell
./scripts/console planner
aws s3api create-bucket --bucket "${S3_BUCKET}"
```

### Run Locally

```shell
docker compose run --rm planner --pipeline-uri ./activator/planner/data/pipeline-test-s3.json
# or for usage instructions
docker compose run --rm planner --help
```

`/data` is a mounted Docker volume that can be reused across container executions for development.
