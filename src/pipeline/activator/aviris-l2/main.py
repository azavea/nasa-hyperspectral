import argparse
from datetime import datetime, timezone
from math import floor
import os
from pathlib import Path
import shutil
import tarfile
from tempfile import mkdtemp
from urllib.parse import urlparse
import logging
from config import CliConfig

import boto3
from boto3.s3.transfer import TransferConfig
from osgeo import gdal, osr
import pystac
import requests
import urllib.request
import json

from progress import ProgressPercentage, timing, warp_callback, DownloadProgressBar
from stac_client import STACClient

from random import randint
from time import sleep

# set a configurable logging level for the entire app
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='[%(relativeCreated)d|%(levelname)s|%(name)s|%(lineno)d] %(message)s', level=LOG_LEVEL)
logger = logging.getLogger(__name__)

GB = 1024 ** 3

AVIRIS_ARCHIVE_COLLECTION_ID = "aviris-classic"

COG_COLLECTION_EXTENSIONS = [
    'https://stac-extensions.github.io/eo/v1.0.0/schema.json',
    'https://github.com/azavea/nasa-hyperspectral/tree/master/docs/stac/hsi/json-schema/schema.json'
]

COG_ITEM_EXTENSIONS = COG_COLLECTION_EXTENSIONS + \
    ['https://stac-extensions.github.io/projection/v1.0.0/schema.json']

AVIRIS_L2_COG_COLLECTION = pystac.Collection(
    "aviris-l2-cogs",
    "AVIRIS L2 Refl Imagery converted to pixel-interleaved COGs",
    pystac.Extent(
        pystac.SpatialExtent([[-180, -90, 180, 90]]),
        pystac.TemporalExtent(
            [
                [
                    datetime(2014, 1, 1, tzinfo=timezone.utc),
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                ]
            ]
        ),
    ),
    stac_extensions=COG_COLLECTION_EXTENSIONS
)
AVIRIS_L2_COG_COLLECTION.links = []
AVIRIS_L2_COG_COLLECTION.properties = {}

