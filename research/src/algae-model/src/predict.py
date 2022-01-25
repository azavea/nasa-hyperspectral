#!/usr/bin/env python3

import argparse
import copy
import logging
import sys
import warnings

import numpy as np
import rasterio as rio
import torch
import torch.hub
import tqdm
from rasterio.windows import Window

BACKBONES = [
    'vgg16', 'densenet161', 'shufflenet_v2_x1_0', 'mobilenet_v2',
    'mobilenet_v3_large', 'mobilenet_v3_small', 'resnet18', 'resnet34',
    'resnet50', 'resnet101', 'resnet152', 'efficientnet_b0', 'efficientnet_b1',
    'efficientnet_b2', 'efficientnet_b3', 'efficientnet_b4', 'efficientnet_b5',
    'efficientnet_b6', 'efficientnet_b7', 'fpn_resnet18', 'fpn_resnet34',
    'fpn_resnet50'
]


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backbone', required=True, type=str, choices=BACKBONES)
    parser.add_argument('--chunksize', required=False, type=int, default=256)
    parser.add_argument('--device', required=False, type=str, default='cuda', choices=['cuda', 'cpu'])
    parser.add_argument('--infile', required=True, type=str, nargs='+')
    parser.add_argument('--outfile', required=False, default=None, type=str, nargs='+')
    parser.add_argument('--prescale', required=False, type=int, default=1)
    parser.add_argument('--pth-load', required=True, type=str)
    parser.add_argument('--stride', required=False, type=int, default=13)
    parser.add_argument('--window-size', required=False, type=int, default=32)

    parser.add_argument('--classifier-from-github', required=False, dest='classifier_from_github', action='store_true')
    parser.set_defaults(classifier_from_github=False)

    parser.add_argument('--ndwi-mask', required=False, dest='ndwi_mask', action='store_true')
    parser.set_defaults(ndwi_mask=False)

    return parser


if __name__ == '__main__':

    warnings.filterwarnings('ignore')

    args = cli_parser().parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)-15s %(message)s')
    log = logging.getLogger()

    n = args.window_size

    device = torch.device(args.device)
    if args.classifier_from_github:
        model = torch.hub.load('jamesmcclain/algae-classifier:df888fa9c383c976faecada5bef7844afe53cba7',
                               'make_algae_model',
                               in_channels=[4, 12, 224],
                               prescale=args.prescale,
                               backbone_str=args.backbone,
                               pretrained=False)
    else:
        from algae import make_algae_model
        model = make_algae_model(
            in_channels=[4, 12, 224],
            prescale=args.prescale,
            backbone_str=args.backbone,
            pretrained=False)
    model.load_state_dict(torch.load(args.pth_load))
    model.to(device)
    model.eval()

    if args.outfile is None:
        model_name = args.pth_load.split('/')[-1].split('.')[0]
        def transmute(filename):
            filename = filename.split('/')[-1]
            filename = f"./predict-{model_name}-{filename}"
            if not filename.endswith('.tiff'):
                filename = filename.replace('.tif', '.tiff')
            return filename
        args.outfile = [transmute(f) for f in args.infile]

    for (infile, outfile) in zip(args.infile, args.outfile):
        log.info(outfile)
        with rio.open(infile, 'r') as infile_ds, torch.no_grad():
            out_raw_profile = copy.deepcopy(infile_ds.profile)
            out_raw_profile.update({
                'compress': 'lzw',
                'dtype': np.float32,
                'count': 1,
                'bigtiff': 'yes',
                'sparse_ok': 'yes',
                'tiled': 'yes',
            })
            width = infile_ds.width
            height = infile_ds.height
            bandcount = infile_ds.count
            ar_out = torch.zeros((1, height, width), dtype=torch.float32).to(device)
            pixel_hits = torch.zeros((1, height, width), dtype=torch.uint8).to(device)

            if bandcount == 224:
                indexes = list(range(1, 224 + 1))
            elif bandcount in {12, 13}:
                indexes = list(range(1, 12 + 1))
                # NOTE: 13 bands does not indicate L1C support, this is
                # for Franklin COGs that have an extra band.
                bandcount = 12
            elif bandcount == 4:
                indexes = list(range(1, 4 + 1))
            elif bandcount == 5:
                indexes = [1, 2, 3, 5]
                bandcount = 4
            else:
                raise Exception(f'bands={bandcount}')

            # gather up batches
            batches = []
            for i in range(0, width - n, args.stride):
                for j in range(0, height - n, args.stride):
                    batches.append((i, j))
            batches = [batches[i:i + args.chunksize] for i in range(0, len(batches), args.chunksize)]

            for batch in tqdm.tqdm(batches):
                windows = [infile_ds.read(indexes, window=Window(i, j, n, n)) for (i, j) in batch]
                windows = [w.astype(np.float32) for w in windows]
                if args.ndwi_mask:
                    windows = [w * (((w[2] - w[7]) / (w[2] + w[7])) > 0.0) for w in windows]

                try:
                    windows = np.stack(windows, axis=0)
                except:
                    continue
                windows = torch.from_numpy(windows).to(dtype=torch.float32, device=device)
                prob = model(windows)

                for k, (i, j) in enumerate(batch):
                    if 'seg' in prob:
                        _prob = torch.sigmoid(prob.get('seg')[k, 1]) - torch.sigmoid(prob.get('seg')[k, 0])
                        ar_out[0, j:(j + n), i:(i + n)] += _prob
                    else:
                        ar_out[0, j:(j + n), i:(i + n)] += torch.sigmoid(prob.get('class')[k, 0])
                    pixel_hits[0, j:(j + n), i:(i + n)] += 1

        # Bring results back to CPU
        ar_out /= pixel_hits
        ar_out = ar_out.cpu().numpy()

        # Write results to file
        with rio.open(outfile, 'w', **out_raw_profile) as outfile_raw_ds:
            outfile_raw_ds.write(ar_out[0], indexes=1)
