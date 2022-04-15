# flake8: noqa

import hashlib
import re

from functools import partial

from pystac.stac_io import DefaultStacIO, StacIO
from pystac import Catalog
from rastervision.core.backend import *
from rastervision.core.data import *
from rastervision.core.data import (
    ClassConfig, DatasetConfig, GeoJSONVectorSourceConfig,
    RasterioSourceConfig, RasterizedSourceConfig, RasterizerConfig,
    SceneConfig, SemanticSegmentationLabelSourceConfig, CastTransformerConfig)
from rastervision.core.rv_pipeline import *
from rastervision.gdal_vsi.vsi_file_system import VsiFileSystem
from rastervision.pytorch_backend import *
from rastervision.pytorch_learner import *


def pystac_workaround(uri):
    if uri.startswith('/vsizip/') and not uri.startswith('/vsizip//'):
        uri = uri.replace('/vsizip/', '/vsizip//')
    if uri.startswith('/vsitar/vsigzip/') and not uri.startswith('/vsitar/vsigzip//'):
        uri = uri.replace('/vsitar/vsigzip/', '/vsitar/vsigzip//')

    return uri
    return VsiFileSystem.read_str(uri)


class CustomStacIO(DefaultStacIO):
    def read_text(self, source, *args, **kwargs) -> str:
        return VsiFileSystem.read_str(pystac_workaround(source))

    def write_text(self, dest, txt, *args, **kwargs) -> None:
        pass
StacIO.set_default(CustomStacIO)


def root_of_tarball(tarball: str) -> str:
    catalog_root = pystac_workaround(tarball)
    while not (catalog_root.endswith('catalog.json') and catalog_root is not None):
        paths = VsiFileSystem.list_paths(catalog_root)
        if len(paths) > 1:
            paths = list(filter(lambda s: s.endswith('catalog.json'), paths))
        if len(paths) != 1:
            raise Exception('Unrecognizable Tarball')
        catalog_root = f'{paths[0]}'
    return catalog_root


def hrefs_from_catalog(catalog: Catalog, N: int = None) -> Tuple[str, str]:

    def find_label_collection(c):
        return 'label' in str.lower(c.description)

    catalog.make_all_asset_hrefs_absolute()
    labels = next(filter(find_label_collection, catalog.get_children()))
    label_items = list(labels.get_items())

    label_hrefs = []
    imagery_hrefs = []
    for item in label_items:
        try:
            imagery = item.get_links('source')[0]
            imagery.resolve_stac_object()
            imagery_href = imagery.target.assets.get('cog').href
        except:
            imagery_href = None
        label_href = pystac_workaround(item.assets.get('data').href)
        label_hrefs.append(label_href)
        if imagery_href.startswith('./'):
            imagery_href = re.sub('^\.\/[0-9]+-', './', imagery_href)
        imagery_href = imagery_href.replace('14060at01p00r17', '140603t01p00r17')
        imagery_hrefs.append(imagery_href)

    if N is not None:
        N = int(N)
        label_hrefs = [label_hrefs[N]]
        imagery_hrefs = [imagery_hrefs[N]]
    return (label_hrefs, imagery_hrefs)


def hrefs_to_sceneconfig(
        imagery: str,
        labels: Optional[str],
        name: str,
        class_id_filter_dict: Dict[int, str],
        extent_crop: Optional[CropOffsets] = None) -> SceneConfig:

    transformers = [CastTransformerConfig(to_dtype='float16')]
    image_source = RasterioSourceConfig(
        channel_order=list(range(224)),
        uris=[imagery],
        allow_streaming=True,
        transformers=transformers,
        extent_crop=extent_crop,
    )

    label_vector_source = GeoJSONVectorSourceConfig(
        uri=labels,
        class_id_to_filter=class_id_filter_dict,
        default_class_id=0xff)
    label_raster_source = RasterizedSourceConfig(
        vector_source=label_vector_source,
        rasterizer_config=RasterizerConfig(background_class_id=0,
                                           all_touched=True))
    label_source = SemanticSegmentationLabelSourceConfig(
        raster_source=label_raster_source)

    return SceneConfig(id=name,
                       raster_source=image_source,
                       label_source=label_source)


