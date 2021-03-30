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

from typing import List

import numpy as np
import torch as torch
import torch.nn.functional as F


def argsort(model: torch.nn.Module,
            ps: torch.tensor,
            v: torch.tensor,
            inds: List[int]):
    """Given a model and some (positive) examples, return a list of band
    indices sorted according to salience.

    Parameters
    ----------
    model : torch.nn.Module
        A PyTorch representation of a model.  In the typical case,
        this will be a PyTorch representation of a match-filter target
        detection model.
    ps : torch.tensor
        An n⨯c⨯1 tensor containing n hyperspectral pixels, each of c
        channels.
    v : torch.tensor
        A 1⨯c⨯1 tensor containing the target spectrum.
    inds : List[int]
        A list of indices (relative to the first dimension of ps)
        containing "positive" pixels.

    Returns
    -------
    np.array
        A list of band indices sorted by salience

    """

    # Save training state
    model_train_state = model.training
    model.eval()

    ps.requires_grad_()
    pred = model(ps, v)

    for ind in inds:
        pred[ind, 0, 0].backward(retain_graph=True)

    salience = ps.grad.data.cpu().detach().numpy()
    salience = salience[inds, :, :]
    salience = np.mean(salience, axis=0)
    according_to_salience = np.argsort(np.abs(salience), axis=0)

    # Restore training state
    model.train(model_train_state)

    return according_to_salience
