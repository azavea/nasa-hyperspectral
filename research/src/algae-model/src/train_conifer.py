#!/usr/bin/env python3

import argparse
import logging
import math
import random
import sys

import numpy as np
import rasterio as rio
import torch
import torch.nn.functional as F
import torchvision as tv
import tqdm
from rasterio.windows import Window
from torch import nn
from torch.optim.lr_scheduler import OneCycleLR
from torch.utils.data import DataLoader


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', required=False, type=int, default=6)
    parser.add_argument('--device', required=False, type=str, default='cuda', choices=['cuda', 'cpu'])
    parser.add_argument('--epochs', required=False, type=int, default=241)
    parser.add_argument('--imagery', required=True, type=str, nargs='+')
    parser.add_argument('--lr', required=False, type=float, default=1e-4)
    parser.add_argument('--masks', required=True, type=str, nargs='+')
    parser.add_argument('--preshrink', required=False, type=int, default=8)
    parser.add_argument('--pth-load', required=False, type=str)
    parser.add_argument('--pth-save', required=False, type=str, default='model.pth')
    parser.add_argument('--val-batch-size', required=False, type=int, default=8)
    parser.add_argument('--window-size', required=False, type=int, default=256)

    parser.add_argument('--freeze-bn', required=False, dest='freeze_bn', action='store_true')
    parser.set_defaults(freeze_bn=False)

    return parser


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
    # tmp[np.isnan(tmp)] = 0
    tmp[tmp.isnan()] = 0
    return tmp


def ndvi(batch):
    nir = batch[:, 46, :, :]
    red = batch[:, 27, :, :]
    tmp = (nir - red)/(nir + red)
    # tmp[np.isnan(tmp)] = 0
    tmp[tmp.isnan()] = 0
    return tmp


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


if __name__ == '__main__':

    args = cli_parser().parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)-15s %(message)s')
    log = logging.getLogger()

    pairs = list(zip(args.imagery, args.masks))
    n = args.window_size

    # from cloud import make_cloud_model
    # model = make_cloud_model(in_channels=[224], preshrink=args.preshrink)
    from tree import make_tree_model
    model = make_tree_model(preshrink=args.preshrink)
    if args.pth_load is not None:
        model.load_state_dict(torch.load(args.pth_load), strict=True)
    device = torch.device(args.device)
    model.to(device)

    log.info(f'epochs = {args.epochs}')
    log.info(f'lr = {args.lr}')
    log.info(f'window-size = {args.window_size}')
    log.info(f'batch-size = {args.batch_size}')
    log.info(f'val-batch-size = {args.val_batch_size}')

    log.info(f'freeze_bn = {args.freeze_bn}')
    log.info(f'preshrink = {args.preshrink}')

    log.info(f'pth-load = {args.pth_load}')
    log.info(f'pth-save = {args.pth_save}')
    log.info(f'imagery = {args.imagery}')
    log.info(f'masks = {args.masks}')

    weight = torch.tensor([13/21.0, 7/21.0, 1/21.0])
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    obj_bce = torch.nn.BCEWithLogitsLoss().to(device)
    obj_ce = torch.nn.CrossEntropyLoss(weight=weight, ignore_index=0xff).to(device)

    best_train_loss = math.inf
    best_val_loss = math.inf

    for i in range(args.epochs):
        if args.freeze_bn and i == 1:
            log.info('BN layers frozen')
            freeze_bn(model)

        for mode in ['train', 'val']:
            losses = []

            for (imagery_tiff, mask_tiff) in pairs:
                with rio.open(imagery_tiff, 'r') as imagery_ds, rio.open(mask_tiff, 'r') as mask_ds:
                    width = imagery_ds.width
                    height = imagery_ds.height
                    assert(mask_ds.width == width)
                    assert(mask_ds.height == height)
                    assert(imagery_ds.count == 224)
                    assert(mask_ds.count == 1)

                    endwidth = width if width % n == 0 else width-n
                    endheight = height if height % n == 0 else height-n
                    windows = [(x, y) for x in range(0, endwidth, n) for y in range(0, endheight, n)]

                    if mode == 'train':
                        windows = [(x, y) for (x, y) in windows if x % (4*n) != n]
                        windows = list(chunks(windows, args.batch_size))
                        model.train()
                    elif mode == 'val':
                        windows = [(x, y) for (x, y) in windows if x % (4*n) == n]
                        windows = list(chunks(windows, args.val_batch_size))
                        model.eval()

                    for batch in tqdm.tqdm(windows):
                            chips = [imagery_ds.read(window=Window(x, y, n, n)) for (x, y) in batch]
                            chips = np.stack(chips, axis=0).astype(np.float32)
                            chips = torch.from_numpy(chips).to(device=device)

                            masks = [mask_ds.read(window=Window(x, y, n, n)) for (x, y) in batch]
                            masks = np.stack(masks, axis=0)
                            masks = torch.from_numpy(masks).long().to(device=device)
                            (b, _, x, y) = masks.shape
                            masks = masks.reshape(b, x, y)

                            bsi_tmp = bsi(chips)
                            ndvi_tmp = ndvi(chips)
                            red_conifer = ((masks == 1) * (bsi_tmp < 1.0/6) * (bsi_tmp > -1.0/6) * (ndvi_tmp > 1.0/3) * (ndvi_tmp < 2.0/3))
                            green_conifer = ((masks == 1) * (bsi_tmp < -1.0/6) * (ndvi_tmp > 2.0/3))
                            unknown  = ((masks == 1) * ~red_conifer * ~green_conifer)

                            masks[masks == 0] = 2
                            masks[red_conifer] = 0
                            masks[green_conifer] = 1
                            masks[unknown] = 0xff

                            if mode == 'train':
                                out = model(chips)
                                loss = obj_ce(out, masks)
                                # + \
                                #     obj_bce(out[:,1,:,:], green_conifer.float()) + \
                                #     obj_bce(out[:,0,:,:], red_conifer.float())
                                if not math.isnan(loss.item()):
                                    losses.append(loss.item())
                                    loss.backward()
                                    opt.step()
                                    opt.zero_grad()
                            elif mode == 'val':
                                with torch.no_grad():
                                    out = model(chips)
                                    loss = obj_ce(out, masks)
                                    if not math.isnan(loss.item()):
                                        losses.append(loss.item())

            avg_loss = np.mean(losses)
            log.info(f'epoch {i}: avg {mode} loss = {avg_loss}')
            if mode == 'val' and avg_loss < best_val_loss:
                log.info(f'Saving checkpoint to /tmp/best-checkpoint.pth')
                torch.save(model.state_dict(), '/tmp/best-checkpoint.pth')
                best_val_loss = avg_loss
            if mode == 'train' and avg_loss < best_train_loss:
                best_train_loss = avg_loss

        log.info(f'Saving checkpoint to /tmp/checkpoint.pth')
        torch.save(model.state_dict(), '/tmp/checkpoint.pth')

    if args.pth_save is not None:
        log.info(f'Saving model to {args.pth_save}')
        torch.save(model.state_dict(), args.pth_save)
