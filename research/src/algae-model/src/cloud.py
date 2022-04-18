from typing import List

import torch
import torch.hub
import torchvision as tv
import torch.nn.functional as F


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


class Nugget(torch.nn.Module):
    def __init__(self, kernel_size, in_channels, out_channels, preshrink):
        super(Nugget, self).__init__()
        self.conv2ds = torch.nn.ModuleDict()
        for n in in_channels:
            self.conv2ds[str(n)] = torch.nn.Conv2d(n, 10, kernel_size=kernel_size)
        self.batch_norm = torch.nn.BatchNorm2d(10)
        self.relu = torch.nn.ReLU()
        self.cheaplab = torch.hub.load(
            'jamesmcclain/CheapLab:38af8e6cd084fc61792f29189158919c69d58c6a',
            'make_cheaplab_model',
            num_channels=10,
            preshrink=preshrink,
            out_channels=out_channels)

    def forward(self, x):
        n = x.shape[-3]
        out = self.conv2ds[str(n)](x)
        out = self.batch_norm(out)
        out = self.relu(out)
        out = self.cheaplab(out)
        return out


class CloudModel(torch.nn.Module):
    def __init__(self, in_channels: List[int], preshrink: int):
        super().__init__()
        magic_number = 3
        self.rs = torch.nn.ModuleList([Nugget(1, in_channels, 1, preshrink) for i in range(magic_number)])
        self.gs = torch.nn.ModuleList([Nugget(1, in_channels, 1, preshrink) for i in range(magic_number)])
        self.bgs = torch.nn.ModuleList([Nugget(1, in_channels, 1, preshrink) for i in range(magic_number)])

    def forward(self, x):
        if len(x.shape) != 4:
            raise Exception('ruh-roh')

        x[x < 0] = 0

        rs = [m(x) for m in self.rs]
        rs = torch.cat(rs, dim=1)

        gs = [m(x) for m in self.gs]
        gs = torch.cat(gs, dim=1)

        bgs = [m(x) for m in self.bgs]
        bgs = torch.cat(bgs, dim=1)

        out = [
            torch.unsqueeze(torch.amax(rs, dim=1), dim=1),
            torch.unsqueeze(torch.amax(gs, dim=1), dim=1),
            torch.unsqueeze(torch.amax(bgs, dim=1), dim=1)
        ]
        out = torch.cat(out, dim=1)
        # goodness = entropy_function(out[:, 0, :, :]) + entropy_function(out[:, 1, :, :])
        goodness = None

        return (out, goodness)


def make_cloud_model(in_channels: List[int], preshrink: int = 8):
    model = CloudModel(in_channels=in_channels, preshrink=preshrink)
    return model
