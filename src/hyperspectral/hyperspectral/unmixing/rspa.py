import math

import numpy as np

def compute_alpha(x, y, β):
    u = x / np.linalg.norm(x, 2)
    assert np.linalg.norm(x, 2) > np.linalg.norm(y, 2), "x must be larger in norm than y"
    num = (β * np.linalg.norm(x, 2)**2 - np.linalg.norm(y, 2)**2)
    denom = (β * np.dot(u, x)**2 - np.dot(u, y)**2)
    #print('Numerator:   {}\nDenominator: {}'.format(num, denom))
    return 1 - math.sqrt(1 - num / denom)

def select_key(spectra, d, p, β):
    try:
        from tqdm.autonotebook import trange
    except:
        trange = range

    m = spectra.shape[1]
    R = spectra
    Y = R
    Py = np.eye(m)
    k = []
    k1 = []
    e = []
    for i in trange(d, leave=False):
        k.append(np.argmax(np.linalg.norm(Y, 2, axis=1)))
        u = spectra[k[i]] / np.linalg.norm(spectra[k[i]], 2)
        R = spectra - np.einsum('n,m->nm',np.matmul(spectra, u), u)
        e.append(np.sum(np.linalg.norm(R, 2, axis=1)**p))
        k1.append(np.argmax(np.linalg.norm(R, 2, axis=1)))
        x = Y[k[i]]
        y = Y[k1[i]]
        #x = np.matmul(Py, spectra[k[i]])
        #y = np.matmul(Py, spectra[k1[i]])
        α = compute_alpha(x, y, β)
        Y = Y - α * np.einsum('n,m->nm', np.matmul(Y, u), u)
        #Py = np.matmul(np.eye(m) - α * np.outer(u, u), Py)
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
