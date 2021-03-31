# Copyright 2021 Azavea
#
# Redistribution and use  in source and binary forms,  with or without
# modification, are  permitted provided that the  following conditions
# are met:
#
# 1. Redistributions  of source code  must retain the  above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions  and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither  the name of  the copyright holder  nor the names  of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY  THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS"  AND ANY EXPRESS  OR IMPLIED WARRANTIES, INCLUDING,  BUT NOT
# LIMITED TO,  THE IMPLIED  WARRANTIES OF MERCHANTABILITY  AND FITNESS
# FOR  A PARTICULAR  PURPOSE ARE  DISCLAIMED.  IN NO  EVENT SHALL  THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT  LIMITED TO,  PROCUREMENT OF  SUBSTITUTE GOODS  OR SERVICES;
# LOSS OF  USE, DATA,  OR PROFITS;  OR BUSINESS  INTERRUPTION) HOWEVER
# CAUSED AND ON  ANY THEORY OF LIABILITY, WHETHER  IN CONTRACT, STRICT
# LIABILITY, OR  TORT (INCLUDING  NEGLIGENCE OR OTHERWISE)  ARISING IN
# ANY WAY  OUT OF  THE USE OF  THIS SOFTWARE, EVEN  IF ADVISED  OF THE
# POSSIBILITY OF SUCH DAMAGE.

import numpy as np
import torch as torch
import torch.nn.functional as F


class MatchedFilter(torch.nn.Module):

    def __init__(self, W: np.array, bias: float):
        """Given a whitening (sphering) matrix and a bias, build a
        matched-filter target detection model in PyTorch.

        See https://en.wikipedia.org/wiki/Matched_filter for more.

        Parameters
        ----------
        W : np.array
            A c×c numpy array representing the initial whitening
            (sphering) matrix.  c is the number of channels in the
            imagery.
        bias : float
            A number representing the initial bias in the
            matched-filter computation (the number subtracted from the
            dot product of the transformed pixel and the transformed
            spectrum).

        """
        super(MatchedFilter, self).__init__()

        _W = torch.from_numpy(W.astype(np.float)).unsqueeze(2)
        _W = torch.nn.parameter.Parameter(_W)
        self.register_parameter('W', _W)

        _bias = torch.from_numpy(np.array(bias).astype(np.float)).reshape(1)
        _bias = torch.nn.parameter.Parameter(_bias)
        self.register_parameter('bias', _bias)

        self.relu = torch.nn.ReLU()

    def forward(self, x: torch.tensor, y: torch.tensor):
        """Given an n×c tensor representing n pixels of c channels and a c×1
        tensor representing a spectrum, perform the matched-filter
        computation.

        In detail, the computation consists of: (1) transforming the
        pixels using the sphering operator, (2) transforming the
        spectrum using the sphering operator, and (3) computing the
        dot-product of each transformed pixel with the transformed
        spectrum (minus the bias).

        Parameters
        ----------
        x : torch.tensor
            An n×c×1 tensor containing the hyperspectral pixel data.
        y : torch.tensor
            A 1×c×1 tensor containing the spectrum of interest.

        Returns
        -------
        torch.tensor
            An n×1×1 tensor containing the correlation between each
            transformed pixel and the transformed spectrum (minus the
            bias).

        """
        x = F.conv1d(x, self.W)  # step 1
        y = F.conv1d(y, self.W)  # step 2
        x = F.conv1d(x, y, self.bias)  # step 3
        x = self.relu(x)  # want correlations to be more than 0
        return x
