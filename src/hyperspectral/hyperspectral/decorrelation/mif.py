from functools import partial
import math
from pkg_resources import resource_filename

import numpy as np
import scipy.io
from scipy.signal import correlate2d

try:
    import torch
    import torch.nn
    import torch.nn.functional as f
    torch_available = True
except:
    torch_available = False

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


def spherical_radius(signal, χ):
    assert len(signal.shape) == 2
    l_row = 2 * np.mean(np.floor(χ * signal.shape[0] / count_extrema(signal, axis=0)))
    l_col = 2 * np.mean(np.floor(χ * signal.shape[1] / count_extrema(signal, axis=1)))

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


def imf_torch(base, kernel, τ=0.001, max_iters=1000):
    err=[]

    _,_,w,_ = kernel.shape
    k = int((w - 1) / 2)

    try:
        from tqdm.autonotebook import tqdm
        rng = tqdm(range(max_iters), leave=False)
        use_tqdm = True
    except:
        rng = range(max_iters)
        use_tqdm = False

    for i in rng:
        padded = f.pad(base, (k,k,k,k), mode='reflect')
        smoothed = f.conv2d(padded, kernel, stride=1)
        last = base
        base = base - smoothed
        err.append(torch.linalg.norm((base - last)[0,0,:,:], ord=2) / torch.linalg.norm(last[0,0,:,:], ord=2))
        if err[-1] < τ or err[-1] > min(err):
            if use_tqdm:
                rng.update(max_iters)
                rng.close()
            break

    return base, err


def count_extrema_torch(m, axis):
    assert axis==0 or axis==1
    if axis == 0:
        lead_cols = m[:,2:]
        lag_cols = m[:,:-2]
        cols = m[:,1:-1]
        n_extrema = torch.sum(torch.logical_or(
            torch.logical_and(cols < lead_cols, cols < lag_cols),
            torch.logical_and(cols > lead_cols, cols > lag_cols)
        ).int(), dim=1)
    elif axis == 1:
        lead_rows = m[2:,:]
        lag_rows = m[:-2,:]
        rows = m[1:-1,:]
        n_extrema = torch.sum(torch.logical_or(
            torch.logical_and(rows < lead_rows, rows < lag_rows),
            torch.logical_and(rows > lead_rows, rows > lag_rows)
        ).int(), dim=0)
    return n_extrema


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


# def count_extrema(m, axis):
#     assert axis==0 or axis==1
#     if axis == 0:
#         lead_cols = m[:,2:]
#         lag_cols = m[:,:-2]
#         cols = m[:,1:-1]
#         n_extrema = np.sum(np.logical_or(
#             np.logical_and(cols < lead_cols, cols < lag_cols),
#             np.logical_and(cols > lead_cols, cols > lag_cols)
#         ).int(), dim=1)
#     elif axis == 1:
#         lead_rows = m[2:,:]
#         lag_rows = m[:-2,:]
#         rows = m[1:-1,:]
#         n_extrema = np.sum(np.logical_or(
#             np.logical_and(rows < lead_rows, rows < lag_rows),
#             np.logical_and(rows > lead_rows, rows > lag_rows)
#         ).int(), dim=0)
#     return n_extrema


def terminated_torch(m):
    return True if torch.logical_or(torch.min(count_extrema_torch(m, 0)) <= 1,
                                    torch.min(count_extrema_torch(m, 1)) <= 1) else False


def terminated(m):
    return True if np.logical_or(np.min(count_extrema_torch(m, 0)) <= 1,
                                 np.min(count_extrema_torch(m, 1)) <= 1) else False


def spherical_radius_torch(signal, χ):
    assert len(signal.shape) == 2
    l_row = 2 * torch.mean(torch.floor(χ * signal.shape[0] / count_extrema_torch(signal, axis=0)))
    l_col = 2 * torch.mean(torch.floor(χ * signal.shape[1] / count_extrema_torch(signal, axis=1)))

    return int((l_row + l_col) / 2)


def mif_torch(dev, signal, χ=1.6, τ=0.001, max_iters=1000, max_imfs=25):
    centered = signal - np.mean(signal)
    imfs = []

    f = torch.from_numpy(np.array([[centered]])).to(dev)
    base = torch.unsqueeze(f, 0)
    base = torch.unsqueeze(f, 0)

    try:
        from tqdm.autonotebook import tqdm
        rng = tqdm(range(max_imfs), leave=False)
        use_tqdm = True
    except:
        rng = range(max_imfs)
        use_tqdm = False

    for i in rng:
        k = spherical_radius_torch(f[0,0,:,:], χ)
        if k >= min(list(f.shape)[2:]):
            if use_tqdm:
                rng.update(max_imfs)
                rng.close()
            break
        kernel = get_mask_2d(k)
        tkern = torch.from_numpy(np.array([kernel], dtype=np.float32)).to(dev)
        kern = torch.unsqueeze(tkern, 0)
        kern = torch.unsqueeze(tkern, 0)
        imf_n, _ = imf_torch(f, kern, τ, max_iters)
        imfs.append(imf_n)
        f = f - imf_n
        if terminated_torch(f[0,0,:,:]):
            if use_tqdm:
                rng.update(max_imfs)
                rng.close()
            break

    return imfs, f


def mif(signal, χ=1.6, τ=0.001, max_iters=1000, max_imfs=25):
    """
    Multidimensional iterative filter

    Arguments:
        signal (np.array): The image to decorrelate
        χ: Spherical radius mutiplier
        τ: The error threshhold for IMF generation
        max_iters: Maximum allowable iterations for IMF generation
        max_imfs: Maximum allowable number of IMFs to generate

    References:
        Cicone, A., & Zhou, H. (2017).  Multidimensional iterative filtering method
        for the decomposition of high–dimensional non–stationary signals. Numerical
        Mathematics: Theory, Methods and Applications, 10(2), 278-298.
    """
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
        if terminated(f[0,0,:,:]):
            if use_tqdm:
                rng.update(max_imfs)
                rng.close()
            break

    return imfs, f


def mif_decorrelate(img, χ=1.6, τ=0.001, max_iters=1000, max_imfs=25, dev=None):
    """
    Decorrelate an image with MIF

    Arguments:
        img (np.array or torch.tensor): The image to decorrelate; if using torch, also set dev
        χ: Spherical radius mutiplier
        τ: The error threshhold for IMF generation
        max_iters: Maximum allowable iterations for IMF generation
        max_imfs: Maximum allowable number of IMFs to generate
        dev: Torch device, if applicable

    References:
        Cicone, A., Liu, J., & Zhou, H. (2016). Hyperspectral chemical plume
        detection algorithms based on multidimensional iterative filtering
        decomposition. Philosophical Transactions of the Royal Society A:
        Mathematical, Physical and Engineering Sciences, 374(2065), 20150196.
    """
    rng = range(img.shape[0])
    try:
        from tqdm.autonotebook import tqdm
        rng = tqdm(rng)
    except: pass

    if torch_available and dev is not None:
        do_mif = partial(mif_torch, dev)
        use_torch = True
    else:
        do_mif = mif
        use_torch = False

    decorrelated = []
    for i in rng:
        _, r = do_mif(img[i,:,:], χ, τ, max_iters, max_imfs)
        resid = r.detach().cpu().numpy() if use_torch else r
        decorrelated.append(img[i,:,:] - resid[0,0,:,:])
    return np.array(decorrelated)
