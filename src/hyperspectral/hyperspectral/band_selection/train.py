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


def vanilla_train(model: torch.nn.Module,
                  ps: torch.tensor,
                  ls: torch.tensor,
                  v: torch.tensor,
                  device: torch.device,
                  num_epochs: int = 500):
    """Given a model, some labeled hyperspectral pixels, a spectrum, and a
    number of training epochs, train the model to do a better job of
    discriminating between the given foreground and background pixels.

    It is imagined that one will start with a matched-filter (or
    similar) model constructed from theory and use this code to
    further improve it.

    Parameters
    ----------
    model : torch.nn.Module
        A PyTorch representation of a model.  In the typical case,
        this will be a PyTorch representation of a match-filter target
        detection model.
    ps : torch.tensor
        An n×c×1 tensor containing n hyperspectral pixels, each of c
        channels.
    ls : torch.tensor
        An n×1×1 tensor containing labels for the pixels ps.  0 is for
        background and 1 is for target.
    v : torch.tensor
        A 1×c×1 tensor containing the target spectrum.
    num_epochs : int
        The number of training epochs to use.

    Returns
    -------
    torch.nn.Module
        The trained model.

    """
    for parameter in model.parameters():
        parameter.requires_grad = True

    obj = torch.nn.BCEWithLogitsLoss().to(device)
    opt = torch.optim.SGD(model.parameters(), lr=1e-4, momentum=0.9)

    for i in range(0, num_epochs):
        opt.zero_grad()
        pred = model(ps, v)
        loss = obj(pred, ls)
        loss.backward()
        opt.step()

    return model
