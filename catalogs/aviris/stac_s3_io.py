from urllib.parse import urlparse

import boto3
from pystac import STAC_IO


def s3_read(uri):
    parsed = urlparse(uri)
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        s3 = boto3.resource("s3")
        obj = s3.Object(bucket, key)
        return obj.get()["Body"].read().decode("utf-8")
    else:
        return STAC_IO.default_read_text_method(uri)


def s3_write(uri, txt):
    parsed = urlparse(uri)
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        s3 = boto3.resource("s3")
        s3.Object(bucket, key).put(Body=txt)
    else:
        STAC_IO.default_write_text_method(uri, txt)


def register_s3_io():
    STAC_IO.read_text_method = s3_read
    STAC_IO.write_text_method = s3_write
