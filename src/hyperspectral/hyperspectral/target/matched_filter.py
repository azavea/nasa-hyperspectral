import math

import numpy as np

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
        image = image - np.median(image.reshape((r * c, d)), axis=0)

    X̃ = whiten(image, white_matrix=white)
    s̃ = whiten(target, white_matrix=white)

    return np.divide(np.einsum('i,rci->rc', s̃, X̃), np.sqrt(np.einsum('rci,rci->rc',X̃, X̃)))/math.sqrt(np.inner(s̃, s̃))
