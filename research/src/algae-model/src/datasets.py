import warnings
import random
import tqdm
import glob
import math
import bisect
from PIL import Image
from typing import List
from zipfile import ZipFile

import numpy as np
import torch


def veggie_mask(data):
    n = data.shape[0]
    if n == 4:
        ndvi = (data[3] - data[2]) / (data[3] + data[2])
    elif n == 12:
        ndvi = (data[7] - data[3]) / (data[7] + data[3])
    elif n == 224:
        ndvi = (data[50] - data[33]) / (data[50] + data[33])
    else:
        raise Exception(n)
    return ndvi


def water_mask(data):
    n = data.shape[0]
    if n == 4:
        ndwi = (data[1] - data[3]) / (data[1] + data[3])
    elif n == 12:
        ndwi = (data[2] - data[7]) / (data[2] + data[7])
    elif n == 224:
        ndwi = (data[22] - data[50]) / (data[22] + data[50])
    else:
        raise Exception(n)
    return ndwi


def augment0(data):
    if np.random.randint(0, 2) == 0:
        data = np.transpose(data, axes=(0, 2, 1))
    return data


def augment1(data):
    [n, w, h] = data.shape
    if np.random.randint(0, 5) < 1:
        data *= (1.0 + ((np.random.rand(n, 1, 1) - 0.5) / 50))
    if np.random.randint(0, 5) < 1:
        data *= (1.0 + ((np.random.rand(n, w, h) - 0.5) / 500))
    return data


class AlgaeUnlabeledDataset(torch.utils.data.Dataset):
    def __init__(self,
                 savezs,
                 ndwi_mask: bool = False,
                 augment: bool = False):
        self.yesno = []
        self.yesnos = []
        for savez in savezs:
            npz = np.load(savez)
            self.yesno.append(npz.get('yesno'))
            self.yesnos.append(self.yesno[-1].shape[-1])
        self.compound = list(zip(self.yesnos, self.yesno))
        self.ndwi_mask = ndwi_mask
        self.augment = augment
        warnings.filterwarnings('ignore')

    def __len__(self):
        n = 0
        for yesnos in self.yesnos:
            n += yesnos
        return n

    def __getitem__(self, idx):
        for (yesnos, yesno) in self.compound:
            if idx < yesnos:
                data = yesno[..., idx]
                break
            idx -= yesnos

        data = data.transpose((2, 0, 1))
        n = data.shape[-3]

        # Water Mask
        if self.ndwi_mask:
            ndwi = water_mask(data)
            data *= (ndwi > 0.0)

        # Augmentations
        if self.augment:
            data = augment0(data)

        ndvi = veggie_mask(data)
        ndwi = water_mask(data)
        not_algae = ((ndvi <= 0.0) + (ndwi <= 0.0)) > 0
        yes_algae = (ndvi > 0.3) * (ndvi <= 0.8) * (ndwi > 0.3)
        maybe_algae = (not_algae + yes_algae) < 1
        label = 0 * not_algae + 1 * yes_algae + 2 * maybe_algae

        # More augmentations
        if self.augment:
            data = augment1(data)

        return (data, label)


class AlgaeClassificationDataset(torch.utils.data.Dataset):
    def __init__(self,
                 savezs: List[str],
                 ndwi_mask: bool = False,
                 augment: bool = False):
        self.yes = []
        self.no = []
        self.yeas = []
        self.nays = []
        for savez in savezs:
            npz = np.load(savez)
            self.yes.append(npz.get('yes'))
            self.yeas.append(self.yes[-1].shape[-1])
            self.no.append(npz.get('no'))
            self.nays.append(self.no[-1].shape[-1])
        self.compound = list(
            zip(list(zip(self.yeas, self.nays)), list(zip(self.yes, self.no))))
        self.ndwi_mask = ndwi_mask
        self.augment = augment
        warnings.filterwarnings('ignore')

    def __len__(self):
        n = 0
        for yeas in self.yeas:
            n += yeas
        for nays in self.nays:
            n += nays
        return n

    def __getitem__(self, idx):
        for ((yeas, nays), (yes, no)) in self.compound:
            if idx < yeas:
                data, label = yes[..., idx], 1
                break
            idx -= yeas
            if idx < nays:
                data, label = no[..., idx], 0
                break
            idx -= nays

        data = data.transpose((2, 0, 1))
        n = data.shape[-3]

        # Water Mask
        if self.ndwi_mask:
            ndwi = water_mask(data)
            data *= (ndwi > 0.0)

        # Augmentations
        if self.augment:
            data = augment0(data)

        ndvi = veggie_mask(data)
        ndwi = water_mask(data)
        not_algae = ((ndvi <= 0.0) + (ndwi <= 0.0)) > 0
        yes_algae = (ndvi > 0.3) * (ndvi <= 0.8) * (ndwi > 0.3)
        maybe_algae = (not_algae + yes_algae) < 1
        if label == 1:
            label2 = 2 * not_algae + 1 * yes_algae + 2 * maybe_algae
        elif label == 0:
            label2 = 0 * not_algae + 2 * yes_algae + 2 * maybe_algae

        # More augmentations
        if self.augment:
            data = augment1(data)

        return (data, label, label2)


class SegmentationDataset(torch.utils.data.Dataset):
    def __init__(self, dataset_path: str,
                 is_aviris: bool = True,
                 is_validation: bool = False):

        self.is_aviris = is_aviris
        self.ziparray = []
        self.idxs = []
        self.samples = 0

        for filename in tqdm.tqdm(glob.glob(f'{dataset_path}/*.zip')):
            with ZipFile(filename, 'r') as z:
                if is_validation:
                    imgs = list(filter(lambda s: 'valid/' in s and 'img/' in s, z.namelist()))
                    labels = list(filter(lambda s: 'valid/' in s and 'labels/' in s, z.namelist()))
                elif not is_validation:
                    imgs = list(filter(lambda s: 'train/' in s and 'img/' in s, z.namelist()))
                    labels = list(filter(lambda s: 'train/' in s and 'labels/' in s, z.namelist()))
                imgs.sort()
                labels.sort()
                entry = {'filename': filename, 'imgs': imgs, 'labels': labels}
                if len(imgs) > 0 and len(imgs) == len(labels):
                    self.samples += len(imgs)
                    self.ziparray.append(entry)
                    self.idxs.append(self.samples)

    def __len__(self):
        return self.samples

    def __getitem__(self, idx):

        # Find the zip file containing the index
        entry = bisect.bisect(self.idxs, idx)
        if entry >= len(self.idxs):
            raise StopIteration()
        idx -= self.idxs[entry]
        entry = self.ziparray[entry]
        filename = entry.get('filename')

        img = entry.get('imgs')[idx]
        labels = entry.get('labels')[idx]
        with ZipFile(filename, 'r') as z:
            try:
                with z.open(img) as f:
                    if img.endswith('.png'):
                        img = np.copy(np.asarray(Image.open(f)))
                    elif img.endswith('.npy'):
                        img = np.load(f).transpose(2, 0, 1)
                    else:
                        return None
            except:
                return None
            try:
                with z.open(labels) as f:
                    if labels.endswith('.png'):
                        labels = np.copy(np.asarray(Image.open(f)))
                    elif labels.endswith('.npy'):
                        labels = np.load(f)
                    else:
                        return None
            except:
                return None

        img = img.astype(np.float32)
        return (img, labels)
