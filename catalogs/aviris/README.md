# AVIRIS STAC Catalog

STAC Catalog generated from the AVIRIS sensor flight lines in `aviris-flight-lines.csv` for flights 2006-2019.

CSV file downloaded on 2020-10-08 from https://docs.google.com/spreadsheets/d/16geeqURwEyuLljM4lX4b2queRWAcvJmAOQklCFEeUhA/edit#gid=1335809227 available at https://aviris.jpl.nasa.gov/dataportal/.

This catalog can be published locally or to an S3 bucket via any of the three `pystac.CatalogType`s. Write the catalog with:

```shell
docker-compose run --rm aviris <catalog_output_path>
```

Run

```shell
docker-compose run --rm aviris --help
```

for more options.
