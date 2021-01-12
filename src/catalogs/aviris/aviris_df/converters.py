from datetime import datetime, timedelta, timezone
from xml.dom import minidom

import fastkml
import pandas as pd
import pystac
from shapely.geometry import box


def kml_poly_to_geom(kml_poly):
    """ Convert KML polygon in AVIRIS kml_poly field to a shapely Geometry """
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


def aviris_series_to_item(s2_scenes_map, series):
    """ Convert AVIRIS CSV series to another Series compatible with stacframes

    s2_scenes_map is an object where the key is Flight Scene and the value is an ftp url to
    that Flight Scene's s2 atmo corrected data file

    This method is currently valid for both AVIRIS Class and AVIRIS NG

    """
    year = int(series["Year"])
    hour = min(max(int(series.get("UTC Hour", 0)), 0), 23)
    minute = min(max(int(series.get("UTC Minute", 0)), 0), 59)
    try:
        flight_dt = datetime(
            int(year), int(series["Month"]), int(series["Day"]), tzinfo=timezone.utc
        ) + timedelta(hours=hour, minutes=minute)
    except (ValueError, OverflowError):
        [month, day, year] = series["Date"].split("/")
        flight_dt = datetime(
            int(year), int(month), int(day), tzinfo=timezone.utc
        ) + timedelta(hours=hour, minutes=minute)

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
            "Name",
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
    # Add any layer ids of interest
    properties["layer:ids"] = [series["collection"]]

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
