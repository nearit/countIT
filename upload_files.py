#!/usr/bin/python

import json
import os

from uploader import upload_file

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
config_file = "config.json"
config = os.path.join(script_dir, config_file)

with open(config, 'r') as f:
    config = json.load(f)
    folder_name = config["customer"]+"/"+config["env"]+"/"+config["device_id"]
    bucket_name = config["bucket_name"]
    path = os.path.join(script_dir, folder_name)

    # enumerate local files recursively
    for root, dirs, files in os.walk(path):
        for filename in files:
            # construct the full local path
            file_path = os.path.join(path, filename)
            # upload the file
            print(folder_name+"/"+filename)
            upload_file(file_path, bucket_name, folder_name+"/"+filename)
