# AVIRIS STAC Catalog

STAC Catalog generated from the AVIRIS sensor flight lines in `aviris-flight-lines.csv` for flights 2006-2019.

CSV file downloaded on 2020-10-08 from https://docs.google.com/spreadsheets/d/16geeqURwEyuLljM4lX4b2queRWAcvJmAOQklCFEeUhA/edit#gid=1335809227 available at https://aviris.jpl.nasa.gov/dataportal/.

## Writing the Catalog

```shell
docker-compose run --rm catalogs-aviris
```

## Upload the Catalog to S3

```shell
# Still in container console
./scripts/console catalogs-aviris
aws s3 cp --recursive --quiet data/catalog/ s3://aviris-data/stac-catalog
```

## Ingest into local Franklin

```shell
# Run from repository root directory
docker-compose run -v "$(pwd)/src/catalogs/aviris/data:/data:ro" --rm franklin \
                import-catalog --catalog-root /data/catalog/catalog.json
```

The franklin ingest may not exit. If it's still running after a few minutes, log into the db and see if
the count in collection_items table is still increasing:

```
./scripts/db-console
> select count(*) from collection_items;
```

If the count is no longer increasing, ctrl+c the ingest. It is complete.
