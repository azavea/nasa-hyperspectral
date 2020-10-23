import argparse
import csv
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import sys
from xml.dom import minidom

import fastkml
import pystac
from shapely.geometry import GeometryCollection, box, mapping, shape


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


AVIRIS_DESCRIPTION = "AVIRIS is an acronym for the Airborne Visible InfraRed Imaging Spectrometer. AVIRIS is a premier instrument in the realm of Earth Remote Sensing. It is a unique optical sensor that delivers calibrated images of the upwelling spectral radiance in 224 contiguous spectral channels (also called bands) with wavelengths from 400 to 2500 nanometers (nm). AVIRIS has been flown on four aircraft platforms: NASA's ER-2 jet, Twin Otter International's turboprop, Scaled Composites' Proteus, and NASA's WB-57. The ER-2 flies at approximately 20 km above sea level, at about 730 km/hr. The Twin Otter aircraft flies at 4km above ground level at 130km/hr. AVIRIS has flown all across the US, plus Canada and Europe. This catalog contains all AVIRIS missions from 2006 - 2019."


def default_year_extent(year):
    return pystac.Extent(
        pystac.SpatialExtent([None, None, None, None]),
        pystac.TemporalExtent(
            [
                (
                    datetime(int(year), 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                    datetime(
                        int(year),
                        12,
                        31,
                        23,
                        59,
                        59,
                        tzinfo=timezone.utc,
                    ),
                )
            ]
        ),
    )


def default_flight_extent(flight_dt):
    return pystac.Extent(
        pystac.SpatialExtent([None, None, None, None]),
        pystac.TemporalExtent([(flight_dt, flight_dt)]),
    )


def kml_poly_to_geom(kml_poly):
    # Not all KML polygons are correct (missing LinearRing tag); grab coords directly
    kmldom = minidom.parseString(
        '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark>'
        + kml_poly
        + "</Placemark></Document></kml>"
    )
    coords = kmldom.getElementsByTagName("outerBoundaryIs")[0].getElementsByTagName(
        "coordinates"
    )[0]
    kml = fastkml.KML()
    kml.from_string(
        '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><Polygon><outerBoundaryIs><LinearRing>'
        + coords.toxml()
        + "</LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>"
    )
    return next(next(kml.features()).features()).geometry


def set_collection_bounds(collection):
    """ Update the spatial and temporal bounds of a pystac.Collection """
    if not isinstance(collection, pystac.Collection):
        return

    geoms = []
    dates = []
    for i in collection.get_all_items():
        geoms.append(shape(i.geometry))
        dates.append(i.datetime)
    if len(geoms) > 0:
        bounds = GeometryCollection(geoms).bounds
        collection.extent.spatial = pystac.SpatialExtent([bounds])
    if len(dates) > 0:
        collection.extent.temporal = pystac.TemporalExtent([(min(dates), max(dates))])


def set_catalog_bounds(catalog):
    """ Recursively update the pystac.Extents for all pystac.Collections contained in catalog """
    for stac_object in catalog.get_children():
        set_catalog_bounds(stac_object)
    set_collection_bounds(catalog)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-path",
        default="./data/catalog",
        help="Local file path to write catalog to",
    )
    args = parser.parse_args()

    # First we have to monkeypatch a fastkml date method. It crashes on parsing invalid dates
    # that are present in the AVIRIS KML files. We only want the polygon so it's fine to just
    # not parse dates.
    def fastkml_timestamp_from_element_stub(self, element):
        pass

    fastkml.kml.TimeStamp.from_element = fastkml_timestamp_from_element_stub

    catalog = pystac.Catalog("aviris", AVIRIS_DESCRIPTION)

    aviris_csv = Path(Path(__file__).parent.absolute(), "aviris-flight-lines.csv")
    with open(aviris_csv) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            # Filter rows with invalid data
            if not (
                int(row["Gzip File Size (Bytes)"]) > 0
                and int(row["Number of Samples"]) > 0
            ):
                continue

            year = int(row["Year"])
            year_collection_id = "aviris_{}".format(year)
            collection = catalog.get_child(year_collection_id)
            if collection is None:
                collection = pystac.Collection(
                    year_collection_id,
                    "{} AVIRIS Missions".format(year),
                    default_year_extent(year),
                )
                catalog.add_child(collection)
                logger.info("Created new Collection({})".format(collection.id))

            # Limit these to positive numbers because -999 is used as "unknown" in csv
            # Use timedelta for hh:mm because some values are out of range, e.g. minutes=60
            hour = max(int(row.get("UTC Hour", 0)), 0)
            minute = max(int(row.get("UTC Minute", 0)), 0)
            flight_dt = (
                datetime(
                    int(year),
                    int(row["Month"]),
                    int(row["Day"]),
                    tzinfo=timezone.utc,
                )
                + timedelta(hours=hour, minutes=minute)
            )

            flight_collection_id = "aviris_{}_{}".format(year, row["Flight"])
            flight_collection = collection.get_child(flight_collection_id)
            if flight_collection is None:
                flight_collection = pystac.Collection(
                    flight_collection_id,
                    "Flight Number {}".format(row["Flight"]),
                    default_flight_extent(flight_dt),
                )
                collection.add_child(flight_collection)
                logger.info("\tCreated new Collection({})".format(flight_collection.id))

            item_id = "aviris_{}".format(row["Flight Scene"])
            # There are duplicate rows where the older info is exactly the same except
            # for link_log, and the later row has the correct url.
            if flight_collection.get_item(item_id) is not None:
                logger.warning(
                    "\t\tSuperseding duplicate Item {} with newer info...".format(
                        item_id
                    )
                )
                flight_collection.remove_item(item_id)

            lons = [float(row["Lon{}".format(n)]) for n in range(1, 5)]
            lats = [float(row["Lat{}".format(n)]) for n in range(1, 5)]
            bbox = [min(lons), min(lats), max(lons), max(lats)]
            try:
                geometry = kml_poly_to_geom(row["kml_poly"])
            except IndexError:
                geometry = box(*bbox)

            properties = {
                k: row[k]
                for k in (
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

            item = pystac.Item(item_id, mapping(geometry), bbox, flight_dt, properties)
            item.add_asset(
                "ftp",
                pystac.Asset(
                    row["link_ftp"],
                    title="ftp",
                    description="AVIRIS data archive. The file size is described by the 'Gzip File Size' property.",
                    media_type="application/gzip",
                ),
            )
            item.add_asset(
                "kml_overlay",
                pystac.Asset(
                    row["link_kml_overlay"],
                    title="kml_overlay",
                    description="KML file describing the bounding box of the flight",
                    media_type="application/vnd.google-earth.kml+xml",
                ),
            )
            item.add_asset(
                "kml_outline",
                pystac.Asset(
                    row["link_kml_outline"],
                    title="kml_outline",
                    description="KML file describing the flight outline",
                    media_type="application/vnd.google-earth.kml+xml",
                ),
            )
            item.add_asset(
                "rgb",
                pystac.Asset(
                    row["link_rgb"],
                    title="rgb",
                    description="Full resolution RGB image captured by the flight",
                    media_type="image/jpeg",
                ),
            )
            item.add_asset(
                "rgb_small",
                pystac.Asset(
                    row["link_rgb_small"],
                    title="rgb_small",
                    description="A lower resolution thumbnail of the same image as the 'rgb' asset.",
                    media_type="image/jpeg",
                ),
            )
            item.add_asset(
                "flight_log",
                pystac.Asset(
                    row["link_log"],
                    title="flight_log",
                    description="HTML page with table listing the runs for this flight.",
                    media_type="text/html",
                ),
            )

            flight_collection.add_item(item)

    set_catalog_bounds(catalog)
    catalog.normalize_and_save(
        args.output_path, catalog_type=pystac.CatalogType.SELF_CONTAINED
    )


if __name__ == "__main__":
    main()
