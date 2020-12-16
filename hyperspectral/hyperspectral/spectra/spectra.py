from collections import Counter
from copy import deepcopy
from functools import reduce
import re

import numpy as np
import parsec
import scipy.interpolate as interpolate

class Spectrum:
    def __init__(self, name, type_, class_, x_min, x_max, n_samples, info, x, y):
        self.name = name
        self.type_ = type_
        self.class_ = class_
        self.x_range = [x_min, x_max]
        self.n_samples = n_samples
        self.info = info
        self.x = np.array(x)
        self.y = np.array(y)

    def plot(self, rnga=None, rngb=None):
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

        fig = plt.figure()
        plt.plot(x, y)
        fig.suptitle(self.name)
        if 'X Untitlednits' in self.info:
            plt.xlabel(self.info['X Units'])
        if 'X Units' in self.info:
            plt.ylabel(self.info['Y Units'])
        return ax

    def resample(self, new_x):
        f = interpolate.interp1d(self.x, self.y)
        def do(x):
            try:
                return f(x)
            except:
                return float('nan')
        resampled = np.array([do(x) for x in new_x])
        return Spectrum(self.name, self.type_, self.class_, min(new_x), max(new_x), len(resampled), deepcopy(self.info), new_x, resampled)

    def drop_bands(self, bands):
        ixs = list(sorted(set(range(0, self.n_samples)) - set(bands)))
        x = [self.x[i] for i in ixs]
        y = [self.y[i] for i in ixs]
        return Spectrum(self.name, self.type_, self.class_, min(x), max(x), len(x), deepcopy(self.info), x ,y)

    def __getitem__(self, ix):
        return self.info[ix]

    @staticmethod
    def parse_ECOSTRESS(filename):
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
    def __init__(self, spectra):
        self.spectra = spectra
        self.grp_fn = None
        self.groups = None
        self.source_bands = list(range(0, len(spectra[0].x)))

    def is_regular(self, tol=1e-8):
        m = np.array([s.x for s in self.spectra])
        return len(m.shape) == 2 and all(np.abs(np.min(m, axis=0) - np.max(m, axis=0)) < tol)

    def regularize(self, band_frequencies, source_bands=None):
        self.spectra = [s.resample(band_frequencies) for s in self.spectra]
        if source_bands:
            assert len(source_bands) == len(band_frequencies)
            self.source_bands = source_bands
        else:
            self.source_bands = list(range(0, len(band_frequencies)))

    @property
    def band_count(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        return len(self.spectra[0].x)

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

    def invalid_band_count(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        samples = np.array([s.y for s in self.spectra])
        return np.sum(np.isnan(samples), 0)

    def invalid_spectra(self, band=None):
        assert self.is_regular(), 'Spectral collection must be regular'
        if band:
            return list(filter(lambda s: np.isnan(s.y[band]), self.spectra))
        else:
            return list(filter(lambda s: any(map(lambda x: np.isnan(x), s.y)), self.spectra))

    def drop_bands(self, ixs):
        assert self.is_regular(), 'Spectral collection must be regular'
        self.source_bands = [self.source_bands[i] for i in list(sorted(set(range(0,len(self.spectra[0].x))) - set(ixs)))]
        self.spectra = [s.drop_bands(ixs) for s in self.spectra]
        self.grp_fn = None
        self.groups = None

    def drop_invalid_spectra(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        self.spectra = list(filter(lambda s: not any(map(lambda x: np.isnan(x), s.y)), self.spectra))
        self.grp_fn = None
        self.groups = None

    def filter_spectra(self, filter_fn):
        self.spectra = list(filter(filter_fn, self.spectra))
        self.grp_fn = None
        self.groups = None

    def group_by(self, grp_fn):
        assert self.is_regular(), 'Spectral collection must be regular'
        groups = set(map(grp_fn, self.spectra))
        self.grp_fn = grp_fn
        self.groups = dict(sorted(map(lambda x: (x[1], x[0]), enumerate(groups))))

    @property
    def group_vector(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        assert self.groups and self.grp_fn, 'Groups must be assigned'
        return [self.groups[self.grp_fn(s)] for s in self.spectra]

    @property
    def model_matrix(self):
        assert self.is_regular(), 'Spectral collection must be regular'
        return np.array([s.y for s in self.spectra]).transpose()
