from datetime import datetime, timedelta, timezone
from ftplib import FTP
from pathlib import Path
from xml.dom import minidom

import fastkml
from functools import partial
from geopandas import GeoDataFrame
import pandas as pd
import pystac
from shapely.geometry import box
import stacframes


AVIRIS_DESCRIPTION = "AVIRIS is an acronym for the Airborne Visible InfraRed Imaging Spectrometer. AVIRIS is a premier instrument in the realm of Earth Remote Sensing. It is a unique optical sensor that delivers calibrated images of the upwelling spectral radiance in 224 contiguous spectral channels (also called bands) with wavelengths from 400 to 2500 nanometers (nm). AVIRIS has been flown on four aircraft platforms: NASA's ER-2 jet, Twin Otter International's turboprop, Scaled Composites' Proteus, and NASA's WB-57. The ER-2 flies at approximately 20 km above sea level, at about 730 km/hr. The Twin Otter aircraft flies at 4km above ground level at 130km/hr. AVIRIS has flown all across the US, plus Canada and Europe. This catalog contains all AVIRIS missions from 2006 - 2019."


def kml_poly_to_geom(kml_poly):
    # Not all KML polygons are correct (missing LinearRing tag); grab coords directly
    kmldom = minidom.parseString(
        '<?xml version="1.0" encoding="UTF-8"?>'
        + '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark>'
        + kml_poly
        + "</Placemark></Document></kml>"
    )
    coords = kmldom.getElementsByTagName("outerBoundaryIs")[0].getElementsByTagName(
        "coordinates"
    )[0]
    kml = fastkml.KML()
    kml.from_string(
        '<?xml version="1.0" ?>'
        + '<kml xmlns="http://www.opengis.net/kml/2.2">'
        + "<Document><Placemark><Polygon><outerBoundaryIs><LinearRing>"
        + coords.toxml()
        + "</LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>"
    )
    return next(next(kml.features()).features()).geometry


def find_s2_scenes():
    print("Finding scenes with atmo corrected data...")
    JPL_FTP_HOSTNAME = "popo.jpl.nasa.gov"
    JPL_FTP_USERNAME = "avoil"
    JPL_FTP_PASSWORD = "Gulf0il$pill"

    ftp = FTP(JPL_FTP_HOSTNAME)
    ftp.login(JPL_FTP_USERNAME, JPL_FTP_PASSWORD)

    s2_scenes = {}

    aviris_dir_list = ftp.nlst()
    for aviris_dir in aviris_dir_list:
        print("\tSearching FTP dir {}...".format(aviris_dir))
        aviris_files = set(ftp.nlst(aviris_dir))
        aviris_scenes = set(
            map(
                lambda x: Path(x).name.replace(".tar.gz", ""),
                filter(
                    lambda x: x.endswith(".tar.gz") and "_" not in Path(x).name,
                    aviris_files,
                ),
            )
        )

        for scene in aviris_scenes:
            s2_file = "{}/{}_refl.tar.gz".format(aviris_dir, scene)
            if s2_file in aviris_files:
                s2_scenes[scene] = "ftp://{}:{}@{}/{}".format(
                    JPL_FTP_USERNAME, JPL_FTP_PASSWORD, JPL_FTP_HOSTNAME, s2_file
                )
    print("Found {} scenes with S2 data".format(len(s2_scenes.keys())))
    return s2_scenes


