# Cog Clip module

Given a STAC Item Id and the STAC Collection, clips Features from it an puts into the Target Collection.

## Demo

A picture of the original scene and two clipped out polygons.

<img width="502" alt="image" src="https://user-images.githubusercontent.com/4929546/104251306-6f2eac00-543d-11eb-9ad3-794aae05b7bc.png">

```bash
[info] running com.azavea.nasa.hsi.Main clip-pipeline --help
[ioapp-compute-0] ERROR c.a.n.hsi.Main - Usage:  clip-pipeline --pipeline <Json arguments>

Clip extents from COG as provided by GeoJSON Feature Collection

Options and flags:
    --help
        Display this help text.
    --pipeline <Json arguments>
        JSON that sets application arguments. 

[info] running com.azavea.nasa.hsi.Main clip --help
[ioapp-compute-0] ERROR c.a.n.hsi.Main - Usage:  clip --source-collection-id <string> --source-item-id <string> --source-asset-id <string> --target-collection-id <string> [--target-layer-id <string>] [--features <{ "type": "FeatureCollection", "features": [<features>] }>] [--stac-api-uri <uri>] [--target-s3-uri <Amazon S3 URI>] [--threads <integer>] [--with-gdal] [--force]

Clip extents from COG as provided by GeoJSON Feature Collection

Options and flags:
    --help
        Display this help text.
    --source-collection-id <string>
        Source collectionId.
    --source-item-id <string>
        Source itemId.
    --source-asset-id <string>
        Source assetIt.
    --target-collection-id <string>
        Target collectionId.
    --target-layer-id <string>
        Target layerId.
    --features <{ "type": "FeatureCollection", "features": [<features>] }>
        Feature Collection of features to clip from COG
    --stac-api-uri <uri>

    --target-s3-uri <Amazon S3 URI>

    --threads <integer>
        Number of threads
    --with-gdal
        Uses GDAL for raster reads.
    --force
        Force reingest StacItem even though this it is already present in the catalog.

Environment Variables:
    FEATURES=<{ "type": "FeatureCollection", "features": [<features>] }>
        Feature Collection of features to clip from COG.
    STAC_API_URI=<uri>
    
    TARGET_S3_URI=<Amazon S3 URI>
    THREADS=<integer>
        Number of threads.
```

## Testing Instructions

### TLDR; 
Spin up a local dev env via `make run-dev-env`

### A bit more detailed description of the environment
* Run a local postgres instance: `make postgres`
* Run migrations: `make migrations`
* Import a test collection: `make import-aviris-test-collection`
* Run a local Franklin instance: `make run-franklin`
* `s3://aviris-data/test/f130329t01p00r06_corr_v1_warp.tif` is the test tiff.
* Run clipping: `./sbt "run clip-pipeline --json {\"sourceCollectionId\":\"aviris-l2-cogs\",\"sourceItemId\":\"aviris-l2-cogs_f130329t01p00r06_sc01\",\"sourceAssetId\":\"cog\",\"targetCollectionId\":\"aviris-l2-chips\",\"targetLayerId\":null,\"features\":{\"type\":\"FeatureCollection\",\"bbox\":[-116.59616231918336,34.048179201421064,-116.5848970413208,34.05689052283076],\"features\":[{\"type\":\"Feature\",\"properties\":{\"id\":\"test-poly-1\"},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[-116.59545421600342,34.05296164991205],[-116.59616231918336,34.048268096976194],[-116.58968210220337,34.048179201421064],[-116.58933877944945,34.05241052647845],[-116.59545421600342,34.05296164991205]]]}},{\"type\":\"Feature\",\"properties\":{\"id\":\"test-poly-2\"},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[-116.58989667892456,34.05612609576202],[-116.58860921859741,34.0527660903941],[-116.5848970413208,34.05518388547134],[-116.5864634513855,34.05689052283076],[-116.58989667892456,34.05612609576202]]]}}]},\"stacApiURI\":\"http:\/\/localhost:9090\",\"targetS3URI\":\"s3:\/\/nasahyperspectral-test\/activator-clip-cogs\/\",\"threads\":4,\"withGDAL\":false,\"force\":false}"`
* The result imagery lives here: `s3://nasahyperspectral-test/activator-clip-cogs`