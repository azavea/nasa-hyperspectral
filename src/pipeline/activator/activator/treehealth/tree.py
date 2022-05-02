from typing import List

import numpy as np

import torch
import torch.hub
import torchvision as tv
import torch.nn.functional as F


class TreeModel(torch.nn.Module):
    def __init__(self, preshrink: int):
        super().__init__()
        magic_number = 13
        self.cheaplabs = torch.nn.ModuleList([
            torch.hub.load(
                'jamesmcclain/CheapLab:38af8e6cd084fc61792f29189158919c69d58c6a',
                'make_cheaplab_model',
                num_channels=224,
                preshrink=preshrink,
                out_channels=1)
            for i in range(magic_number)])
        self.conv2d1 = torch.nn.Conv2d(magic_number, 3, 1)
        self.conv2d2 = torch.nn.Conv2d(magic_number, 3, 1)
        self.relu = torch.nn.ReLU()

    def forward(self, x):
        x[x < 0] = 0
        xs = [m(x) for m in self.cheaplabs]
        xs = torch.cat(xs, dim=1)
        a = self.conv2d1(xs)
        b = self.conv2d2(xs)
        out = self.relu(a*b)
        return out


def make_tree_model(preshrink: int = 8):
    model = TreeModel(preshrink=preshrink)
    return model
