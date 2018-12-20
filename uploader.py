#!/usr/bin/python
"""This module exposes a method to post a single detection log to an endpoint"""
import logging
import requests

LOG_LEVEL = logging.INFO
LOG_FILE = "/var/log/countit.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)

def post_detections(payload, url, token):
    """Posts detections to an endpoint"""
    headers = {'content-type':'application/json'}
    headers['authorization'] = "Token %s"%token
    try:
        req = requests.post(url, data=payload, headers=headers)
        req.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("Upload failed: %s", err.message)
        return False
    else:
        return True
