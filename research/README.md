![Perceptron](https://upload.wikimedia.org/wikipedia/en/5/52/Mark_I_perceptron.jpeg)

This directory and its subdirectories contain code for training machine learning models for three use cases and code for using those models.
The three use cases are: cloud detection,  detecting algal blooms in hyperspectral imagery (ergo the subdirectory name: [src/algae-model](src/algae-model)), and detecting red-stage (versus green-stage) conifers in a particular part of California.
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
rastervision run local pipeline.py chip -a dataset cloud -a catalog_dir /vsizip//catalogs -a imagery_dir /opt/data -a json cloud-catalogs.json -a root_uri /opt/data/chip
```
where the json file in question is [src/algae-model/rastervision/cloud-catalogs.json](src/algae-model/rastervision/cloud-catalogs.json).
The command must be run in the context of a properly-configured Raster Vision installation.
Documentation on that topic can be found [here](https://readthedocs.org/projects/raster-vision/).

### Part 2 ###

The second part of the dataset for this effort can be found as part of the [Azavea cloud model](https://github.com/azavea/cloud-model) (already discussed).

## Model Training ##

Training of a model can be done with the script [src/algae-model/src/train_seg.py](src/algae-model/src/train_seg.py).
The script attempts to use the datasets just mentioned to produce a segmentation model for clouds in aerial imagery that works on L1 AVIRIS imagery as well as Sentinel-2 imagery.
The script can be invoked by typing something like the following
```bash
./train_seg.py --aviris-l1-path /data/AVIRIS_chips/ --sentinel-l1c-path /data/CLOUD_MODEL_L1C_chips/ --sentinel-l2a-path /data/CLOUD_MODEL_L2A_chips/ --lr 1e-3 --num-workers 2 --pth-save model.pth
```
from within a docker container with the appropriate dependencies present and the relevant datasets mounted in the correct places.

# Algal Blooms #

