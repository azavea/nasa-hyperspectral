from functools import partial
import math
from pkg_resources import resource_filename

import numpy as np
import scipy.io
from scipy.signal import correlate2d

def fokker_planck_kernel():
    # This function depends on the preprocessed kernel provided by
    # https://github.com/Acicone/Iterative-Filtering-IF/blob/master/prefixed_double_filter.mat
    return scipy.io.loadmat(resource_filename('hyperspectral.resources', 'prefixed_double_filter.mat'))['MM'].flatten()

def get_mask(k, kernel=None):
    assert isinstance(k, int), "Must provide integer-valued mask support width"

    if kernel is None:
        kernel = fokker_planck_kernel()

    n = len(kernel)
    m = int((n - 1) / 2)

    if k < m:
        mask = np.zeros(2 * k + 1)
        stops = np.linspace(0, n, 2 * k + 2)
        for i in range(2 * k + 1):
            left_frac = math.ceil(stops[i]) - stops[i]
            right_frac = stops[i+1] - math.floor(stops[i+1])
            lidx = math.ceil(stops[i]) #if i >0 else 0
            ridx = math.floor(stops[i+1]) #if i < 2 * k else n - 1
            mask[i] = (left_frac * kernel[lidx-1] if lidx>0 else 0.0) + \
                np.sum(kernel[lidx:ridx]) + \
                (right_frac * kernel[ridx+1] if ridx < n-1 else 0.0)
    else:
        # Interpolate results
        dx = 0.01
        f = kernel / dx
        dy = m * dx / k

        b = np.interp(np.linspace(0, m, k + 1), range(m+1), f[m:n])
        mask = np.hstack([np.flip(b), b[1:]]) * dy

    mask = mask / np.linalg.norm(mask, 1)

    return mask


def get_mask_2d(k, kernel_1d=None):
    m = get_mask(k, kernel_1d)

    cols = np.array(list(range(k,-1,-1)) * (k + 1)).reshape((k+1,k+1))
    rows = cols.transpose()
    rad = np.sqrt(np.power(rows, 2) + np.power(cols,2))

    xs = sorted(set(rad.flatten()))
    ys = np.interp(xs, range(k+1), m[k:])

    lookup = {x: y for (x, y) in zip(xs, ys)}

    ul = np.vectorize(lambda x: lookup[x])(rad)
    top = np.hstack([ul, np.fliplr(ul)[:,1:]])
    kernel = np.vstack([top, np.flipud(top)[1:,:]])

    return kernel / np.sum(kernel)


def count_extrema(signal, axis=None):
    def extrema1(sig):
        lead = sig[2:]
        lag = sig[:-2]
        sig = sig[1:-1]

        return np.sum(
            np.logical_or(
                np.logical_and(sig < lead, sig < lag),
                np.logical_and(sig > lead, sig > lag)
            )
        )

    if axis is None:
        return extrema1(signal.flatten())
    else:
        return np.apply_along_axis(extrema1, axis, signal)


def spherical_radius(signal, χ):
    assert len(signal.shape) == 2
    l_row = 2 * np.mean(np.floor(χ * signal.shape[1] / count_extrema(signal, axis=0)))
    l_col = 2 * np.mean(np.floor(χ * signal.shape[0] / count_extrema(signal, axis=0)))

    return int((l_row + l_col) / 2)

def imf(f, kernel, τ, max_iters):
    """
    Find the next Intrinsic Mode Function of an image

    Arguments:
        f (np.ndarray): A 2-d image matrix, values have mean of zero
        kernel (np.ndarray): A 2-d cross-correlation kernel
        τ (float): The termination error threshold
        max_iters (int): The largest number of permissible iterations

    Returns an np.ndarray and the final termination error value
    """
    err = []

    try:
        from tqdm.autonotebook import tqdm
        rng = tqdm(range(max_iters), leave=False)
        use_tqdm = True
    except:
        rng = range(max_iters)
        use_tqdm = False

    for i in rng:
        mva = correlate2d(f, kernel, mode='same', boundary='symm')
        last = f
        f = f - mva
        err.append(np.linalg.norm(f - last, 2) / np.linalg.norm(last, 2))
        if err[-1] < τ or err[-1] > min(err):
            if use_tqdm:
                rng.reset()
                rng.close()
            break

    return f, err

def mif(signal, χ=1.6, τ=0.001, max_iters=1000, max_imfs=25):
    f = signal - np.mean(signal)
    imfs = []

    try:
        from tqdm.autonotebook import tqdm
        rng = tqdm(range(max_imfs))
    except:
        rng = range(max_imfs)

    for i in rng:
        k = spherical_radius(f, χ)
        kernel = get_mask_2d(k)
        imf_n, _ = imf(f, kernel, τ, max_iters)
        imfs.append(imf_n)
        f = f - imf_n

    return imfs, f
