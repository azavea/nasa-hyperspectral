# AVIRIS L2 Reflectance Imagery Activator

Given a STAC Item Id from the AVIRIS Catalog, convert the raw data to a COG and upload to S3.

## Development

### Setup

If you don't have one already, create a development S3 bucket to store your output:

```shell
./scripts/console activator-prisma
aws s3api create-bucket --bucket "${S3_BUCKET}"
```

### Run Locally

```shell
docker compose run --rm activator-prisma --prisma-path <path>
# or for usage instructions
docker compose run --rm activator-prisma --help
```

A common set of arguments to use in development, to re-use the same temp dir and skip large files, is:

```shell
docker compose run --rm activator-prisma \
  --prisma-uri s3://asi-prisma/L2D/PRS_L2D_STD_20200825024857_20200825024901_0001.zip \
  --temp-dir /data \
  --keep-temp-dir
```

Alternatively, activator can be launched via the following command:

```shell
docker compose run --rm activator-aviris-l2 \
  --pipeline "{\"avirisStacId\":\"aviris_f130329t01p00r06_sc01\",\"avirisCollectionId\":\"aviris-collection\",\"stacApiUri\":\"http:\/\/host.docker.internal:9090\",\"s3Bucket\":\"aviris-data\",\"s3Prefix\":\"aviris-scene-cogs-l2\",\"tempDir\":\"\/data\",\"keepTempDir\":true,\"skipLarge\":true,\"force\":false}"
```

or 

```shell
docker compose run --rm activator-aviris-l2 \
  --pipeline-uri /usr/local/src/data/pipeline-test.json
```

`/data` is a mounted Docker volume that can be reused across container executions for development.
