#!/usr/bin/python
"""This module takes care of uploading every detection file to S3 bucket"""
import logging
import json
import os

from uploader import post_detections

LOG_LEVEL = logging.INFO
LOG_FILE = "/var/log/countit.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
config_file = "config.json"
config = os.path.join(script_dir, config_file)

with open(config, 'r') as f:
    config = json.load(f)
    folder_name = config["customer"]+"/"+config["env"]+"/"+config["device_id"]
    endpoint = config["endpoint"]
    token = config["token"]
    path = os.path.join(script_dir, folder_name)

    logging.info("Starting dumps upload")
    # enumerate local files recursively
    for root, dirs, files in os.walk(path):
        for filename in files:
            file_path = os.path.join(path, filename)
            with open(file_path) as f:
                content = f.read()
                post_detections(content, endpoint, token)
    
    logging.info("Dumps upload done.")
