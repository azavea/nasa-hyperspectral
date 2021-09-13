# AVIRIS Imagery Activator

Given a STAC Item Id from the AVIRIS Catalog, convert the raw data to a COG and upload to S3. This works for both L1 and L2 imagery. 

## Development

### Setup

If you don't have one already, create a development S3 bucket to store your output:

```shell
./scripts/console activator-aviris
aws s3api create-bucket --bucket "${S3_BUCKET}"
```

### Run Locally

L1 imagery is used by default, but you can use L2 by passing `--l2`.

```shell
docker compose run --rm activator-aviris --aviris-stac-id <stac-item-id>
# or for usage instructions
docker compose run --rm activator-aviris --help
```

A common set of arguments to use in development, to re-use the same temp dir and skip large files, is:

```shell
docker compose run --rm activator-aviris \
  --aviris-stac-id <stac-item-id> \
  --temp-dir /data \
  --skip-large \
  --keep-temp-dir 
```

Alternatively, the activator can be launched via the following command:

```shell
docker compose run --rm activator-aviris \
  --pipeline "{\"avirisStacId\":\"aviris_f130329t01p00r06_sc01\",\"avirisCollectionId\":\"aviris-collection\",\"stacApiUri\":\"http:\/\/host.docker.internal:9090\",\"s3Bucket\":\"aviris-data\",\"s3Prefix\":\"aviris-scene-cogs-l1\",\"tempDir\":\"\/data\",\"keepTempDir\":true,\"force\":false}"
```

or 

```shell
docker compose run --rm activator-aviris \
  --pipeline-uri /usr/local/src/data/l1/pipeline-test.json
```

`/data` is a mounted Docker volume that can be reused across container executions for development.
