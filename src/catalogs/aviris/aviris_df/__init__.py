from ftplib import FTP
from functools import partial
from pathlib import Path
import logging
import os

from geopandas import GeoDataFrame
import pandas as pd

from .converters import aviris_series_to_item

logger = logging.getLogger(__name__)

AVIRIS_DESCRIPTION = "AVIRIS is an acronym for the Airborne Visible InfraRed Imaging Spectrometer. AVIRIS is a premier instrument in the realm of Earth Remote Sensing. It is a unique optical sensor that delivers calibrated images of the upwelling spectral radiance in 224 contiguous spectral channels (also called bands) with wavelengths from 400 to 2500 nanometers (nm). AVIRIS has been flown on four aircraft platforms: NASA's ER-2 jet, Twin Otter International's turboprop, Scaled Composites' Proteus, and NASA's WB-57. The ER-2 flies at approximately 20 km above sea level, at about 730 km/hr. The Twin Otter aircraft flies at 4km above ground level at 130km/hr. AVIRIS has flown all across the US, plus Canada and Europe. This catalog contains all AVIRIS missions from 2006 - 2019."


class AvirisClassic:
    """ Load AVIRIS Classic flights as a dataframe

    Usage: `AvirisClassic.as_df(path_to_aviris_classic_csv)`

    """

    COLLECTION_NAME = "aviris-classic"

    @classmethod
    def as_df(cls, aviris_classic_csv):

        logger.info("Loading AVIRIS data...")
        df = pd.read_csv(aviris_classic_csv)
        # Filter to only include flights with data
        df = df[(df["Gzip File Size (Bytes)"] > 0) & (df["Number of Samples"] > 0)]

        # There are duplicate rows where the older info is exactly the same except
        # for the link_log column, and the later row has the correct url.
        df = df.drop_duplicates(subset="Flight Scene", keep="last")

        # Ensure all empty values in columns aren't NaN so we write valid STAC
        df = df.fillna("")

        # Add collection name
        df.loc[:, "collection"] = cls.COLLECTION_NAME

        # With the filters above applied to the aviris-flight-lines.csv checked into the repo,
        # we should see exactly this many results. This number may need to be changed if the csv
        # is updated. Ensure that the "Flight Scene" field remains unique in the DF after all
        # filters are applied.
        assert len(df) == 3741

        s2_scenes_map = cls._find_s2_scenes()

        logger.info("Converting AVIRIS to DataFrame...")
        map_series_to_item_partial = partial(aviris_series_to_item, s2_scenes_map)
        return GeoDataFrame(df.apply(map_series_to_item_partial, axis=1)).set_crs(
            epsg=4326
        )

    @classmethod
    def _find_s2_scenes(cls):
        logger.info("Finding AVIRIS Classic scenes with atmo corrected data...")
        JPL_FTP_HOSTNAME = "popo.jpl.nasa.gov"
        JPL_FTP_USERNAME = "avoil"
        JPL_FTP_PASSWORD = "Gulf0il$pill"

        ftp = FTP(JPL_FTP_HOSTNAME)
        ftp.login(JPL_FTP_USERNAME, JPL_FTP_PASSWORD)

        s2_scenes = {}

        aviris_dir_list = ftp.nlst()
        for aviris_dir in aviris_dir_list:
            logger.info("\tSearching FTP dir {}...".format(aviris_dir))
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
        logger.info("Found {} scenes with refl data".format(len(s2_scenes.keys())))
        return s2_scenes


class AvirisNg:
    """ Load AVIRIS NG flights as a dataframe

    Usage: `AvirisNg.as_df(path_to_aviris_ng_csv)`

    """

    COLLECTION_NAME = "aviris-ng"

    @classmethod
    def as_df(cls, aviris_ng_csv):

        logger.info("Loading AVIRIS NG data...")
        df = pd.read_csv(aviris_ng_csv)
        df = df.fillna("")
        # Skip entries with no geometry
        df = df[df["kml_poly"] != ""]
        df = df.drop_duplicates(subset="Flight Scene", keep="last")

        # Add collection name
        df.loc[:, "collection"] = cls.COLLECTION_NAME

        s2_scenes_map = cls._find_s2_scenes()

        logger.info("Converting AVIRIS NG to DataFrame...")
        map_series_to_item_partial = partial(aviris_series_to_item, s2_scenes_map)
        return GeoDataFrame(df.apply(map_series_to_item_partial, axis=1)).set_crs(
            epsg=4326
        )

    @classmethod
    def _find_s2_scenes(cls):
        logger.info("Finding AVIRIS NG scenes with atmo corrected data...")
        JPL_FTP_HOSTNAME = "avng.jpl.nasa.gov"
        JPL_FTP_USERNAME = "avng_dp"
        JPL_FTP_PASSWORD = "P73axIvP"

        ftp = FTP(JPL_FTP_HOSTNAME)
        ftp.login(JPL_FTP_USERNAME, JPL_FTP_PASSWORD)

        s2_scenes = {}

        aviris_dir_list = ftp.nlst()
        for aviris_dir in aviris_dir_list:
            logger.info("\tSearching FTP dir {}...".format(aviris_dir))
            aviris_files = set(ftp.nlst(aviris_dir))
            aviris_scenes = set(
                map(
                    lambda x: Path(x).name.replace(".tar.gz", ""),
                    filter(
                        lambda x: x.endswith(".tar.gz") and "rfl" not in Path(x).name,
                        aviris_files,
                    ),
                )
            )

            for scene in aviris_scenes:
                s2_file = "{}rfl.tar.gz".format(scene)
                if s2_file in aviris_files:
                    s2_scenes[scene] = "ftp://{}:{}@{}/{}".format(
                        JPL_FTP_USERNAME, JPL_FTP_PASSWORD, JPL_FTP_HOSTNAME, s2_file
                    )
        logger.info("Found {} scenes with refl data".format(len(s2_scenes.keys())))
        return s2_scenes
