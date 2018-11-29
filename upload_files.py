import json
import os

from uploader import upload_file

with open('config.json', 'r') as f:
    config = json.load(f)
    folder_name = config["customer"]+"/"+config["env"]+"/"+config["id"]
    bucket_name = config["bucket_name"]
    path = os.getcwd()+"/"+folder_name

    # enumerate local files recursively
    for root, dirs, files in os.walk(path):
        for filename in files:
            # construct the full local path
            file_path = os.path.join(root, filename)
            # upload the file
            upload_file(file_path, bucket_name)