#!/usr/bin/env python3

import sys
from urllib.parse import urlparse


def ftp_to_https(uri: str) -> str:
    if uri.startswith('ftp'):
        gzip_ftp_url = urlparse(uri)
        username_password, ftp_hostname = gzip_ftp_url.netloc.split("@")
        return f'https://{ftp_hostname}/avcl{gzip_ftp_url.path}'
    else:
        return uri


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(ftp_to_https(sys.argv[1]))
