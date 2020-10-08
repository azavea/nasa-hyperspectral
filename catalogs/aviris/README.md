# AVIRIS STAC Catalog

STAC Catalog generated from the AVIRIS sensor flight lines in `aviris-flight-lines.csv` for flights 2006-2019.

CSV file downloaded on 2020-10-08 from https://docs.google.com/spreadsheets/d/16geeqURwEyuLljM4lX4b2queRWAcvJmAOQklCFEeUhA/edit#gid=1335809227 available at https://aviris.jpl.nasa.gov/dataportal/.

The `build_catalog.py` script will write the catalog to `./data/catalog`. After updating the catalog, be sure to upload to S3 by running the following command from this directory: `aws s3 cp --recursive --quiet ./data/catalog/ s3://aviris-data/stac-catalog/`.
