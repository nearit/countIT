#!/usr/bin/python
"""This module exposes a method to upload a single file to S3 bucket"""
import os

import boto3

from compressor import gzip_file

s3 = boto3.resource('s3')

def upload_file(filename, bucket_name, destination, compress=True, compress_in_memory=False):
    """Uploads a file to S3 bucket"""
    bucket = s3.Bucket(bucket_name)
    if compress:
        with gzip_file(filename, in_memory=compress_in_memory) as zipped_file:
            try:
                _ = bucket.upload_fileobj(
                    zipped_file,
                    destination,
                    {'ContentType': 'text/plain', 'ContentEncoding': 'gzip'}
                )
                os.remove(filename)
            except Exception as e:
                if hasattr(e, "message"):
                    print "Upload failed. %s" % e.message
                else:
                    print "Upload failed."
    else:
        try:
            s3.meta.client.upload_file(filename, bucket_name, destination)
            os.remove(filename)
        except Exception as e:
            if hasattr(e, "message"):
                print "Upload failed. %s" %e.message
            else:
                print "Upload failed."
