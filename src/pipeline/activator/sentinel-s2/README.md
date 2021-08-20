# AVIRIS L2 Reflectance Imagery Activator

Given a STAC Item Id from the AVIRIS Catalog, convert the raw data to a COG and upload to S3.

## Development

### Setup

If you don't have one already, create a development S3 bucket to store your output:

```shell
./scripts/console activator-sentinel-s2
aws s3api create-bucket --bucket "${S3_BUCKET}"
```

### Run Locally

```shell
docker compose run --rm activator-sentinel-s2 --sentinel-stac-id <stac-item-id>
# or for usage instructions
docker compose run --rm activator-sentinel-s2 --help
```

A common set of arguments to use in development, to re-use the same temp dir and skip large files, is:

```shell
docker compose run --rm activator-sentinel-s2 --sentinel-stac-id S2B_23XNK_20210819_0_L2A
```

Alternatively, activator can be launched without docker:

```shell
python3 main.py --sentinel-stac-id S2B_23XNK_20210819_0_L2A
```
