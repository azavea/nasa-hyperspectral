#!/usr/bin/env python3

import argparse
import csv
import logging
import math
import sys

import numpy as np
import torch
import torch.hub
import torch.nn.functional as F
import torchvision as tv
import tqdm
from torch.utils.data import DataLoader
from torchvision.io import VideoReader
from torchvision.transforms.functional import F_t
from torch.optim.lr_scheduler import OneCycleLR

from datasets import (AlgaeClassificationDataset, AlgaeUnlabeledDataset)

BACKBONES = [
    'vgg16', 'densenet161', 'shufflenet_v2_x1_0', 'mobilenet_v2',
    'mobilenet_v3_large', 'mobilenet_v3_small', 'resnet18', 'resnet34',
    'resnet50', 'resnet101', 'resnet152', 'efficientnet_b0', 'efficientnet_b1',
    'efficientnet_b2', 'efficientnet_b3', 'efficientnet_b4', 'efficientnet_b5',
    'efficientnet_b6', 'efficientnet_b7', 'fpn_resnet18', 'fpn_resnet34',
    'fpn_resnet50', 'fpn_resnet101', 'fpn_resnet152', 'fpn_efficientnet_b0',
    'fpn_efficientnet_b1', 'fpn_efficientnet_b2', 'fpn_efficientnet_b3',
    'fpn_efficientnet_b4', 'fpn_efficientnet_b5', 'fpn_efficientnet_b6',
    'fpn_efficientnet_b7'
]

AVIRIS_TO_SENTINEL2 = [10, 15, 22, 33, 37, 41, 45, 50, 62, 107, 132, 193]

SENTINEL2_TO_4B = [0, 2, 3, 8]


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backbone', required=True, type=str, choices=BACKBONES)
    parser.add_argument('--batch-size', required=False, type=int, default=128)
    parser.add_argument('--classification-savezs', required=True, type=str, nargs='+')
    parser.add_argument('--epochs1', required=False, type=int, default=33)
    parser.add_argument('--epochs2', required=False, type=int, default=2003)
    parser.add_argument('--epochs3', required=False, type=int, default=33)
    parser.add_argument('--lr1', required=False, type=float, default=1e-4)
    parser.add_argument('--lr2', required=False, type=float, default=1e-5)
    parser.add_argument('--num-workers', required=False, type=int, default=0)
    parser.add_argument('--prescale', required=False, type=int, default=1)
    parser.add_argument('--pth-cheaplab-donor', required=False, type=str, default=None)
    parser.add_argument('--pth-load', required=False, type=str, default=None)
    parser.add_argument('--pth-save', required=False, type=str, default=None)
    parser.add_argument('--unlabeled-epoch-size', required=False, type=int, default=1e6)
    parser.add_argument('--unlabeled-savezs', required=False, default=[], type=str, nargs='+')
    parser.add_argument('--w0', required=False, type=float, default=1.0)
    parser.add_argument('--w1', required=False, type=float, default=0.0)
    parser.add_argument('--w2', required=False, type=float, default=0.5)
    parser.add_argument('--w3', required=False, type=float, default=0.5)

    parser.add_argument('--classifier-from-github', required=False, dest='classifier_from_github', action='store_true')
    parser.set_defaults(classifier_from_github=False)

    parser.add_argument('--ndwi-mask', required=False, dest='ndwi_mask', action='store_true')
    parser.set_defaults(ndwi_mask=False)

    parser.add_argument('--no-schedule', dest='schedule', action='store_false')
    parser.set_defaults(schedule=True)

    parser.add_argument('--no-pretrained', dest='pretrained', action='store_false')
    parser.set_defaults(pretrained=True)

    return parser


def worker_init_fn(x):
    np.random.seed(42 + x)


dataloader1_cfg = {
    'batch_size': None,
    'num_workers': None,
    'shuffle': True,
    'worker_init_fn': worker_init_fn
}

dataloader2_cfg = {
    'batch_size': None,
    'num_workers': None,
    'shuffle': True,
    'worker_init_fn': worker_init_fn
}


