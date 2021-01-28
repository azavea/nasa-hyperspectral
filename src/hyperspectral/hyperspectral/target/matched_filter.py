import math

import numpy as np

from hyperspectral.math.rpca import whitening_matrix, whiten

def normalized_matched_filter(image, target, clutter_cov):
    """

    """
    white = whitening_matrix(clutter_cov)
    X̃ = whiten(image, white_matrix=white)
    s̃ = whiten(target, white_matrix=white)

    return np.divide(np.einsum('i,rci->rc', s̃, X̃), np.sqrt(np.einsum('rci,rci->rc',X̃, X̃)))/math.sqrt(np.inner(s̃, s̃))
