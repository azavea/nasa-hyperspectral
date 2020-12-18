from collections import Counter
from copy import deepcopy
from functools import reduce
import re

import numpy as np
import parsec
import scipy.interpolate as interpolate

class Spectrum:
    """
    A class to represent a hyperspectral radiance/reflectance curve

    Spectrum objects carry sampled spectral data to facilitate comparisons across and operations involving hyperspectral data.  The most salient functions of this class provide the means to manipulate the spectral curves via resampling or eliding bands.

    These objects also carry metadata describing the sampled curve—minimally, a name and a type/class pair.  Further metadata can be provided as a dictionary in the info field.  These data can be used for filtering purposes by SpectralLibrary instances.

    The means to parse individual spectra from various sources will also be a part of this class.  For now, only ECOSTRESS source files may be parsed.
    """
    def __init__(self, name, type_, class_, x_min, x_max, n_samples, info, x, y):
        """
        Create a Spectrum object

        The data are a matched pair of arrays, one with the x-values of the sample, the
        other with the corresponding y-values.  Identifying metadata for the spectrum are
        also attached.

        The info dictionary is not specified, but the plotting routine will look for
        'X Units' and 'Y Units' fields to label the plot axes.

        Arguments:
            name (str): A descriptive name for the spectrum
            type_ (str): The name of the broad category for the spectrum's substance
                         (ex: trees)
            class_ (str): The name of the narrow category for the spectrum's substance
                          (ex: evergreen)
            x_min (float): The smallest admissible value for the sampled x values
            x_max (float): The largest admissible value for the sampled x values
            n_samples (int): The number of sampled points
            info (dict): Additional metadata
            x (float list, np.array): The sampled x values
            y (float list, np.array): The y values at the sampled x locations
        """
        self.name = name
        self.type_ = type_
        self.class_ = class_
        self.x_range = [x_min, x_max]
        self.n_samples = n_samples
        self.info = info
        self.x = np.array(x)
        self.y = np.array(y)

    def plot(self, rnga=None, rngb=None, ax=None):
        """
        Produce a matplotlib plot of the sampled spectrum

        Arguments:
            rnga (float or (float, float)): The start of the x range to plot if a single number, or a tuple giving the start and end of the x range
            rngb (float): The end of the x range to plot
            ax (matplotlib.axes.Axes): The axes object to target, in case working with subplots
        """
        import matplotlib.pyplot as plt

        if rnga:
            if rngb:
                ixs = (rnga <= self.x) & (self.x <= rngb)
            else:
                ixs = (rnga[0] <= self.x) & (self.x <= rnga[1])

            x = self.x[ixs]
            y = self.y[ixs]
        else:
            x = self.x
            y = self.y

        if not ax:
            fig, ax = plt.subplots()

        ax.plot(x, y)
        ax.set_title(self.name)
        if 'X Units' in self.info:
            ax.set_xlabel(self.info['X Units'])
        if 'Y Units' in self.info:
            ax.set_ylabel(self.info['Y Units'])
        return ax

    def resample(self, new_x):
        """
        Choose new x values for the spectral curve

        Currently uses interpolation to identify the new y values.  This may change in
        the future.  As a result, new x values which are not contained in the domain of
        the original spectral curve result in NaN values.
        """
        f = interpolate.interp1d(self.x, self.y)
        def do(x):
            try:
                return f(x)
            except:
                return float('nan')
        resampled = np.array([do(x) for x in new_x])
        return Spectrum(self.name, self.type_, self.class_, min(new_x), max(new_x), len(resampled), deepcopy(self.info), new_x, resampled)

    def drop_bands(self, bands):
        """
        Elide bands from the curve

        This function uses the integer band indices to identify the bands to drop.
        """
        ixs = list(sorted(set(range(0, self.n_samples)) - set(bands)))
        x = [self.x[i] for i in ixs]
        y = [self.y[i] for i in ixs]
        return Spectrum(self.name, self.type_, self.class_, min(x), max(x), len(x), deepcopy(self.info), x ,y)

    def __getitem__(self, ix):
        return self.info[ix]

    @staticmethod
    def parse_ECOSTRESS(filename):
        """
        Load a spectrum from an ECOSTRESS file
        """
        spaces = parsec.regex(r'\s*', re.MULTILINE)

        @parsec.generate
        def header_field():
            k = yield spaces >> parsec.regex('[^:]*') << spaces
            yield parsec.string(':')
            v = yield parsec.ends_with(parsec.regex('[^\n]*'), parsec.string('\n'))
            return { k: v.strip() }

        @parsec.generate
        def header():
            items = yield parsec.many(header_field)
            d = {}
            for item in items:
                d.update(item)
            return d

        floating = parsec.regex('[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)')

        @parsec.generate
        def sample():
            fwhm = yield spaces >> floating << spaces
            level = yield floating << spaces
            yield parsec.optional(parsec.string('\n'))
            return (float(fwhm), float(level))

        @parsec.generate
        def parser():
            head = yield header
            yield parsec.many(parsec.string('\n'))
            samps = yield parsec.many(sample)
            return head, samps

        def parse_spectrum(filename):
            try:
                with open(filename, 'r', encoding='iso-8859-1') as f:
                    parsed = parser.parse(f.read())
                return parsed
            except:
                print('Error parsing '+filename)
                raise

        header, data = parse_spectrum(filename)

        name = header.pop('Name')
        type_ = header.pop('Type')
        class_ = header.pop('Class')
        x0 = float(header.pop('First X Value'))
        x1 = float(header.pop('Last X Value'))
        x_min, x_max = min(x0, x1), max(x0, x1)
        n_samples = header.pop('Number of X Values')

        x = list(map(lambda v: v[0], data))
        y = list(map(lambda v: v[1], data))

        return Spectrum(name, type_, class_, x_min, x_max, n_samples, header, x, y)


