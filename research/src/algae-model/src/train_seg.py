#!/usr/bin/env python3

import argparse
import logging
import random
import sys
import math

import numpy as np
import torch
from torch import nn
import torchvision as tv
import tqdm
from torch.optim.lr_scheduler import OneCycleLR
from torch.utils.data import DataLoader
import torch.nn.functional as F

from datasets import SegmentationDataset


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aviris-l1-path', required=False, type=str, default=None)
    parser.add_argument('--batch-size', required=False, type=int, default=6)
    parser.add_argument('--epochs', required=False, type=int, default=33)
    parser.add_argument('--lr', required=False, type=float, default=1e-4)
    parser.add_argument('--num-workers', required=False, type=int, default=4)
    parser.add_argument('--preshrink', required=False, type=int, default=8)
    parser.add_argument('--pth-load', required=False, type=str)
    parser.add_argument('--pth-save', required=False, type=str, default='model.pth')
    parser.add_argument('--sentinel-l1c-path', required=False, type=str, default=None)
    parser.add_argument('--sentinel-l2a-path', required=False, type=str, default=None)
    parser.add_argument('--wanted-chips', required=False, type=float, default=0.75)

    parser.add_argument('--freeze-bn', required=False, dest='freeze_bn', action='store_true')
    parser.set_defaults(freeze_bn=False)

    parser.add_argument('--tree', required=False, dest='tree', action='store_true')
    parser.set_defaults(tree=False)

    return parser


def worker_init_fn(x):
    np.random.seed(42 + x)
    random.seed(42 + x)


def collate_fn(batch):
    batch = list(filter(lambda x: x is not None, batch))
    return torch.utils.data.dataloader.default_collate(batch)


def freeze(m: nn.Module) -> nn.Module:
    for p in m.parameters():
        p.requires_grad = False


def unfreeze(m: nn.Module) -> nn.Module:
    for p in m.parameters():
        p.requires_grad = True


def freeze_bn(m):
    for (name, child) in m.named_children():
        if isinstance(child, torch.nn.BatchNorm2d):
            for param in child.parameters():
                param.requires_grad = False
            child.eval()
        else:
            freeze_bn(child)


def unfreeze_bn(m):
    for (name, child) in m.named_children():
        if isinstance(child, torch.nn.BatchNorm2d):
            for param in child.parameters():
                param.requires_grad = True
            child.train()
        else:
            unfreeze_bn(child)


def bsi(batch):
    swir2 = batch[:, 194, :, :]
    red = batch[:, 27, :, :]
    blue = batch[:, 9, :, :]
    nir = batch[:, 46, :, :]
    tmp = (swir2 + red - nir - blue)/(swir2 + red + nir + blue)
    tmp[tmp.isnan()] = 0
    return tmp


def ndvi(batch):
    nir = batch[:, 46, :, :]
    red = batch[:, 27, :, :]
    tmp = (nir - red)/(nir + red)
    tmp[tmp.isnan()] = 0
    return tmp


dataloader_cfg = {
    'batch_size': None,
    'num_workers': None,
    'pin_memory': True,
    'worker_init_fn': worker_init_fn,
    'collate_fn': collate_fn
}