def get_scenes(
    json_file: str,
    class_config: ClassConfig,
    class_id_filter_dict: dict,
    catalog_dir: str, imagery_dir: str,
    train_crops: List[CropOffsets] = [],
    val_crops: List[CropOffsets] = [],
    N: int = None
) -> Tuple[List[SceneConfig], List[SceneConfig]]:

    train_scenes = []
    val_scenes = []
    with open(json_file, 'r') as f:
        for catalog_imagery in json.load(f):
            catalog = catalog_imagery.get('catalog')
            catalog = catalog.strip()
            catalog = f'{catalog_dir}/{catalog}'
            catalog = catalog.replace('s3://', '/vsizip/vsis3/')
            (labelss, imagerys) = hrefs_from_catalog(Catalog.from_file(root_of_tarball(catalog)), N)
            imagery_name = imagery = catalog_imagery.get('imagery')
            if imagery_name is not None:
                imagery = imagery.strip()
                imagery = f'{imagery_dir}/{imagery}'
                if '.zip' in imagery:
                    imagery = imagery.replace('s3://', '/vsizip/vsis3/')
                else:
                    imagery = imagery.replace('s3://', '/vsis3/')
                imagerys = [imagery]*len(labelss)
            else:
                imagerys = map(lambda i: i.replace('_rgb',''), imagerys)
                if not imagery_dir.endswith('/'):
                    imagery_dir = imagery_dir + '/'
                imagerys = list(map(lambda i: i.replace('./', imagery_dir), imagerys))
            h = hashlib.sha256(catalog.encode()).hexdigest()
            del imagery
            print('imagery', imagerys)
            print('labels', labelss)

            make_scene = partial(hrefs_to_sceneconfig,
                                 class_id_filter_dict=class_id_filter_dict)
            for j, (labels, imagery) in enumerate(zip(labelss, imagerys)):
                for i, crop in enumerate(train_crops):
                    scene = make_scene(name=f'{h}-train-{i}-{j}', extent_crop=crop, imagery=imagery, labels=labels)
                    train_scenes.append(scene)
                for i, crop in enumerate(val_crops):
                    scene = make_scene(name=f'{h}-val-{i}-{j}', extent_crop=crop, imagery=imagery, labels=labels)
                    val_scenes.append(scene)
    return train_scenes, val_scenes


def get_config(runner,
               root_uri,
               json,
               dataset,
               catalog_dir='/vsizip//workdir', imagery_dir='/opt/data',
               chip_sz=512,
               N=None):

    chip_sz = int(chip_sz)

    if dataset == 'cloud':
        class_config = ClassConfig(
            names=['algal_bloom', 'normal_water',
                   'cloud', 'cloud_shadow', 'other'],
            colors=['green', 'blue', 'white', 'gray', 'brown'])
        class_id_filter_dict = {
            0: ['==', 'default', 'Algal bloom'],
            1: ['==', 'default', 'Non-algal-bloomed water'],
            2: ['==', 'default', 'Cloud'],
            3: ['==', 'default', 'Cloud shadow'],
            0xff: ['==', 'default', 'Other '],
        }
    elif dataset == 'tree':
        class_config = ClassConfig(
            names=['green_stage', 'red_stage', 'other'],
            colors=['green', 'brown', 'cyan'])
        class_id_filter_dict = {
            0: ['==', 'default', "Green stage conifer"],
            1: ['==', 'default', "Red stage conifer"],
            0xff: ['==', 'default', "Other"],
        }
    else:
        raise Exception()

    train_crops = []
    val_crops = []
    for x in range(0, 5):
        for y in range(0, 5):
            x_start = x / 5.0
            x_end = 0.80 - x_start
            y_start = y / 5.0
            y_end = 0.80 - y_start
            crop = [x_start, y_start, x_end, y_end]
            if x == y:
                val_crops.append(crop)
            else:
                train_crops.append(crop)

    scenes = get_scenes(json,
                        class_config,
                        class_id_filter_dict,
                        catalog_dir, imagery_dir,
                        train_crops=train_crops,
                        val_crops=val_crops, N=N)

    train_scenes, validation_scenes = scenes

    print(f'{len(train_scenes)} training scenes')
    print(f'{len(validation_scenes)} validation scenes')

    dataset = DatasetConfig(
        class_config=class_config,
        train_scenes=train_scenes,
        validation_scenes=validation_scenes,
    )

    solver = SolverConfig()
    data = SemanticSegmentationImageDataConfig(
        img_sz=chip_sz,
        num_workers=0,
        preview_batch_limit=8
    )
    model = SemanticSegmentationModelConfig()

    backend = PyTorchSemanticSegmentationConfig(model=model, data=data, solver=solver)

    chip_options = SemanticSegmentationChipOptions(
        window_method=SemanticSegmentationWindowMethod.sliding, stride=chip_sz)

    return SemanticSegmentationConfig(root_uri=root_uri,
                                      dataset=dataset,
                                      backend=backend,
                                      train_chip_sz=chip_sz,
                                      predict_chip_sz=chip_sz,
                                      chip_options=chip_options,
                                      chip_nodata_threshold=.75,
                                      img_format='npy',
                                      label_format='png')
