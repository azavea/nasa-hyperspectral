# Cog Clip module

Given a STAC Item Id and the STAC Collection, clips Features from it an puts into the Target Collection.

## Demo

A picture of the original scene and two clipped out polygons.

<img width="502" alt="image" src="https://user-images.githubusercontent.com/4929546/104251306-6f2eac00-543d-11eb-9ad3-794aae05b7bc.png">

```bash
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

* Run a local Franklin instance.
* <details> 
     <summary>Create `aviris-l2-cogs` collection.</summary>

     ```javascript
     {
        "stac_version":"1.0.0-beta.2",
        "stac_extensions":[
           
        ],
        "id":"aviris-l2-cogs",
        "title":null,
        "description":"AVIRIS L2 Refl Imagery converted to pixel-interleaved COGs",
        "keywords":[
           
        ],
        "license":"proprietary",
        "providers":[
           
        ],
        "extent":{
           "spatial":{
              "bbox":[
                 [
                    -180,
                    -90,
                    180,
                    90
                 ]
              ]
           },
           "temporal":{
              "interval":[
                 [
                    "2014-01-01T00:00:00Z",
                    "2019-12-31T00:00:00Z"
                 ]
              ]
           }
        },
        "summaries":{
           
        },
        "properties":{
           
        },
        "links":[
           {
              "href":"https://franklin.nasa-hsi.azavea.com/collections/aviris-l2-cogs/tiles",
              "rel":"tiles",
              "type":"application/json",
              "title":"Tile URLs for Collection"
           },
           {
              "href":"https://franklin.nasa-hsi.azavea.com/collections/aviris-l2-cogs",
              "rel":"self",
              "type":"application/json",
              "title":null
           },
           {
              "href":"https://franklin.nasa-hsi.azavea.com",
              "rel":"root",
              "type":"application/json",
              "title":null
           }
        ]
     }
      ```
</details>

* <details>
     <summary>Insert item into the collection.</summary>

     ```javascript
     {
         "id":"aviris_f130329t01p00r06_sc01",
         "stac_version":"1.0.0-beta.2",
         "stac_extensions":[
            
         ],
        "type":"Feature",
        "geometry":{
           "type":"Polygon",
           "coordinates":[
              [
                 [
                    -114.887217,
                    33.498289
                 ],
                 [
                    -114.819923,
                    33.66972
                 ],
                 [
                    -116.769931,
                    34.187606
                 ],
                 [
                    -116.833779,
                    34.015078
                 ],
                 [
                    -114.887217,
                    33.498289
                 ]
              ]
           ]
        },
        "bbox":[
           -116.833779,
           33.498289,
           -114.819923,
           34.187606
        ],
        "links":[
           {
              "href":"https://franklin.nasa-hsi.azavea.com/collections/aviris-data",
              "rel":"collection",
              "type":"application/json",
              "title":null
           },
           {
              "href":"https://franklin.nasa-hsi.azavea.com/collections/aviris-data/items/aviris_f130329t01p00r06_sc01",
              "rel":"self",
              "type":"application/json",
              "title":null
           }
        ],
        "assets":{
           "ftp":{
              "href":"ftp://avoil:Gulf0il$pill@popo.jpl.nasa.gov/y13_data/f130329t01p00r06.tar.gz",
              "title":"ftp",
              "description":"AVIRIS data archive. The file size is described by the 'Gzip File Size' property.",
              "roles":[
                 
              ],
              "type":"application/gzip"
           },
           "cog":{
              "href":"s3://aviris-data/test/f130329t01p00r06_corr_v1_warp.tif",
              "title":"cog",
              "description":"AVIRIS TIFF COG.",
              "roles":[
                 
              ],
              "type":"image/tiff; application=geotiff; profile=cloud-optimized"
           },
           "rgb":{
              "href":"http://aviris.jpl.nasa.gov/aviris_locator/y13_RGB/f130329t01p00r06_sc01_RGB.jpeg",
              "title":"rgb",
              "description":"Full resolution RGB image captured by the flight",
              "roles":[
                 
              ],
              "type":"image/jpeg"
           },
           "kml_overlay":{
              "href":"http://aviris.jpl.nasa.gov/aviris_locator/y13_KML/f130329t01p00r06_sc01_overlay_KML.kml",
              "title":"kml_overlay",
              "description":"KML file describing the bounding box of the flight",
              "roles":[
           
              ],
              "type":"application/vnd.google-earth.kml+xml"
           },
           "rgb_small":{
              "href":"http://aviris.jpl.nasa.gov/aviris_locator/y13_RGB/f130329t01p00r06_sc01_RGB-W200.jpg",
              "title":"rgb_small",
              "description":"A lower resolution thumbnail of the same image as the 'rgb' asset.",
              "roles":[
                 
              ],
              "type":"image/jpeg"
           },
           "flight_log":{
              "href":"http://aviris.jpl.nasa.gov/cgi/flights_13.cgi?step=view_flightlog&flight_id=f130329t01",
              "title":"flight_log",
              "description":"HTML page with table listing the runs for this flight.",
              "roles":[
                 
              ],
              "type":"text/html"
           },
           "kml_outline":{
              "href":"http://aviris.jpl.nasa.gov/aviris_locator/y13_KML/f130329t01p00r06_sc01_outline_KML.kml",
              "title":"kml_outline",
              "description":"KML file describing the flight outline",
              "roles":[
                 
              ],
              "type":"application/vnd.google-earth.kml+xml"
           },
           "ftp_refl":{
              "href":"ftp://avoil:Gulf0il$pill@popo.jpl.nasa.gov/y13_data/f130329t01p00r06_refl.tar.gz",
              "title":"ftp_refl",
              "description":"AVIRIS data archive of atmospheric corrected imagery for this scene.",
              "roles":[
                 
              ],
              "type":"application/gzip"
           }
        },
        "collection":"aviris-l2-cogs",
        "properties":{
           "YY":13,
           "Run":6,
           "Name":"f130329t01p00r06",
           "Tape":"t01",
           "Year":2013,
           "Scene":"sc01",
           "Flight":130329,
           "GEO Ver":"ort",
           "RDN Ver":"e",
           "Comments":"Heading to southern end of So Cal Box Line 2",
           "NASA Log":"132003",
           "Rotation":73,
           "datetime":"2013-03-29T18:17:00Z",
           "has_refl":true,
           "Flight ID":"f130329t01",
           "Site Name":"Ad Hoc",
           "Pixel Size":14.4,
           "Flight Scene":"f130329t01p00r06_sc01",
           "Investigator":"Robert Green",
           "Solar Azimuth":140.15,
           "Number of Lines":13139,
           "Solar Elevation":52.9,
           "File Size (Bytes)":9438628864,
           "Number of Samples":1391,
           "Max Scene Elevation":3019.12,
           "Min Scene Elevation":122.25,
           "Mean Scene Elevation":843.55,
           "Gzip File Size (Bytes)":3659283368
        }
     }
      ```
</details>

* `s3://aviris-data/test/f130329t01p00r06_corr_v1_warp.tif` is the test tiff.
* FeatureCollection to test this module: [test.json.zip](https://github.com/azavea/nasa-hyperspectral/files/5798939/test.json.zip)
* Set FeatureCollections as env variable (to simplify testing): `export FEATURES=`cat test-data/test.json`
* Run clipping: `./sbt run clip --source-collection-id aviris-l2-cogs --source-item-id aviris_f130329t01p00r06_sc01 --source-asset-id cog --target-collection-id aviris-l2-chips`

Result imagery lives here: `s3://nasahyperspectral-test/activator-clip-cogs`