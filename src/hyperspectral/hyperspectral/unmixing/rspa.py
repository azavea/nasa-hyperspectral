import math

import numpy as np

def compute_alpha(x, y, β):
    nx, ny = np.linalg.norm(x, 2), np.linalg.norm(y, 2)
    u = x / nx
    #assert nx > ny, "x must be larger in norm than y"
    num = (β * nx**2 - ny**2)
    denom = (β * np.dot(u, x)**2 - np.dot(u, y)**2)
    return 1 - math.sqrt(1 - num / denom)

def select_key(R, d, p, β):
    try:
        from tqdm.autonotebook import trange
    except:
        trange = range

    m = R.shape[1]
    Y = R
    k = []
    k1 = []
    e = []
    for i in trange(d, leave=False):
        k.append(np.argmax(np.linalg.norm(Y, 2, axis=1)))
        u = R[k[i]] / np.linalg.norm(R[k[i]], 2)
        Ri = R - np.outer(np.matmul(R, u), u)
        e.append(np.sum(np.linalg.norm(Ri, 2, axis=1)**(p/2)))
        if i < d - 1:
            uyi = Y[k[i]] / np.linalg.norm(Y[k[i]], 2)
            Yi = Y - np.outer(np.matmul(Y, uyi), uyi)
            normY = np.linalg.norm(Yi, 2, axis=1)
            k1.append(np.argmax(normY))
            if normY[k1[i]] < 1e-12:
                break
            else:
                x = Y[k[i]]
                u = x / np.linalg.norm(x, 2)
                y = Y[k1[i]]
                α = compute_alpha(x, y, β)
                assert α > 0 and α < 1, "α out of range (0,1)"
                Y = Y - α * np.outer(np.matmul(Y, u), u)
    return k[np.argmin(e)]

def rspa(image, n, d, β=4.0, p=1, tol=1e-8):
    if len(image.shape)==3:
        spectra = image.reshape((image.shape[0]*image.shape[1], -1))
    else:
        spectra = image
    R = spectra
    k = 1
    keys = []
    while np.any(np.abs(R) > tol) and k <= n:
        key = select_key(R, d, p, β)
        u = R[key] / np.linalg.norm(R[key], 2)
        R = R - np.einsum('n,m->nm', np.matmul(R, u), u)
        keys.append(key)
        k = k + 1
    return spectra[keys]
