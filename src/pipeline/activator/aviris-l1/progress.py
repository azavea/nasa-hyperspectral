from contextlib import contextmanager
from math import floor
import os
import sys
import threading
from time import time
from tqdm import tqdm


class ProgressPercentage(object):
    """ Callable object for use with s3.upload_object callback """

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r{}  {} / {} ({:.2f}%)".format(
                    self._filename, self._seen_so_far, self._size, percentage
                )
            )
            sys.stdout.flush()
            if percentage >= 100:
                print("")


@contextmanager
def timing(description: str) -> None:
    """ Prints time elapsed between context manager opened and closed """
    start = time()
    yield
    elapsed = time() - start
    print("{}: {:.4f}s".format(description, elapsed))


def warp_callback(progress, *args):
    """ Report progress for GDALWarp callback argument """
    progress_pct = floor(progress * 100)
    if progress_pct % 10 == 0 > progress_pct > 0:
        print("GDAL Warp: {}%".format(progress_pct))


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)