# https://discuss.pytorch.org/t/how-to-freeze-bn-layers-while-training-the-rest-of-network-mean-and-var-wont-freeze/89736/9
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


def freeze(m):
    for p in m.parameters():
        p.requires_grad = False


def unfreeze(m):
    for p in m.parameters():
        p.requires_grad = True


def greens_function(x, x0, eps=1e-3):
    out = -((x - x0) * (x - x0)) / (eps * eps)
    out = torch.exp(out)
    return out


def entropy_function(x):
    s = torch.sigmoid(x)
    pno_narrow = torch.mean(greens_function(s, 0.25, 1.0 / 16))
    pno_wide = torch.mean(greens_function(s, 0.25, 1.0 / 8))
    pyes_narrow = torch.mean(greens_function(s, 0.75, 1.0 / 16))
    pyes_wide = torch.mean(greens_function(s, 0.75, 1.0 / 8))
    return ((pyes_narrow * torch.log(pyes_wide)) +
            (pno_narrow * torch.log(pno_wide)))


if __name__ == '__main__':

    args = cli_parser().parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)-15s %(message)s')
    log = logging.getLogger()

    dataloader1_cfg['batch_size'] = args.batch_size
    dataloader1_cfg['num_workers'] = args.num_workers

    dataloader2_cfg['batch_size'] = args.batch_size
    dataloader2_cfg['num_workers'] = args.num_workers

    device = torch.device('cuda')
    if args.classifier_from_github:
        model = torch.hub.load(
            'jamesmcclain/algae-classifier:df888fa9c383c976faecada5bef7844afe53cba7',
            'make_algae_model',
            in_channels=[4, 12, 224],
            prescale=args.prescale,
            backbone_str=args.backbone,
            pretrained=args.pretrained)
    else:
        from algae import make_algae_model
        model = make_algae_model(
            in_channels=[4, 12, 224],
            prescale=args.prescale,
            backbone_str=args.backbone,
            pretrained=args.pretrained)

    if args.pth_cheaplab_donor:
        state = torch.load(args.pth_cheaplab_donor)
        for key in list(state.keys()):
            if 'cheaplab' not in key:
                state.pop(key)
        model.load_state_dict(state, strict=False)

    for cheaplab in model.cheaplab.values():
        cheaplab.to(device)
    model.to(device)

    opt1a = torch.optim.AdamW(model.parameters(), lr=args.lr1)
    opt1b = torch.optim.AdamW(model.parameters(), lr=args.lr2)
    if args.epochs2 > 0:
        sched1 = OneCycleLR(opt1b, max_lr=args.lr2, total_steps=args.epochs2)

    opt2a = torch.optim.SGD(model.parameters(), lr=args.lr1, momentum=0.9)
    opt2b = torch.optim.SGD(model.parameters(), lr=args.lr2, momentum=0.9)
    if args.epochs2 > 0:
        sched2 = OneCycleLR(opt2b, max_lr=args.lr2, total_steps=args.epochs2)

    obj1 = torch.nn.BCEWithLogitsLoss().to(device)
    obj2 = torch.nn.CrossEntropyLoss(ignore_index=2).to(device)

    log.info(f'backbone={args.backbone}')
    log.info(f'batch-size={args.batch_size}')
    log.info(f'classification-savezs={args.classification_savezs}')
    log.info(f'epochs1={args.epochs1}')
    log.info(f'epochs2={args.epochs2}')
    log.info(f'epochs3={args.epochs3}')
    log.info(f'ndwi-mask={args.ndwi_mask}')
    log.info(f'num-workers={args.num_workers}')
    log.info(f'prescale={args.prescale}')
    log.info(f'pretrained={args.pretrained}')
    log.info(f'pth-load={args.pth_load}')
    log.info(f'pth-save={args.pth_save}')
    log.info(f'schedule={args.schedule}')
    log.info(f'unlabeled-epoch-size={args.unlabeled_epoch_size}')
    log.info(f'unlabeled-savezs={args.unlabeled_savezs}')

    log.info(f'parameter lr1: {args.lr1}')
    log.info(f'parameter lr2: {args.lr2}')
    log.info(f'parameter w0:   {args.w0}')
    log.info(f'parameter w1:   {args.w1}')
    log.info(f'parameter w2:   {args.w2}')
    log.info(f'parameter w3:   {args.w3}')

    classification_dls = []
    classification_batches = 0
    for savez in args.classification_savezs:
        log.info(f'loading {savez}')
        ad1 = AlgaeClassificationDataset(savezs=[savez],
                                         ndwi_mask=args.ndwi_mask,
                                         augment=True)
        dl1 = DataLoader(ad1, **dataloader1_cfg)
        classification_batches += len(dl1)
        classification_dls.append(dl1)

    unlabeled_dls = []
    for savez in args.unlabeled_savezs:
        log.info(f'loading {savez}')
        ad2 = AlgaeUnlabeledDataset(savezs=[savez],
                                    ndwi_mask=args.ndwi_mask,
                                    augment=True)
        dl2 = DataLoader(ad2, **dataloader2_cfg)
        unlabeled_dls.append(dl2)

    if args.pth_load is None:
        log.info('Training everything')
        unfreeze(model)
        freeze_bn(model)
        for epoch in range(0, args.epochs1):
            constraints1 = []
            entropies1 = []
            entropies2 = []
            losses1 = []
            losses2 = []

            for dl in classification_dls:
                for (i, batch) in enumerate(dl):
                    imgs = batch[0].float()
                    if i == 0:
                        freeze_bn(model.cheaplab)
                        unfreeze_bn(model.cheaplab[str(imgs.shape[1])])
                    while imgs is not None:
                        out = model(imgs.to(device))
                        constraint = obj1(out.get('class').squeeze(), batch[1].float().to(device))
                        if 'seg' in out.keys():
                            constraint += obj2(out.get('seg'), batch[2].to(device))
                        if args.w1 != 0.0:
                            entropy = entropy_function(out.get('class').squeeze())
                            loss = args.w0 * constraint + args.w1 * entropy
                            entropies1.append(entropy.item())
                        else:
                            loss = args.w0 * constraint
                        losses1.append(loss.item())
                        constraints1.append(constraint.item())
                        loss.backward()
                        opt1a.step()
                        opt1a.zero_grad()
                        if imgs.shape[1] == 224:
                            imgs = imgs[:, AVIRIS_TO_SENTINEL2, :, :]
                        elif imgs.shape[1] == 12:
                            imgs = imgs[:, SENTINEL2_TO_4B, :, :]
                        else:
                            imgs = None

            for dl in unlabeled_dls:
                for (i, batch) in enumerate(dl):
                    if i > args.unlabeled_epoch_size:
                        break
                    imgs = batch[0].float()
                    if i == 0:
                        freeze_bn(model.cheaplab)
                        unfreeze_bn(model.cheaplab[str(imgs.shape[1])])
                    while imgs is not None:
                        out = model(imgs.to(device))
                        entropy = entropy_function(out.get('class').squeeze())
                        entropies2.append(entropy.item())
                        loss = args.w3 * entropy
                        losses2.append(loss.item())
                        loss.backward()
                        opt2a.step()
                        opt2a.zero_grad()
                        if imgs.shape[1] == 224:
                            imgs = imgs[:, AVIRIS_TO_SENTINEL2, :, :]
                        elif imgs.shape[1] == 12:
                            imgs = imgs[:, SENTINEL2_TO_4B, :, :]
                        else:
                            imgs = None

            mean_constraint1 = np.mean(constraints1)
            mean_entropy1 = np.mean(entropies1)
            mean_entropy2 = np.mean(entropies2)
            mean_loss1 = np.mean(losses1)
            mean_loss2 = np.mean(losses2)

            log.info(f'epoch={epoch:<3d} loss={mean_loss1:+1.5f} entropy={mean_entropy1:+1.5f} constraint={mean_constraint1:+1.5f}')
            log.info(f'          loss={mean_loss2:+1.5f} entropy={mean_entropy2:+1.5f}')

        log.info('Training input and output layers')
        freeze(model)
        unfreeze(model.cheaplab)
        unfreeze(model.first)
        unfreeze(model.last)
        freeze_bn(model)
        for epoch in range(0, args.epochs1):
            constraints1 = []
            entropies1 = []
            losses1 = []

            for dl in classification_dls:
                for (i, batch) in enumerate(dl):
                    imgs = batch[0].float()
                    if i == 0:
                        freeze_bn(model.cheaplab)
                        unfreeze_bn(model.cheaplab[str(imgs.shape[1])])
                    while imgs is not None:
                        out = model(imgs.to(device)).get('class').squeeze()
                        constraint = obj1(out, batch[1].float().to(device))
                        if args.w1 != 0.0:
                            entropy = entropy_function(out)
                            loss = args.w0 * constraint + args.w1 * entropy
                            entropies1.append(entropy.item())
                        else:
                            loss = args.w0 * constraint
                        losses1.append(loss.item())
                        constraints1.append(constraint.item())
                        loss.backward()
                        opt1a.step()
                        opt1a.zero_grad()
                        if imgs.shape[1] == 224:
                            imgs = imgs[:, AVIRIS_TO_SENTINEL2, :, :]
                        elif imgs.shape[1] == 12:
                            imgs = imgs[:, SENTINEL2_TO_4B, :, :]
                        else:
                            imgs = None

            mean_constraint1 = np.mean(constraints1)
            mean_entropy1 = np.mean(entropies1)
            mean_loss1 = np.mean(losses1)

            log.info(f'epoch={epoch:<3d} loss={mean_loss1:+1.5f} entropy={mean_entropy1:+1.5f} constraint={mean_constraint1:+1.5f}')
    else:
        log.info(f'Loading model from {args.pth_load}')
        model.load_state_dict(torch.load(args.pth_load))
        for cheaplab in model.cheaplab.values():
            cheaplab.to(device)
        model.to(device)

    log.info('Training everything')
    unfreeze(model.backbone)
    freeze_bn(model)
    for epoch in range(0, args.epochs2):
        constraints1 = []
        constraints2 = []
        entropies1 = []
        entropies2 = []
        losses1 = []
        losses2 = []

        for dl in classification_dls:
            for (i, batch) in enumerate(dl):
                imgs = batch[0].float()
                if i == 0:
                    freeze_bn(model.cheaplab)
                    unfreeze_bn(model.cheaplab[str(imgs.shape[1])])
                while imgs is not None:
                    out = model(imgs.to(device))
                    constraint = obj1(out.get('class').squeeze(), batch[1].float().to(device))
                    if 'seg' in out.keys():
                        constraint += obj2(out.get('seg'), batch[2].to(device))
                    if args.w1 != 0.0:
                        entropy = entropy_function(out)
                        loss = args.w0 * constraint + args.w1 * entropy
                        entropies1.append(entropy.item())
                    else:
                        loss = args.w0 * constraint
                    losses1.append(loss.item())
                    constraints1.append(constraint.item())
                    loss.backward()
                    opt1b.step()
                    opt1b.zero_grad()
                    if imgs.shape[1] == 224:
                        imgs = imgs[:, AVIRIS_TO_SENTINEL2, :, :]
                    elif imgs.shape[1] == 12:
                        imgs = imgs[:, SENTINEL2_TO_4B, :, :]
                    else:
                        imgs = None

        for dl in unlabeled_dls:
            for (i, batch) in enumerate(dl):
                if i > args.unlabeled_epoch_size:
                    break
                imgs = batch[0].float()
                if i == 0:
                    freeze_bn(model.cheaplab)
                    unfreeze_bn(model.cheaplab[str(imgs.shape[1])])
                while imgs is not None:
                    out = model(imgs.to(device))
                    entropy = entropy_function(out.get('class').squeeze())
                    entropies2.append(entropy.item())
                    if 'seg' in out.keys():
                        constraint = obj2(out.get('seg'), batch[1].to(device))
                        loss = (i/args.unlabeled_epoch_size) * args.w2 * constraint + args.w3 * entropy
                        constraints2.append(constraint.item())
                    else:
                        loss = args.w3 * entropy
                    losses2.append(loss.item())
                    loss.backward()
                    opt2b.step()
                    opt2b.zero_grad()
                    if imgs.shape[1] == 224:
                        imgs = imgs[:, AVIRIS_TO_SENTINEL2, :, :]
                    elif imgs.shape[1] == 12:
                        imgs = imgs[:, SENTINEL2_TO_4B, :, :]
                    else:
                        imgs = None

        if args.schedule:
            sched1.step()
            sched2.step()
        if epoch % 107 == 0:
            log.info(f'Saving checkpoint to /tmp/checkpoint.pth')
            torch.save(model.state_dict(), '/tmp/checkpoint.pth')

        mean_constraint1 = np.mean(constraints1)
        mean_constraint2 = np.mean(constraints2)
        mean_entropy1 = np.mean(entropies1)
        mean_entropy2 = np.mean(entropies2)
        mean_loss1 = np.mean(losses1)
        mean_loss2 = np.mean(losses2)

        log.info(f'epoch={epoch:<3d} loss={mean_loss1:+1.5f} entropy={mean_entropy1:+1.5f} constraint={mean_constraint1:+1.5f}')
        log.info(f'          loss={mean_loss2:+1.5f} entropy={mean_entropy2:+1.5f} constraint={mean_constraint2:+1.5f}')

    log.info(f'Saving checkpoint to /tmp/checkpoint.pth')
    torch.save(model.state_dict(), '/tmp/checkpoint.pth')

    log.info('Reconciling CheapLabs')
    freeze(model)
    unfreeze(model.cheaplab['224'])
    unfreeze(model.cheaplab['4'])
    freeze_bn(model)
    for epoch in range(0, args.epochs3):
        losses1 = []

        for dl in unlabeled_dls:
            for (i, batch) in enumerate(dl):
                if i > args.unlabeled_epoch_size or batch[0].shape[1] < 224:
                    break
                imgs = batch[0].float()
                if i == 0:
                    freeze_bn(model.cheaplab)
                    unfreeze_bn(model.cheaplab[str(imgs.shape[1])])
                outs = []
                outs.append(model(imgs.to(device)).get('class'))
                if imgs.shape[1] == 224:
                    imgs = imgs[:, AVIRIS_TO_SENTINEL2, :, :]
                    outs.append(model(imgs.to(device)).get('class'))
                if imgs.shape[1] == 12:
                    imgs = imgs[:, SENTINEL2_TO_4B, :, :]
                    outs.append(model(imgs.to(device)).get('class'))

                if len(outs[0].shape) == 2:
                    label = torch.stack([o for o in outs], axis=2)
                    label = torch.round(torch.sigmoid(torch.mean(label, axis=2))).float()
                else:
                    label = torch.stack([o for o in outs], axis=4)
                    label = torch.round(torch.sigmoid(torch.mean(label, axis=4))).float()
                loss = obj1(outs[0], label) + obj1(outs[2], label)
                losses1.append(loss.item())
                loss.backward()
                opt1a.step()
                opt1a.zero_grad()

        mean_loss1 = np.mean(losses1)

        log.info(f'epoch={epoch:<3d} loss={mean_loss1:+1.5f}')

    if args.pth_save is not None:
        log.info(f'Saving model to {args.pth_save}')
        torch.save(model.state_dict(), args.pth_save)

    model.eval()
    tp = 0.0
    tn = 0.0
    fp = 0.0
    fn = 0.0
    with torch.no_grad():
        for (i, batch) in enumerate(dl1):
            pred = torch.sigmoid(model(batch[0].float().to(device)).get('class')).squeeze()
            pred = (pred > 0.5).detach().cpu().numpy().astype(np.uint8)
            gt = batch[1].detach().cpu().numpy().astype(np.uint8)
            tp += np.sum((pred == 1) * (gt == 1))
            tn += np.sum((pred == 0) * (gt == 0))
            fp += np.sum((pred == 1) * (gt == 0))
            fn += np.sum((pred == 0) * (gt == 1))
    total = tp + tn + fp + fn
    log.info(f'tpr={tp/(tp+fn)} tnr={tn/(tn+fp)}')
