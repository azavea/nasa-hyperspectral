from typing import List

import torch
import torch.hub
import torchvision as tv


class AlgaeSegmentationToClassification(torch.nn.Module):
    def __init__(self, chip_size: int = 32):
        super().__init__()
        self.pool = torch.nn.AdaptiveAvgPool2d(output_size=1)
        self.conv2d = torch.nn.Conv2d(in_channels=1,
                                      out_channels=1,
                                      kernel_size=1,
                                      bias=True)

    def forward(self, x):
        x = x[:, [1], :, :]
        x = self.pool(x)
        x = self.conv2d(x)
        return x


class AlgaeClassifier(torch.nn.Module):
    def __init__(self,
                 in_channels: List[int],
                 backbone_str: str,
                 pretrained: bool,
                 prescale: int,
                 chip_size: int = 32):
        super().__init__()

        self.backbone_str = backbone_str
        self.prescale = prescale

        # Backbone
        if 'fpn' in self.backbone_str and 'resnet' in self.backbone_str:
            bb = self.backbone_str.split('_')[-1]
            self.backbone = torch.hub.load(
                'AdeelH/pytorch-fpn:98c2ea43a9b0118c2e1dc29497bf6c832da5706b',
                'make_fpn_resnet',
                name=bb,
                fpn_type='panoptic',
                num_classes=2,
                fpn_channels=256,
                in_channels=3,
                out_size=(chip_size, chip_size))
            self.seg_to_class = AlgaeSegmentationToClassification(chip_size=chip_size)
        elif 'fpn' in self.backbone_str and 'efficientnet' in self.backbone_str:
            bb = '_'.join(self.backbone_str.split('_')[-2:])
            self.backbone = torch.hub.load(
                'AdeelH/pytorch-fpn:98c2ea43a9b0118c2e1dc29497bf6c832da5706b',
                'make_fpn_efficientnet',
                name=bb,
                fpn_type='panoptic',
                num_classes=2,
                fpn_channels=256,
                in_channels=3,
                out_size=(chip_size, chip_size))
            self.seg_to_class = AlgaeSegmentationToClassification(chip_size=chip_size)
        elif 'efficientnet_b' in self.backbone_str:
            self.backbone = torch.hub.load(
                'lukemelas/EfficientNet-PyTorch:7e8b0d312162f335785fb5dcfa1df29a75a1783a',
                backbone_str,
                num_classes=1,
                in_channels=3,
                pretrained=('imagenet' if pretrained else None))
        else:
            backbone = getattr(tv.models, self.backbone_str)
            self.backbone = backbone(pretrained=pretrained)

        # First
        if 'fpn' in self.backbone_str and 'resnet' in self.backbone_str:
            self.first = self.backbone[0].m[0][0]
        elif 'fpn' in self.backbone_str and 'efficientnet' in self.backbone_str:
            self.first = self.backbone[0].m._conv_stem
        elif 'efficientnet_b' in self.backbone_str:
            self.first = self.backbone._conv_stem
        else:
            if self.backbone_str == 'vgg16':
                self.first = self.backbone.features[0]
            elif self.backbone_str == 'squeezenet1_0':
                self.first = self.backbone.features[0]
            elif self.backbone_str == 'densenet161':
                self.first = self.backbone.features.conv0
            elif self.backbone_str == 'shufflenet_v2_x1_0':
                self.first = self.backbone.conv1[0]
            elif self.backbone_str == 'mobilenet_v2':
                self.first = self.backbone.features[0][0]
            elif self.backbone_str in ['mobilenet_v3_large', 'mobilenet_v3_small']:
                self.first = self.backbone.features[0][0]
            elif self.backbone_str == 'mnasnet1_0':
                self.first = self.backbone.layers[0]
            elif self.backbone_str in ['resnet18', 'resnet34', 'resnet50', 'resnet101', 'resnet152']:
                self.first = self.backbone.conv1
            else:
                raise Exception(f'Unknown backbone {self.backbone_str}')

        # Last
        if 'fpn' in self.backbone_str and 'resnet' in self.backbone_str:
            self.last = self.seg_to_class
        elif 'efficientnet_b' in self.backbone_str:
            self.last = self.seg_to_class
        elif self.backbone_str == 'vgg16':
            self.last = self.backbone.classifier[6] = torch.nn.Linear(
                in_features=4096, out_features=1, bias=True)
        elif self.backbone_str == 'squeezenet1_0':
            self.last = self.backbone.classifier[1] = torch.nn.Conv2d(
                512, 1, kernel_size=(1, 1), stride=(1, 1))
        elif self.backbone_str == 'densenet161':
            self.last = self.backbone.classifier = torch.nn.Linear(
                in_features=2208, out_features=1, bias=True)
        elif self.backbone_str == 'shufflenet_v2_x1_0':
            self.last = self.backbone.fc = torch.nn.Linear(in_features=1024,
                                                           out_features=1,
                                                           bias=True)
        elif self.backbone_str == 'mobilenet_v2':
            self.last = self.backbone.classifier[1] = torch.nn.Linear(
                in_features=1280, out_features=1, bias=True)
        elif self.backbone_str in ['mobilenet_v3_large', 'mobilenet_v3_small']:
            in_features = self.backbone.classifier[0].out_features
            self.last = self.backbone.classifier[3] = torch.nn.Linear(
                in_features=in_features, out_features=1, bias=True)
        elif self.backbone_str == 'mnasnet1_0':
            self.last = self.backbone.classifier[1] = torch.nn.Linear(
                in_features=1280, out_features=1, bias=True)
        elif self.backbone_str in ['resnet18', 'resnet34', 'resnet50', 'resnet101', 'resnet152']:
            in_features = self.backbone.fc.in_features
            self.last = self.backbone.fc = torch.nn.Linear(in_features, 1)
        else:
            raise Exception(f'Unknown backbone {self.backbone_str}')

        self.cheaplab = torch.nn.ModuleDict()
        for n in in_channels:
            self.cheaplab[str(n)] = torch.hub.load(
                'jamesmcclain/CheapLab:38af8e6cd084fc61792f29189158919c69d58c6a',
                'make_cheaplab_model',
                num_channels=n,
                out_channels=3)

    def forward(self, x):
        [w, h] = x.shape[-2:]
        n = x.shape[-3]
        out = x

        if self.prescale > 1:
            out = torch.nn.functional.interpolate(
                out,
                size=[w * self.prescale, h * self.prescale],
                mode='bilinear',
                align_corners=False)
        cheaplab = self.cheaplab[str(n)]
        if cheaplab is None:
            raise Exception(f"no CheapLab for {n} channels")
        out = cheaplab(out)
        out = self.backbone(out)

        [w, h] = out.shape[-2:]
        if len(out.shape) == 4 and w > 1 and h > 1 and w == h:
            _out = out
            out = {}
            out.update({'class': self.seg_to_class(_out)})
            out.update({'seg': _out})
        else:
            out = {'class': out}

        return out


def make_algae_model(in_channels: List[int], backbone_str: str,
                     pretrained: bool, prescale: int):
    model = AlgaeClassifier(in_channels=in_channels,
                            backbone_str=backbone_str,
                            pretrained=pretrained,
                            prescale=prescale)
    return model