if __name__ == '__main__':

    args = cli_parser().parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)-15s %(message)s')
    log = logging.getLogger()

    dataloader_cfg['batch_size'] = args.batch_size
    dataloader_cfg['num_workers'] = args.num_workers

    train_dls = []
    valid_dls = []
    if args.sentinel_l1c_path is not None:
        ds = SegmentationDataset(
            args.sentinel_l1c_path,
            is_aviris=False, is_validation=False)
        dl = DataLoader(ds, **dataloader_cfg)
        train_dls.append({'dl': dl, 'shadows': False})
        ds = SegmentationDataset(
            args.sentinel_l1c_path,
            is_aviris=False, is_validation=True)
        dl = DataLoader(ds, **dataloader_cfg)
        valid_dls.append({'dl': dl, 'shadows': False})
    if args.sentinel_l2a_path is not None:
        ds = SegmentationDataset(
            args.sentinel_l2a_path,
            is_aviris=False, is_validation=False)
        dl = DataLoader(ds, **dataloader_cfg)
        train_dls.append({'dl': dl, 'shadows': False})
        ds = SegmentationDataset(
            args.sentinel_l2a_path,
            is_aviris=False, is_validation=True)
        dl = DataLoader(ds, **dataloader_cfg)
        valid_dls.append({'dl': dl, 'shadows': False})
    if args.aviris_l1_path is not None:
        ds = SegmentationDataset(
            args.aviris_l1_path,
            is_aviris=True, is_validation=False)
        dl = DataLoader(ds, **dataloader_cfg)
        train_dls.append({'dl': dl, 'shadows': True})
        ds = SegmentationDataset(
            args.aviris_l1_path,
            is_aviris=True, is_validation=True)
        dl = DataLoader(ds, **dataloader_cfg)
        valid_dls.append({'dl': dl, 'shadows': True})

    assert len(train_dls) == len(valid_dls)

    from cloud import make_cloud_model
    # model = make_cloud_model(in_channels=[13, 12, 224])
    model = make_cloud_model(in_channels=[224], preshrink=args.preshrink)
    if args.pth_load is not None:
        model.load_state_dict(torch.load(args.pth_load), strict=True)
    device = torch.device('cuda')
    log.info(f'freeze_bn = {args.freeze_bn}')
    log.info(f'tree = {args.tree}')
    log.info(f'epochs = {args.epochs}')
    log.info(f'batch-size = {args.batch_size}')
    log.info(f'wanted-size = {args.wanted_chips}')
    log.info(f'num-workers = {args.num_workers}')
    log.info(f'pth-load = {args.pth_load}')
    log.info(f'pth-save = {args.pth_save}')

    model.to(device)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    obj_bce = torch.nn.BCEWithLogitsLoss().to(device)
    obj_ce = torch.nn.CrossEntropyLoss(ignore_index=0xff).to(device)

    wanted_pixels = 512 * 512 * args.wanted_chips

    best_valid_loss = 1e6
    for i in range(args.epochs):

        choice_index = i % len(train_dls)
        losses = []
        fills = []

        for mode in ['train', 'valid']:
            if mode == 'train':
                choice = train_dls[choice_index]
                model.train()
            elif mode == 'valid':
                choice = valid_dls[choice_index]
                model.eval()

            dl = choice.get('dl')
            lendl = len(dl)
            shadows = choice.get('shadows')
            if args.freeze_bn and i > 0:
                freeze_bn(model)

            desc = 'Training' if mode == 'train' else 'Validation'
            for (j, batch) in tqdm.tqdm(enumerate(dl), total=len(dl), desc=desc):
                if args.tree:
                    soil = bsi(batch[0])
                    vegitation = ndvi(batch[0])
                    red_stage = (batch[1] == 1) * (soil < 0.0) * (vegitation > 0.0)
                    green_stage = (batch[1] == 0) * (soil < 0.0) * (vegitation > 0.0)
                    other = (batch[1] > 1) + (soil > 0.3) + (vegitation < -0.3)
                    mask = (red_stage + green_stage + other).to(device)
                    fill = mask.sum().item() / wanted_pixels
                    fills.append(fill)
                    while mask.sum().item() > wanted_pixels:
                        p = wanted_pixels / mask.sum().item()
                        mask = mask * (torch.rand(mask.shape).to(device) < p)
                    if mask.sum().item() == 0:
                        continue
                    pixels_of_interest = torch.masked_select(
                        batch[0].to(device),
                        mask.unsqueeze(dim=1))
                    c = batch[0].shape[1]
                    n = int(math.sqrt(len(pixels_of_interest) / c))
                    pixels_of_interest = pixels_of_interest[:c*n*n].reshape(1, c, n, n)

                    labels_of_interest = torch.masked_select((0*red_stage + 1*green_stage + 2*other).to(device), mask)
                    labels_of_interest = labels_of_interest.reshape(-1)[:n*n].reshape(1, n, n)

                    out = model(pixels_of_interest)
                    loss = obj_ce(out[0], labels_of_interest)
                else:
                    out = model(batch[0].to(device))
                    if shadows:
                        cloud_gt = (batch[1] == 2).type(out[0].type())
                        cloud_shadow_gt = (batch[1] == 3).type(out[0].type())
                        cloud_pred = out[0][:, 1, :, :] - out[0][:, 0, :, :]
                        cloud_shadow_pred = out[0][:, 2, :, :] - out[0][:, 0, :, :]
                        loss1 = obj_bce(cloud_pred, cloud_gt.to(device))
                        loss2 = obj_bce(cloud_shadow_pred, cloud_shadow_gt.to(device))
                        loss = loss1 + loss2
                    else:
                        cloud_gt = (batch[1] == 1).type(out[0].type())
                        cloud_pred = out[0][:, 1, :, :] - out[0][:, 0, :, :]
                        loss = obj_bce(cloud_pred, cloud_gt.to(device))

                if not math.isnan(loss.item()):
                    losses.append(loss.item())
                    loss.backward()
                    opt.step()
                opt.zero_grad()

            avg_loss = np.mean(losses)
            avg_fill = np.mean(fills)
            log.info(f'epoch={i:<3d} avg-fill={avg_fill:1.2f} avg-{mode}-loss={avg_loss:1.5f}')

            if mode == 'valid' and avg_loss < best_valid_loss:
                log.info(f'Saving checkpoint to /tmp/best-checkpoint.pth')
                torch.save(model.state_dict(), '/tmp/best-checkpoint.pth')
                best_valid_loss = avg_loss

        log.info(f'Saving checkpoint to /tmp/checkpoint.pth')
        torch.save(model.state_dict(), '/tmp/checkpoint.pth')

    if args.pth_save is not None:
        log.info(f'Saving model to {args.pth_save}')
        torch.save(model.state_dict(), args.pth_save)
