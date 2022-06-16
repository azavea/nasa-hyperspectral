![Perceptron](https://upload.wikimedia.org/wikipedia/en/5/52/Mark_I_perceptron.jpeg)

This directory and its subdirectories contain code for training machine learning models for three use cases and code for using those models.
The three use cases are: cloud detection,  detecting algal blooms in hyperspectral imagery (ergo the subdirectory name: [`src/algae-model`](src/algae-model)), and detecting red-stage (versus green-stage) conifers in a particular part of California.
Much of the code found here is experimental and is preserved for purposes of completeness, but the tree health code and models might be somewhat useful.

# Cloud Detection #

![Clouds](https://upload.wikimedia.org/wikipedia/commons/4/46/Socrates_in_a_basket.jpg)

These are (currently incomplete) experiments that are somewhat adjacent to the (non-experimental and well-functioning) [Azavea cloud model](https://github.com/azavea/cloud-model).
The two are related in that the latter operates on Sentinel-2 imagery (L1 and L2) and the former is the beginnings of an effort to bootstrap a general model (which works with L1 AVIRIS imagery and Sentinel-2 imagery) on top of the Sentinel-2 starting point.

## Dataset Creation ##

### Part 1 ###

The first part of the dataset for this effort can be created by starting with the initial cloud factory algal bloom labels as input and using raster vision to convert those labels into a dataset.
That is done by running the command
```bash
rastervision run local pipeline.py chip -a dataset cloud \
   -a catalog_dir /vsizip//catalogs -a imagery_dir /opt/data \
   -a json cloud-catalogs.json -a root_uri /opt/data/chip
```
where the json file in question is [src/algae-model/rastervision/cloud-catalogs.json](src/algae-model/rastervision/cloud-catalogs.json).
The command must be run in the context of a properly-configured Raster Vision installation.
Documentation on that topic can be found [here](https://readthedocs.org/projects/raster-vision/).

### Part 2 ###

The second part of the dataset for this effort can be found/created as part of the [Azavea cloud model](https://github.com/azavea/cloud-model) (already discussed).

## Model Training ##

Training of a model can be done with the script [src/algae-model/src/train_seg.py](src/algae-model/src/train_seg.py).
The script attempts to use the datasets just mentioned to produce a segmentation model for clouds in aerial imagery that works on L1 AVIRIS imagery as well as Sentinel-2 imagery.
The script can be invoked by typing something like the following
```bash
./train_seg.py --aviris-l1-path /data/AVIRIS_chips/ \
   --sentinel-l1c-path /data/CLOUD_MODEL_L1C_chips/ \
   --sentinel-l2a-path /data/CLOUD_MODEL_L2A_chips/ \
   --lr 1e-3 --num-workers 2 --pth-save model.pth
```
from within a docker container with the appropriate dependencies present and the relevant datasets mounted in the correct places.

# Algal Blooms #

![Algae](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Gephyrocapsa_oceanica_color.jpg/600px-Gephyrocapsa_oceanica_color.jpg)

This is another partially-complete effort.
The intention here was to create a single model that could detect algal blooms in 4-band Planet imagery, AVIRIS imagery, or Sentinel-2 imagery.

## Scene Gathering ##

Dataset creation for this model is complicated.
The dataset used to train this model is a fusion of boot-on-the-ground algae observations (taken from three datasets) with available imagery that coincides with those observations in space and time.
The three observation datasets are [FHAB](https://data.cnra.ca.gov/dataset/surface-water-freshwater-harmful-algal-blooms), [PMN](https://www.ncei.noaa.gov/products/phytoplankton-monitoring-network), and [HASBOS](https://habsos.noaa.gov/).

Observations from those three datasets are (respectively) turned into a canonical CSV format by the scripts [`fhab.py`](src/algae-model/scripts/fhab.py), [`pmn.py`](src/algae-model/scripts/pmn.py), and [`hasbos.py`](src/algae-model/scripts/hasbos.py).

### AVIRIS ###

To join the canonical CSVs to AVIRIS imagery, the script [`franklin.py`](src/algae-model/script/franklin.py) is used to generate queries that can be issued to the NASA HSI [Franklin](https://github.com/azavea/franklin) instance.
Those queries are stored to files with the extension `.query`.
Those queries can then be issued to Franklin using `curl` by typing something like
```bash
curl -d @some.query -H 'Content-Type: application/json' https://franklin.nasa-hsi.azavea.com/search/
```
which will generate a number of responses (one per invocation of `curl`) each containing some number of AVIRIS scene IDs.
One can then use the [AVIRIS activator](../deployment/argo-workflows/eks/README.md) to ask the NASA HSI argo machinery to download and index the imagery (using the scene IDs).
With an appropriate Kubernetes and argo setup, this can be done by typing something like
```bash
```

### Planet ###

Something similar can be done for 4-band Planet imagery, though the respective GeoJSON portions of the queries generated by the `franklin.py` script must be run through the [`planet-query.py`](../src/utils/planet-query.py) script instead of sent to Franklin.
This is because Franklin does not index Planet imagery which has not been downloaded.
Once the Planet scenes have been activated and downloaded using the project's argo machinary, those downloaded scenes will be in Franlin.
(The Planet scene IDs that are obtained from the `planet-query.py` script must be sent to the argo machinary for download and indexing in a manner analogous to the AVIRIS procedure.)

### Sentinel-2 ###

The analogous process for Sentinel-2 is done using the [`sat-search.py`](../src/scripts/sat-search.py) script.
This script uses the Element84 to search for responsive scenes in the AWS Sentinel-2 collection.
The scene IDs that are reported can then be sent to the Sentinel-2 activator functionality to produce Franklin-indexed COGs.

## Dataset Creation ##

### Classification Dataset ###

With all of the desired scenes indexed in Franklin, one can use the script
[`dataset.py`](../src/scripts/dataset.py) to create a collection of chips which are classified as either having or not having algal blooms.
This script only works on AVIRIS and Sentinel-2 imagery.
The script can be run with an invocation such as
```bash
./dataset.py --csv observations.csv.lz --days 1 --imagery aviris --json items.json.lz \
   --window-size 32 --savez aviris-1day.npz
```

The file `observations.csv.lz`, in this example, is the combined canonical CSV for the three input observation datasets.

The file items.json.lz is a (compressed) dump of the items in the Franklin AVIRIS collection.
It can be obtained by typing something like
```bash
curl 'https://franklin.nasa-hsi.azavea.com/collections/aviris-l1-cogs?limit=10000' | \
   python3 -m json.tool > items.json
lzip -9 items.json
```
An analogous process is used for obtaining `items.json` or `items.json.lz` files for Sentinel-2 or Planet imagery.

The output file `aviris-1day.npz` in this example is (compressed) NumPy data containing the positive and negative chips.

### Unlabeled Dataset ###

The script [`transfer_dataset.py`](../src/scripts/transfer_dataset.py),
is used to create unclassified (unlabeled) data for training purposes.

## Model Training ##

Training is done with the
[`train.py`](./src/algae-model/src/train.py) script.
An example of use follows
```bash
./train.py --backbone mobilenet_v3_large \
   --classification-savezs aviris-1day.npz sentinel2-1-day.npz \
   --unlabeled-savezs aviris-transfer.npz planet-transfer.npz \
   --pth-save model.pth
```
