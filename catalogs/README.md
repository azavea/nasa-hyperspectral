# STAC Catalogs

This folder contains a series of scripts used to generate STAC Catalogs for this project.

## The Catalogs

| Catalog Name | Folder | Published Location |
|--------------|--------|--------------------|
| AVIRIS       | aviris | `s3://aviris-data/stac-catalog/catalog.json` |

## Generating Catalogs

Build containers with `docker-compose build`.

Run `docker-compose run --rm <catalog_folder>` in this directory, using the catalog folder name according to the table above.