# Nanometers
# STAC Requires Micrometers (x 0.001)
# band -> frequency relation
AVIRIS_L2_BANDS_FREQS_NANO = {
    '1': 365.9136593,
    '10': 453.0496593,
    '100': 1283.2736593,
    '101': 1293.2436593,
    '102': 1303.2136593,
    '103': 1313.1936593,
    '104': 1323.1636593,
    '105': 1333.1336593,
    '106': 1343.1036593,
    '107': 1353.0736593,
    '108': 1363.0436593,
    '109': 1373.0136593,
    '11': 462.7526593,
    '110': 1382.9836593,
    '111': 1392.9536593,
    '112': 1402.9236593,
    '113': 1412.8936593,
    '114': 1422.8636593,
    '115': 1432.8336593,
    '116': 1442.7936593,
    '117': 1452.7636593,
    '118': 1462.7336593,
    '119': 1472.7036593,
    '12': 472.4606593,
    '120': 1482.6636593,
    '121': 1492.6336593,
    '122': 1502.6036593,
    '123': 1512.5736593,
    '124': 1522.5336593,
    '125': 1532.5036593,
    '126': 1542.4636593,
    '127': 1552.4336593,
    '128': 1562.4036593,
    '129': 1572.3636593,
    '13': 482.1736593,
    '130': 1582.3336593,
    '131': 1592.2936593,
    '132': 1602.2636593,
    '133': 1612.2236593,
    '134': 1622.1836593,
    '135': 1632.1536593,
    '136': 1642.1136593,
    '137': 1652.0736593,
    '138': 1662.0436593,
    '139': 1672.0036593,
    '14': 491.8906593,
    '140': 1681.9636593,
    '141': 1691.9336593,
    '142': 1701.8936593,
    '143': 1711.8536593,
    '144': 1721.8136593,
    '145': 1731.7736593,
    '146': 1741.7336593,
    '147': 1751.6936593,
    '148': 1761.6636593,
    '149': 1771.6236593,
    '15': 501.6116593,
    '150': 1781.5836593,
    '151': 1791.5436593,
    '152': 1801.5036593,
    '153': 1811.4536593,
    '154': 1821.4136593,
    '155': 1831.3736593,
    '156': 1841.3336593,
    '157': 1851.2936593,
    '158': 1861.2536593,
    '159': 1871.2136593,
    '16': 511.3376593,
    '160': 1872.3636593,
    '161': 1866.8436593,
    '162': 1876.9136593,
    '163': 1886.9636593,
    '164': 1897.0236593,
    '165': 1907.0836593,
    '166': 1917.1336593,
    '167': 1927.1836593,
    '168': 1937.2336593,
    '169': 1947.2736593,
    '17': 521.0676593,
    '170': 1957.3136593,
    '171': 1967.3636593,
    '172': 1977.3936593,
    '173': 1987.4336593,
    '174': 1997.4636593,
    '175': 2007.5036593,
    '176': 2017.5236593,
    '177': 2027.5536593,
    '178': 2037.5836593,
    '179': 2047.6036593,
    '18': 530.8016593,
    '180': 2057.6236593,
    '181': 2067.6436593,
    '182': 2077.6536593,
    '183': 2087.6636593,
    '184': 2097.6836593,
    '185': 2107.6836593,
    '186': 2117.6936593,
    '187': 2127.6936593,
    '188': 2137.7036593,
    '189': 2147.6936593,
    '19': 540.5406593,
    '190': 2157.6936593,
    '191': 2167.6936593,
    '192': 2177.6836593,
    '193': 2187.6736593,
    '194': 2197.6636593,
    '195': 2207.6436593,
    '196': 2217.6336593,
    '197': 2227.6136593,
    '198': 2237.5836593,
    '199': 2247.5636593,
    '2': 375.5776593,
    '20': 550.2836593,
    '200': 2257.5336593,
    '201': 2267.5136593,
    '202': 2277.4836593,
    '203': 2287.4436593,
    '204': 2297.4136593,
    '205': 2307.3736593,
    '206': 2317.3336593,
    '207': 2327.2936593,
    '208': 2337.2436593,
    '209': 2347.2036593,
    '21': 560.0316593,
    '210': 2357.1536593,
    '211': 2367.0936593,
    '212': 2377.0436593,
    '213': 2386.9936593,
    '214': 2396.9336593,
    '215': 2406.8736593,
    '216': 2416.8036593,
    '217': 2426.7436593,
    '218': 2436.6736593,
    '219': 2446.6036593,
    '22': 569.7836593,
    '220': 2456.5336593,
    '221': 2466.4536593,
    '222': 2476.3836593,
    '223': 2486.3036593,
    '224': 2496.2236593,
    '23': 579.5396593,
    '24': 589.3006593,
    '25': 599.0656593,
    '26': 608.8356593,
    '27': 618.6086593,
    '28': 628.3876593,
    '29': 638.1696593,
    '3': 385.2466593,
    '30': 647.9576593,
    '31': 657.7486593,
    '32': 667.5446593,
    '33': 655.4756593,
    '34': 665.2826593,
    '35': 675.0846593,
    '36': 684.8816593,
    '37': 694.6726593,
    '38': 704.4596593,
    '39': 714.2406593,
    '4': 394.9196593,
    '40': 724.0166593,
    '41': 733.7866593,
    '42': 743.5526593,
    '43': 753.3126593,
    '44': 763.0676593,
    '45': 772.8166593,
    '46': 782.5616593,
    '47': 792.3006593,
    '48': 802.0356593,
    '49': 811.7646593,
    '5': 404.5966593,
    '50': 821.4876593,
    '51': 831.2066593,
    '52': 840.9196593,
    '53': 850.6276593,
    '54': 860.3306593,
    '55': 870.0286593,
    '56': 879.7206593,
    '57': 889.4076593,
    '58': 899.0906593,
    '59': 908.7666593,
    '6': 414.2786593,
    '60': 918.4386593,
    '61': 928.1046593,
    '62': 937.7666593,
    '63': 947.4226593,
    '64': 957.0726593,
    '65': 966.7186593,
    '66': 976.3586593,
    '67': 985.9946593,
    '68': 995.6246593,
    '69': 1005.2536593,
    '7': 423.9646593,
    '70': 1014.8636593,
    '71': 1024.4836593,
    '72': 1034.0936593,
    '73': 1043.6936593,
    '74': 1053.2936593,
    '75': 1062.8836593,
    '76': 1072.4736593,
    '77': 1082.0636593,
    '78': 1091.6336593,
    '79': 1101.2136593,
    '8': 433.6546593,
    '80': 1110.7736593,
    '81': 1120.3436593,
    '82': 1129.8936593,
    '83': 1139.4436593,
    '84': 1148.9936593,
    '85': 1158.5336593,
    '86': 1168.0736593,
    '87': 1177.6036593,
    '88': 1187.1336593,
    '89': 1196.6536593,
    '9': 443.3496593,
    '90': 1206.1636593,
    '91': 1215.6736593,
    '92': 1225.1836593,
    '93': 1234.6836593,
    '94': 1244.1736593,
    '95': 1253.6636593,
    '96': 1263.1436593,
    '97': 1253.3536593,
    '98': 1263.3336593,
    '99': 1273.3036593
}

