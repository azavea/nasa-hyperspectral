import math

import numpy as np

def shrinkage_covariance(data, regularizer='ridge', approx='mean-mahalanobis', tol=1e-6):
    """
    Compute an approximation to the covariance matrix.

    Computes a shrinkage estimator of the covariance matrix.  Avoids problems due to
    overfitting.

    Arguments:
        data (np.array): A p×n matrix describing the sampled values (p dims, n samples)
        regularizer (str): The name of the regularization strategy; either 'ridge' or
                           'cov_diag'
        approx (str): The log likelihood approximation to use; either 'mean-mahalanobis',
                      'hl' (Hoffbeck & Landgrebe) or None (defaults to 'hl')
        tol (float): Tolerance for likelihood optimization

    References:

    Theiler, J. (2012, May). The incredible shrinking covariance estimator. In Automatic
    Target Recognition XXII (Vol. 8391, p. 83910P). International Society for Optics and
    Photonics.
    """

    p, n = data.shape
    μ = np.mean(data, axis=1)
    S = np.cov(data)

    # x̅ = data - np.repeat(μ, n).reshape(p,n)
    # def Sk(k):
    #     x̅k = x̅[:,k]
    #     n1 = n - 1
    #     return n1 / (n1 - 1) * S - n / ((n - 1) * (n1 - 1)) * np.outer(x̅k, x̅k)

    if regularizer=='ridge':
        T = np.trace(S) / p * np.eye(p)
    elif regularizer=='cov_diag':
        T = np.diag(np.diag(S))
    else:
        raise ValueError('Unrecognized regularizer: {}'.format(regularizer))

    def LMM(α):
        β = (1 - α) / (n - 1)
        Gα = n * β * S + α * T
        try:
            Ginv = np.linalg.inv(Gα)
            detG = np.linalg.det(Gα)
            r0 = np.trace(np.matmul(Ginv, S))
            return (p * math.log(2 * math.pi) + math.log(detG) +
                    math.log(1 - β * r0) + r0 / (1 - β * r0)) / 2
        except np.linalg.LinAlgError:
            return np.inf

    def LHL(α):
        # TODO: implement Hoffbeck/Landgrebe approximation
        raise NotImplementedError('Hoffbeck/Landgrebe likelihood approximation not implemented')

    if not approx or approx=='hl':
        approxL = LHL
    elif approx=='mean-mahalanobis':
        approxL = LMM
    else:
        raise ValueError('Approximation strategy must be \'hl\', \'mean-mahalanobis\' or None')

    step = 0.1
    lo = 0.0
    hi = 1.0
    while step > tol:
        αs = np.arange(lo, hi + step, step)
        likelihoods = np.array(list(map(approxL, αs)))
        i = np.argmin(likelihoods)
        best = αs[i]
        lo = αs[max(i-1,0)]
        hi = αs[min(i+1,len(αs))]
        step = step / 10

    return (1 - best) * S + best * T