class SpectralLibrary:
    """
    A collection of Spectrum objects

    A SpectralLibrary maintains a collection of Spectrum objects and provides some means
    for gathering subcollections and normalizing the contained spectra.

    Arguments:
        spectra (Spectrum list): The contained spectra
    """
    def __init__(self, spectra):
        self.spectra = spectra
        self.grp_fn = None
        self.groups = None
        self.source_bands = list(range(0, len(spectra[0].x)))


    """
    Determine if all contained spectra are compatible

    This test is based on the x-values of the sampled spectra.  All contained spectra
    must have a matching sampling pattern for a library to be considered regular.  Many
    operations require a regular library.
    """
    def is_regular(self, tol=1e-8):
        m = np.array([s.x for s in self.spectra])
        return len(m.shape) == 2 and all(np.abs(np.min(m, axis=0) - np.max(m, axis=0)) < tol)

    """
    Resample all contained spectra to a common basis

    Arguments:
        band_frequencies (float list): Frequencies to resample to
        source_bands (int list): The band indexes corresponding to each frequency for
                                 referencing to an image source.  Uses the default range
                                 starting from 0 if omitted.
    """
    def regularize(self, band_frequencies, source_bands=None):
        self.spectra = [s.resample(band_frequencies) for s in self.spectra]
        if source_bands:
            assert len(source_bands) == len(band_frequencies)
            self.source_bands = source_bands
        else:
            self.source_bands = list(range(0, len(band_frequencies)))

    """
    Count the number of sampled bands in the (regular) library
    """
    @property
    def band_count(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        return len(self.spectra[0].x)

    """
    Identify the sample indices for which not all spectra are defined

    Resampling operators can return NaN for out-of-bounds frequencies.  This function
    will identify the indices of the bands for which not all spectra are defined.
    Requires a regularized library.
    """
    def invalid_bands(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        return set(
            reduce(lambda a, b: a + b, list(map(lambda s:
                list(map(lambda x: x[0],
                    filter(
                        lambda x: np.isnan(x[1]),
                        enumerate(s.y)
                    )
                )),
                self.spectra
            )))
        )

    """
    Counts the number of spectra which are not defined for each sample index

    Requires a regularized library.
    """
    def invalid_band_count(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        samples = np.array([s.y for s in self.spectra])
        return np.sum(np.isnan(samples), 0)

    """
    Returns all spectra which have undefined samples (optionally for a particular band)

    Requires a regularized library.
    """
    def invalid_spectra(self, band=None):
        assert self.is_regular(), 'Spectral collection must be regular'
        if band:
            return list(filter(lambda s: np.isnan(s.y[band]), self.spectra))
        else:
            return list(filter(lambda s: any(map(lambda x: np.isnan(x), s.y)), self.spectra))

    """
    Elide bands corresponding to given band indices

    Requires a regularized library.
    """
    def drop_bands(self, ixs):
        assert self.is_regular(), 'Spectral collection must be regular'
        self.source_bands = [self.source_bands[i] for i in list(sorted(set(range(0,len(self.spectra[0].x))) - set(ixs)))]
        self.spectra = [s.drop_bands(ixs) for s in self.spectra]
        self.grp_fn = None
        self.groups = None

    """
    Drop all spectra which have undefined sample values

    Requires a regularized library.
    """
    def drop_invalid_spectra(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        self.spectra = list(filter(lambda s: not any(map(lambda x: np.isnan(x), s.y)), self.spectra))
        self.grp_fn = None
        self.groups = None

    """
    Filter the available spectra

    Applies a function of type Spectrum → Boolean to all the spectra in the library and
    filters based on the results.  Can be in-place, or return a new, filtered library.
    """
    def filter_spectra(self, filter_fn, inplace=False):
        if inplace:
            self.spectra = list(filter(filter_fn, self.spectra))
            self.grp_fn = None
            self.groups = None
        else:
            return SpectralLibrary(list(filter(filter_fn, self.spectra)))

    """
    Puts spectra into groups based on a user-specified function

    Given a function from Spectrum to any type, the results of those functions define
    groups to which spectra in the library are assigned.  The groups property of the
    library gives the assignments corresponding to all spectra.

    Group information is destroyed when the contents of the library change through class
    methods.

    Requires a regularized library.
    """
    def group_by(self, grp_fn):
        assert self.is_regular(), 'Spectral collection must be regular'
        groups = set(map(grp_fn, self.spectra))
        self.grp_fn = grp_fn
        self.groups = dict(sorted(map(lambda x: (x[1], x[0]), enumerate(groups))))

    """
    Return a vector of group ids for each library spectra

    Requires that groups have been assigned via group_by.
    """
    @property
    def group_vector(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        assert self.groups and self.grp_fn, 'Groups must be assigned'
        return [self.groups[self.grp_fn(s)] for s in self.spectra]

    """
    Assemble library spectra values into a matrix

    Returns an n×p matrix with n samples per spectra and p spectra.  Each column holds
    the sampled values of the corresponding spectrum.

    Requires a regularized library.  May contain NaN values if invalid spectra have not
    been dropped.
    """
    @property
    def model_matrix(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        return np.array([s.y for s in self.spectra]).transpose()
