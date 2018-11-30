# CountIT

A [howmanypeoplearearound](https://github.com/schollz/howmanypeoplearearound) inspired tool.

## Setup

### Install tshark

```sh
sudo apt-get install tshark
```

Let tshark be run as non-root:

```sh
sudo dpkg-reconfigure wireshark-common     (select YES)
sudo usermod -a -G wireshark ${USER:-root}
newgrp wireshark
```

### Configuration

Once you have a configured RPi with a monitor-mode enabled WiFi adapter, you will need to install requirements:

```sh
pip install -r requirements.txt
```

Then you'll need to define a configuration. Place a `config.json` file at the root folder with this structure (replacing the placeholders):

```json
{
    "scan_time": 1200,
    "max_rssi": -70,
    "upload_frequency": "hourly",
    "bucket_name": "YOUR_BUCKET_NAME",
    "compression_type": "gzip",
    "compress_in_memory": true,
    "env": "dev",
    "customer": "CUSTOMER_NAME",
    "id": "01234567-89ab-cdef-0123-456789abcdef"
}
```

In order to successfully upload trackings to your S3 bucket, you must have AWS credentials in your RPi.

Run the following command

```sh
nano ~/.aws/credentials
```

and paste the structure below, fill in the placeholders and save it (`ctrl+x`, insert `y` and then press enter)

```text
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

## Test the tool

To test this tool just run

```sh
python countit.py
```

## Deploy the tool

Just run the setup, it will automagically schedule runs and uploads.

```sh
python setup.py
```