def map_series_to_item(s2_scenes_map, series):
    year = int(series["Year"])
    hour = max(int(series.get("UTC Hour", 0)), 0)
    minute = max(int(series.get("UTC Minute", 0)), 0)
    flight_dt = (
        datetime(
            int(year),
            int(series["Month"]),
            int(series["Day"]),
            tzinfo=timezone.utc,
        )
        + timedelta(hours=hour, minutes=minute)
    )
    item_id = "aviris_{}".format(series["Flight Scene"])

    lons = [float(series["Lon{}".format(n)]) for n in range(1, 5)]
    lats = [float(series["Lat{}".format(n)]) for n in range(1, 5)]
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    try:
        geometry = kml_poly_to_geom(series["kml_poly"])
    except IndexError:
        geometry = box(*bbox)

    properties = {
        k: series[k]
        for k in (
            "Year",
            "Site Name",
            "NASA Log",
            "Investigator",
            "Comments",
            "Flight Scene",
            "RDN Ver",
            "Scene",
            "GEO Ver",
            "YY",
            "Tape",
            "Flight ID",
            "Flight",
            "Run",
            "Pixel Size",
            "Rotation",
            "Number of Lines",
            "Number of Samples",
            "Solar Elevation",
            "Solar Azimuth",
            "Mean Scene Elevation",
            "Min Scene Elevation",
            "Max Scene Elevation",
            "File Size (Bytes)",
            "Gzip File Size (Bytes)",
        )
    }

    assets = {
        "ftp": pystac.Asset(
            series["link_ftp"],
            title="ftp",
            description="AVIRIS data archive. The file size is described by the 'Gzip File Size' property.",
            media_type="application/gzip",
        ).to_dict(),
        "kml_overlay": pystac.Asset(
            series["link_kml_overlay"],
            title="kml_overlay",
            description="KML file describing the bounding box of the flight",
            media_type="application/vnd.google-earth.kml+xml",
        ).to_dict(),
        "kml_outline": pystac.Asset(
            series["link_kml_outline"],
            title="kml_outline",
            description="KML file describing the flight outline",
            media_type="application/vnd.google-earth.kml+xml",
        ).to_dict(),
        "rgb": pystac.Asset(
            series["link_rgb"],
            title="rgb",
            description="Full resolution RGB image captured by the flight",
            media_type="image/jpeg",
        ).to_dict(),
        "rgb_small": pystac.Asset(
            series["link_rgb_small"],
            title="rgb_small",
            description="A lower resolution thumbnail of the same image as the 'rgb' asset.",
            media_type="image/jpeg",
        ).to_dict(),
        "flight_log": pystac.Asset(
            series["link_log"],
            title="flight_log",
            description="HTML page with table listing the runs for this flight.",
            media_type="text/html",
        ).to_dict(),
    }
    if series["Name"] in s2_scenes_map:
        # Include in properties so we can STAC API query for Items with this asset
        properties["has_refl"] = True
        assets["ftp_refl"] = pystac.Asset(
            s2_scenes_map[series["Name"]],
            title="ftp_refl",
            description="AVIRIS data archive of atmospheric corrected imagery for this scene.",
            media_type="application/gzip",
        ).to_dict()

    return pd.Series(
        {
            "id": item_id,
            "datetime": flight_dt,
            "geometry": geometry,
            "bbox": bbox,
            "properties": properties,
            "assets": assets,
            "links": [],
        }
    )


def aviris_to_dataframe(aviris_csv):

    print("Loading AVIRIS data...")
    df = pd.read_csv("aviris-flight-lines.csv")
    # Filter to only include flights with data
    df = df[(df["Gzip File Size (Bytes)"] > 0) & (df["Number of Samples"] > 0)]

    # There are duplicate rows where the older info is exactly the same except
    # for the link_log column, and the later row has the correct url.
    df = df.drop_duplicates(subset="Flight Scene", keep="last")

    # Ensure all empty values in columns aren't NaN so we write valid STAC
    df = df.fillna("")

    # With the filters above applied to the aviris-flight-lines.csv checked into the repo,
    # we should see exactly this many results. This number may need to be changed if the csv
    # is updated. Ensure that the "Flight Scene" field remains unique in the DF after all
    # filters are applied.
    assert len(df) == 3741

    s2_scenes_map = find_s2_scenes()

    print("Converting AVIRIS to DataFrame...")
    map_series_to_item_partial = partial(map_series_to_item, s2_scenes_map)
    return GeoDataFrame(df.apply(map_series_to_item_partial, axis=1)).set_crs(epsg=4326)


def main():
    df = aviris_to_dataframe("aviris-flight-lines.csv")

    df = stacframes.parents.from_properties_accum(
        ["Year", "Flight"], df, prefix="aviris", separator="_"
    )
    catalog = pystac.Catalog("aviris", AVIRIS_DESCRIPTION)
    stacframes.df_to(catalog, df)

    # Normalize before validation to set all the required object links
    catalog_path = "./data/catalog"
    catalog.normalize_hrefs(catalog_path)
    print("Validating catalog...")
    catalog.validate_all()
    print("Saving catalog to {}...".format(catalog_path))
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print("Done!")


if __name__ == "__main__":
    main()
