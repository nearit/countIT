#!/usr/bin/python
"""This module exposes a method to compress a file with gzip"""
from io import BytesIO
from tempfile import TemporaryFile
import gzip
import shutil

def gzip_file(filename, in_memory=True):
    """Gzips a file, in memory or on disk"""
    with open(filename, 'rb') as file_path:
        if in_memory:
            compressed_fp = BytesIO()
        else:
            compressed_fp = TemporaryFile()
        with gzip.GzipFile(fileobj=compressed_fp, mode='wb') as gzipper:
            shutil.copyfileobj(file_path, gzipper)
        compressed_fp.seek(0)
        return compressed_fp
