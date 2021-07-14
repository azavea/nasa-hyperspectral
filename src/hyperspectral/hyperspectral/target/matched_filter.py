import math

import numpy as np
from scipy.optimize import root_scalar

from hyperspectral.math.rpca import whitening_matrix, whiten

def normalized_matched_filter(image, target, clutter_cov, center=False):
    """
    Perform target detection using a normalized matched filter

    This computes the cosine of the angle between a target spectrum and the
    spectra in a hyperspectral image in a whitened space.  The caller is
    responsible for any dimension reduction, and the clutter covariance matrix
    should describe the reduced pixels (if applicable).

    Arguments:
      image (numpy.array): An r×c×d matrix representing an image of d-dimensional spectra
      target (numpy.array): A d-dimensional vector representing the target spectrum
      clutter_cov (numpy.array): A d×d matrix describing the error model for the spectral bands
      center (bool): Whether to median-center the data before running the filter

    References:

      Manolakis, D. G., Lockwood, R. B., & Cooley, T. W. (2016).  Hyperspectral
      imaging remote sensing: Physics, sensors, and algorithms (pp. 494–576).
      Cambridge University Press.

    """
    white = whitening_matrix(clutter_cov)

    if center:
        r,c,d = image.shape
        med = np.median(image.reshape((r * c, d)), axis=0)
        image = image - med
        target = target - med

    X̃ = whiten(image, white_matrix=white)
    s̃ = whiten(target, white_matrix=white)

    return np.divide(np.einsum('i,rci->rc', s̃, X̃), np.sqrt(np.einsum('rci,rci->rc',X̃, X̃)))/math.sqrt(np.inner(s̃, s̃))


def quad_form(ζ, s̃, λ, ε):
    val = np.sum(np.divide(np.square(s̃), np.square(1 + ζ * λ))) - ε
    deriv = -2 * np.sum(
        np.multiply(λ,
                    np.divide(
                        np.square(s̃),
                        (1 + ζ * λ) ** 3
                    )
                   )
    )
    return val, deriv


def robust_filter_vector(Σ, s0, ε, ζ0):
    assert len(s0.shape)==1, "Expecting vector-valued s0"
    k = len(s0)
    assert Σ.shape == (k, k), "Expecting compatible, square Σ"

    λ, Q = np.linalg.eigh(Σ)
    s̃ = np.matmul(Q.T, s0)
    result = root_scalar(quad_form, args=(s̃, λ, ε), method="newton", fprime=True, x0=ζ0)

    if not result.converged:
        raise ValueError("Iteration to find ζ failed to converge!")

    ζ = result.root

    Minv = np.linalg.inv(Σ - (1/ζ) * np.eye(k))

    return np.matmul(Minv, s0) / np.inner(s0, np.matmul(np.matmul(np.matmul(Minv, Σ), Minv), s0))


def robust_matched_filter(image, target, clutter_cov, ε=1e-6, ζ0= 1e-6, center=False):
    """
    Apply a robust matched filter to perform a target detection on a set of spectra.

    Arguments:
        image (np.array): spectral data to perform the matched filter on; can be of
            shape (n, p) or (r, c, p) for p-dimensional spectra
        target (np.array): p-dimensional array giving the approximate target spectrum
        clutter_cov (np.array): p×p matrix describing the background covariance; best
            to derive this with a shrinkage covariance estimator such as
            sklearn.covariance.LedoitWolf
        ε (real): max distance from given target spectrum to actual target spectrum
        ζ (real): initial guess for RMF regularization parameter
        center (bool or np.array): Boolean flag to determine if data should be
            median-centered before applying filter, or spectrum to center signals on
            prior to filtering

    Reference:
        Manolakis, D., Lockwood, R., Cooley, T., & Jacobson, J. (2009, August).
        Hyperspectral detection algorithms: Use covariances or subspaces?. In Imaging
        Spectrometry XIV (Vol. 7457, p. 74570Q). International Society for Optics and
        Photonics.
    """
    if isinstance(center, bool) and center:
        r,c,d = image.shape
        med = np.median(image.reshape((r * c, d)), axis=0)
        image = image - med
        target = target - med
    elif isinstance(center, np.ndarray):
        image = image - center
        target = target - center

    h = robust_filter_vector(clutter_cov, target, ε, ζ0)

    if len(image.shape) == 2:
        return np.dot(image, h)
    elif len(image.shape) == 3:
        return np.einsum('rci,i->rc', image, h)
    else:
        raise ValueError("Input image must be n×p or r×c×p numpy array")
