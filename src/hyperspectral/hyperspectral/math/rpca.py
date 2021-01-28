import math

import matplotlib.pyplot as plt
import numpy as np
import scipy
from tqdm.autonotebook import tqdm


def mad(M):
    return np.median(np.abs(M - np.median(M, axis=0)), axis=0)


def rpca_grid(data, max_dim=None, n_c=5, n_g=11, S=mad, sufficient=None):
    assert len(data.shape)==2, "Provide data as matrix of column vectors"
    if n_g % 2 == 0:
        # The search seems to fail when n_g is even
        n_g = n_g + 1

    p, n = data.shape
    max_dim = max_dim if max_dim else p

    # Order samples so that S(e(i)) >= S(e(j)) when i < j
    row_scores = np.array([S(data[i,:]) for i in range(p)])
    var_order = [y[1] for y in sorted([(x[1], x[0]) for x in enumerate(row_scores)], reverse=True)]
    rev_order = [y[1] for y in sorted([(x[1], x[0]) for x in enumerate(var_order)])]
    Xt = data[var_order,:].transpose()

    def e(j):
        x = np.zeros((p,1))
        x[j] = 1.0
        return x

    A = np.zeros((p, max_dim))
    for k in tqdm(range(max_dim), desc="Vector"):
        for i in tqdm(range(n_c), leave=False, desc="Iteration"):
            prev = float('nan')
            with tqdm(total=p, bar_format="{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {postfix[0]} {postfix[1][value]:>6.4g} [{elapsed}<{remaining}]",
              postfix=["Score", dict(value=float('nan'))], leave=False) as t:
                for j in range(p):
                    if i==0 and j==0:
                        â = e(0)
                        t.update()
                        continue
                    th = np.linspace(-math.pi/math.pow(2, i+1), math.pi/math.pow(2, i+1), n_g)
                    cands = np.outer(â, np.cos(th)) + np.outer(e(j), np.sin(th))
                    cands = cands / np.linalg.norm(cands, ord=2, axis=0)
                    scores = S(np.dot(Xt, cands))
                    best = np.argmax(scores)
                    â = cands[:,best]
                    t.postfix[1]["value"] = scores[best]
                    t.update()
        A[:,k] = â
        Xt = Xt - np.outer(np.dot(Xt, â), â)

        result = A[rev_order,0:(k+1)]
        if sufficient is not None and sufficient(result):
            break

    return result


def projection(basis):
    return np.linalg.solve(np.matmul(basis.transpose(), basis), basis.transpose())


def goodness_of_fit(basis, target, ax=None):
    proj = projection(basis)
    fitted = np.matmul(basis, np.matmul(proj, target))

    if ax is not None:
        plt.plot(fitted)
        plt.plot(target)

    e = target - fitted
    dev = target - np.mean(target)
    r2 = 1 - np.inner(e, e) / np.inner(dev, dev)

    return r2, proj


def basis_for_target(samples, target, max_dim=None, min_r2=0.9):
    def fit_criteria(signal, r2):
        def test(B):
            r2_actual, _ = goodness_of_fit(B, signal)
            return r2_actual > r2

        return test

    assert len(samples.shape == 2), "Input samples must be delivered as matrix of column vectors"
    p,n = samples.shape
    max_dim = max_dim if max_dim else p

    return pca_grid(samples, max_dim, sufficient=fit_criteria(target, min_r2))


def project_data(data, basis=None, proj=None):
    assert (basis is not None and proj is None) or (basis is None and proj is not None), "Must provide either a basis or a projection matrix"

    if proj is None:
        proj = projection(basis)

    if len(data.shape)==3:
        return np.einsum('ij,rcj->rci', proj, data)
    elif len(data.shape) < 3:
        return np.matmul(proj, data)
    else:
        raise ValueError("Data must be single vector, matrix of column vectors, or r × c × b image")


def whitening_matrix(vcov):
    return scipy.linalg.sqrtm(scipy.linalg.inv(vcov))


def whiten(centered_data, vcov=None, white_matrix=None):
    if white_matrix is None:
        assert vcov is not None, "Must provide a variance-covariance matrix if no whitening matrix is provided"
        white_matrix = whitening_matrix(vcov)

    if len(centered_data.shape)==3:
        return np.einsum('ij,rcj->rci', white_matrix, centered_data)
    elif len(centered_data.shape) < 3:
        return np.matmul(white_matrix, centered_data)
    else:
        raise ValueError("Centered data must be single vector, matrix of column vectors, or r × c × b image")
