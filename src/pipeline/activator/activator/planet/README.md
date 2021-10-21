# Planet Imagery Activator

Given a Planet ID (probably obtained by prior use of the Planet API), take the imagery, add overviews, upload to S3, and update Franklin.

## Development

### Setup

If you don't have one already, create a development S3 bucket to store your output:

```shell
./scripts/console activator-planet
aws s3api create-bucket --bucket "${S3_BUCKET}"
```

### Run Locally

```shell
docker compose run --rm activator-planet --planet-id <planet-id>
# or for usage instructions
docker compose run --rm activator-planet --help
```

A common set of arguments to use in development, to re-use the same temp dir and skip large files, is:

```shell
docker compose run --rm activator-planet --planet-id '20160831_143848_0c79'
```

Alternatively, activator can be launched without docker:

```shell
python3 main.py --planet-id '20160831_143848_0c79'
```