# sorted by bands
AVIRIS_L2_BANDS_FREQS = [(b, f * 0.001)
                         for b, f in sorted(AVIRIS_L2_BANDS_FREQS_NANO.items(), key=lambda x: x[0])]
# properties."hsi:wavelengths" = [],
AVIRIS_L2_FREQS = [f for b, f in AVIRIS_L2_BANDS_FREQS]

AVIRIS_L2_COG_COLLECTION.properties['eo:bands'] = [
    {'name': b, 'center_wavelength': f} for (b, f) in AVIRIS_L2_BANDS_FREQS]
AVIRIS_L2_COG_COLLECTION.properties['hsi:wavelength_min'] = min(AVIRIS_L2_FREQS)
AVIRIS_L2_COG_COLLECTION.properties['hsi:wavelength_max'] = max(AVIRIS_L2_FREQS)

def activation_output(item_id: str):
    with open('/tmp/activator-output.json', 'w') as outfile:
        json.dump({
            'sourceCollectionId': AVIRIS_L2_COG_COLLECTION.id,
            'sourceItemId': item_id
        }, outfile)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pipeline-uri",
        type=str,
        help="A URI to JSON with instructions"
    )
    parser.add_argument(
        "--pipeline",
        type=str,
        help="JSON with instructions"
    )
    parser.add_argument(
        "--aviris-stac-id",
        type=str,
        help="STAC Item ID to process from the STAC collection"
    )
    parser.add_argument(
        "--aviris-collection-id",
        type=str,
        default=AVIRIS_ARCHIVE_COLLECTION_ID,
    )
    parser.add_argument(
        "--stac-api-uri",
        type=str,
        default=os.environ.get(
            "STAC_API_URI", "http://franklin:9090"
        ),
    )
    parser.add_argument(
        "--s3-bucket", type=str, default=os.environ.get("S3_BUCKET", "aviris-data")
    )
    parser.add_argument(
        "--s3-prefix",
        type=str,
        default=os.environ.get("S3_PREFIX", "aviris-scene-cogs-l2"),
    )
    parser.add_argument(
        "--temp-dir", type=str, default=os.environ.get("TEMP_DIR", None)
    )
    parser.add_argument(
        "--keep-temp-dir",
        action="store_true",
        help="If provided, script does not delete temporary directory before script exits. Useful for debugging.",
    )
    parser.add_argument(
        "--skip-large",
        action="store_true",
        help="If provided, script will not process any COG > 200 MB to keep processing times reasonable. Useful for debugging.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="If provided, force reingest StacItem even though this it is already present in the catalog.",
    )

    try:
        warpMemoryLimit = int(os.environ.get("GDAL_WARP_MEMORY_LIMIT", None))
    except TypeError:
        warpMemoryLimit = None

    # TODO: replace it with parser.parse_args() later
    cli_args, cli_unknown = parser.parse_known_args()

    # parse all cli arguments
    args = CliConfig(cli_args, cli_unknown)

    s3 = boto3.client("s3")
    stac_client = STACClient(args.stac_api_uri)

    # GET STAC Item from AVIRIS Catalog
    item = stac_client.get_collection_item(
        args.aviris_collection_id, args.aviris_stac_id
    )
    l2_asset = item.assets.get("https_refl", None)
    if l2_asset is None:
        raise ValueError(
            "STAC Item {} from {} has no asset 'https_refl'!".format(
                args.aviris_stac_id, args.stac_api_uri
            )
        )
    scene_name = item.properties.get("Name")

    # Create new COG STAC Item
    cog_item_id = "{}_{}_{}".format(
        AVIRIS_L2_COG_COLLECTION.id,
        item.properties.get("Name"),
        item.properties.get("Scene"),
    )

    item.properties['eo:bands'] = AVIRIS_L2_COG_COLLECTION.properties['eo:bands']
    item.properties['hsi:wavelength_min'] = AVIRIS_L2_COG_COLLECTION.properties['hsi:wavelength_min']
    item.properties['hsi:wavelength_max'] = AVIRIS_L2_COG_COLLECTION.properties['hsi:wavelength_max']

    cog_item = pystac.Item(
        cog_item_id,
        item.geometry,
        item.bbox,
        item.datetime,
        item.properties,
        stac_extensions=COG_ITEM_EXTENSIONS,
        collection=AVIRIS_L2_COG_COLLECTION.id,
    )

    # Create COG Collection if it doesn't exist
    if not stac_client.has_collection(AVIRIS_L2_COG_COLLECTION.id):
        stac_client.post_collection(AVIRIS_L2_COG_COLLECTION)

    if not args.force:
        # Exit early if COG STAC Item already exists
        try:
            stac_client.get_collection_item(AVIRIS_L2_COG_COLLECTION.id, cog_item_id)
            logger.info("STAC Item {} already exists. Exiting.".format(cog_item_id))
            activation_output(cog_item_id)
            return
        except requests.exceptions.HTTPError:
            pass

    # Create tmpdir
    temp_dir = Path(args.temp_dir if args.temp_dir is not None else mkdtemp())
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        # Retrieve AVIRIS GZIP for matching scene name
        local_archive = Path(temp_dir, Path(l2_asset.href).name)
        if local_archive.exists():
            logger.info("Using existing archive: {}".format(local_archive))
        else:
            logger.info(f'Downloading archive {local_archive}...')
            gzip_https_url = l2_asset.href
            with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=gzip_https_url.split('/')[-1]) as t:
                urllib.request.urlretrieve(
                    gzip_https_url, filename=local_archive, reporthook=t.update_to)

        # Retrieve file names from archive and extract if not already extracted to temp_dir
        extract_path = Path(temp_dir, scene_name)
        with tarfile.open(local_archive, mode="r") as tar_gz_fp:
            logger.info("Retrieving filenames from {}".format(local_archive))
            with timing("Query archive"):
                tar_files = tar_gz_fp.getnames()
            # logger.info("Files: {}".format(tar_files))

            if extract_path.exists():
                logger.info("Skipping extract, exists at {}".format(extract_path))
            else:
                logger.info("Extracting {} to {}".format(local_archive, extract_path))
                with timing("Extract"):
                    tar_gz_fp.extractall(extract_path)

        # Find HDR data files in unzipped package
        hdr_files = list(filter(lambda x: x.endswith(".hdr"), tar_files))
        logger.info("HDR Files: {}".format(hdr_files))
        for idx, hdr_file_w_ext in enumerate(hdr_files):
            hdr_file_w_ext_path = Path(hdr_file_w_ext)
            hdr_path = Path(extract_path, hdr_file_w_ext_path.with_suffix(""))
            cog_path = hdr_path.with_suffix(".tiff")

            if args.skip_large and os.path.getsize(hdr_path) > 0.2 * GB:
                file_mb = floor(os.path.getsize(hdr_path) / 1024 / 1024)
                logger.info(
                    "--skip-large provided. Skipping {} with size {}mb".format(
                        hdr_path, file_mb
                    )
                )
                continue

            # Convert HDR data to pixel interleaved COG with GDAL
            # NUM_THREADS only speeds up compression and overview generation
            # gdal.Warp is used to fix rasters rotation
            warp_opts = gdal.WarpOptions(
                callback=warp_callback,
                warpOptions=["NUM_THREADS=ALL_CPUS"],
                creationOptions=["NUM_THREADS=ALL_CPUS", "COMPRESS=DEFLATE", "BIGTIFF=YES"],
                multithread=True,
                warpMemoryLimit=warpMemoryLimit,
                format="COG"
            )
            logger.info("Converting {} to {}...".format(hdr_path, cog_path))
            with timing("GDAL Warp"):
                gdal.Warp(str(cog_path), str(hdr_path), options=warp_opts)

            # read metadata from the transformed TIFF
            cog_ds = gdal.Open(str(cog_path))
            cog_proj = osr.SpatialReference(wkt=cog_ds.GetProjection())
            cog_proj.AutoIdentifyEPSG()

            # set projection
            cog_item.properties['proj:epsg'] = int(cog_proj.GetAttrValue('AUTHORITY', 1))

            # Upload  COG and metadata, if written, to S3 bucket + key
            key = Path(
                args.s3_prefix,
                str(item.properties.get("Year")),
                str(item.properties.get("Name")),
                cog_path.name,
            )
            s3_uri = "s3://{}/{}".format(args.s3_bucket, key)
            logger.info("Uploading {} to {}".format(cog_path, s3_uri))
            s3.upload_file(
                str(cog_path),
                args.s3_bucket,
                str(key),
                Callback=ProgressPercentage(str(cog_path)),
                Config=TransferConfig(multipart_threshold=1 * GB),
            )
            cog_metadata_path = cog_path.with_suffix(".tiff.aux.xml")
            if cog_metadata_path.exists():
                metadata_key = Path(args.s3_prefix, cog_metadata_path.name)
                metadata_s3_uri = "s3://{}/{}".format(args.s3_bucket, metadata_key)
                logger.info("Uploading {} to {}".format(cog_metadata_path, metadata_s3_uri))
                s3.upload_file(
                    str(cog_metadata_path), args.s3_bucket, str(metadata_key)
                )

            # Add assets to COG STAC Item
            cog_item.add_asset(
                "cog_{}".format(idx),
                pystac.Asset(s3_uri, media_type=pystac.MediaType.COG, roles=["data"]),
            )
            if cog_metadata_path.exists():
                cog_item.add_asset(
                    "metadata_{}".format(idx),
                    pystac.Asset(
                        metadata_s3_uri,
                        media_type=pystac.MediaType.XML,
                        roles=["metadata"],
                    ),
                )
    finally:
        if not args.keep_temp_dir:
            logger.info("Removing temp dir: {}".format(temp_dir))
            shutil.rmtree(temp_dir, ignore_errors=True)

    # Add COG Item to AVIRIS L2 STAC Collection
    logger.info("POST Item {} to {}".format(cog_item.id, args.stac_api_uri))
    item_data = stac_client.post_collection_item(AVIRIS_L2_COG_COLLECTION.id, cog_item)
    if item_data.get('id', None):
        logger.info("Success: {}".format(item_data['id']))
        activation_output(item_data['id'])
    else:
        logger.error("Failure: {}".format(item_data))
        return -1


if __name__ == "__main__":
    main()
