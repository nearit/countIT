#!/usr/bin/python
"""CountIT"""
import json
import logging
import os
import subprocess
import sys
import threading
import time
import traceback

from crontab import CronTab

LOG_LEVEL = logging.INFO
LOG_FILE = "/var/log/countit.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)

def main():
    """Entry point"""
    logging.info("Starting countIT")
    # Set config defaults
    scan_time = 1200
    max_rssi = -70
    adapter = "wlan1"
    upload_frequency = "daily"

    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    config_file = "config.json"
    config = os.path.join(script_dir, config_file)

    # Parse config
    with open(config, 'r') as c_file:
        logging.info("Parsing config file")
        config = json.load(c_file)
        if "scan_time" in config:
            scan_time = config["scan_time"]
        if "max_rssi" in config:
            max_rssi = config["max_rssi"]
        if not("device_id" in config and "customer" in config and "env" in config):
            logging.error("Error parsing config: missing \"customer\", \"env\" or \"device_id\"")
            print "You MUST define \"customer\", \"env\" and \"device_id\" value in config.json"
            sys.exit(1)
        else:
            device_id = config["device_id"]
            customer = config["customer"]
            env = config["env"]
            out_directory = customer+"/"+env+"/"+device_id
            folder_name = os.path.join(script_dir, out_directory)
        if "upload_frequency" in config:
            upload_frequency = config["upload_frequency"]
        print "Config:"
        print "\tscan period: {}".format(scan_time)
        print "\tmax tx power: {}".format(max_rssi)
        print "\tcontainer folder: {}".format(folder_name)
        print "\tupload frequency: {}".format(upload_frequency)

        logging.info(
            """Config:
                customer: %s,
                environment: %s,
                device id: %s,
                scan period: %i,
                max tx power: %f,
                upload frequency: %s
            """, customer, env, device_id, scan_time, max_rssi, upload_frequency
            )

        # Define jobs
        schedule_upload_jobs(script_dir, upload_frequency)

        # Infinite scan
        while True:
            adapter = scan(adapter, scan_time, max_rssi, folder_name, device_id)

def schedule_upload_jobs(directory, upload_frequency):
    """Schedules cronjobs"""
    logging.info("Scheduling task via cronjobs")
    cron = CronTab(user="pi")

    uploader_path = "upload_files.py"
    command = os.path.join(directory, uploader_path)

    # Remove existing identical commands
    jobs = cron.find_command(command)
    for job in jobs:
        cron.remove(job)

    new_job = cron.new(command=command)
    reboot_job = cron.new(command=command)

    # Set cron default (on every reboot and everyday/midnight)
    reboot_job.every_reboot()
    new_job.day.every(1)

    # Set cron based on config file
    if upload_frequency == "hourly":
        # every hour
        new_job.every(1).hours()
    elif upload_frequency == "daily":
        # everyday at midnight
        new_job.every(1).day()
    elif upload_frequency == "weekly":
        # every Sunday at midnight
        new_job.dow.on('SUN')
    elif upload_frequency == "monthly":
        # every 1st of month at midnight
        new_job.every(1).month()
    cron.write()


def scan(adapter, scantime, max_power, outfolder, device_id):
    """Launch tshark scan"""
    logging.info("Starting a new scan")
    from_time = time.strftime('%Y-%m-%d %H:%M:%S %z')
    try:
        tshark = which("tshark")
    except OSError as err:
        logging.error("Error starting scan: %s", err.args)
        print "tshark not found, install using\n\napt-get install tshark\n"
        sys.exit(1)

    # If, for some reason, the adapter name is empty, quit with error
    if not adapter:
        logging.error("Error starting scan: %s adapter not found", adapter)
        print "%s adapter not found"%(adapter)
        sys.exit(1)

    print("Using %s adapter and scanning for %s seconds..." %
          (adapter, scantime))

    # Start timer
    thread = threading.Thread(target=show_timer, args=(scantime,))
    thread.daemon = True
    thread.start()

    # Scan with tshark
    command = [tshark, '-I', '-i', adapter, '-a',
               'duration:' + str(scantime), '-w', '/tmp/tshark-temp']

    _, _ = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()

    analysis_thread = threading.Thread(
        target=parse_scan_result, args=[device_id, max_power, from_time, outfolder]
    )
    analysis_thread.start()
    #parse_scan_result(tshark, device_id, max_power, from_time, outfolder)
    return adapter

def parse_scan_result(device_id, max_power, from_time, outfolder):
    """Parse tshark output"""

    # Read tshark output
    command = [
        which("tshark"), '-r',
        '/tmp/tshark-temp', '-T',
        'fields', '-e',
        'wlan.sa', '-e',
        'wlan.bssid', '-e',
        'radiotap.dbm_antsignal'
    ]

    output, _ = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()

    to_time = time.strftime('%Y-%m-%d %H:%M:%S %z')

    found_macs = parse_macs(output)

    if not found_macs:
        logging.warning("Found no signals, are you sure the adapter supports monitor mode?")
        print "Found no signals, are you sure adapter supports monitor mode?"
        return

    for key, value in found_macs.items():
        found_macs[key] = float(sum(value)) / float(len(value))

    detections = []
    for mac in found_macs:
        if found_macs[mac] > max_power:
            detections.append({'rssi': found_macs[mac], 'mac': mac})
        # TO ENABLE sorting by rssi value, uncomment the following line
        # detections.sort(key=lambda x: x['rssi'], reverse=True)

    if not detections:
        print "No one around (not even you!)."
    elif len(detections) == 1:
        print "No one around, but you."
    else:
        print "There are about %d people around." % len(detections)

    # Create log file with count and found devices
    if outfolder:
        if not os.path.exists(outfolder):
            os.makedirs(outfolder)
        with open(outfolder+'/'+time.strftime('%Y-%m-%d_%H:%M:%S'), 'w') as dump_file:
            data_dump = {
                'device_id': device_id, 'from': from_time, 'to': to_time, 'devices': detections
            }
            dump_file.write(json.dumps(data_dump) + "\n")

    # Remove tmp tshark output
    os.remove('/tmp/tshark-temp')

def parse_macs(output):
    """Parse tshark output and return a dict"""
    found_macs = {}
    for line in output.decode('utf-8').split('\n'):
        if line.strip() == '':
            continue
        mac = line.split()[0].strip().split(',')[0]
        dats = line.split()
        if len(dats) == 3:
            if ':' not in dats[0] or len(dats) != 3:
                continue
            if mac not in found_macs:
                found_macs[mac] = []
            dats_2_split = dats[2].split(',')
            if len(dats_2_split) > 1:
                rssi = float(dats_2_split[0]) / 2 + float(dats_2_split[1]) / 2
            else:
                rssi = float(dats_2_split[0])
            found_macs[mac].append(rssi)
    return found_macs

def show_timer(timeleft):
    """Shows a countdown timer"""
    total = int(timeleft) * 10
    for i in range(total):
        sys.stdout.write('\r')
        # the exact output you're looking for:
        timeleft_string = '%ds left' % int((total - i + 1) / 10)
        if (total - i + 1) > 600:
            timeleft_string = '%dmin %ds left' % (
                int((total - i + 1) / 600), int((total - i + 1) / 10 % 60))
        sys.stdout.write("[%-50s] %d%% %15s" %
                         ('=' * int(50.5 * i / total), 101 * i / total, timeleft_string))
        sys.stdout.flush()
        time.sleep(0.1)
    print ""

def which(program):
    """Determines whether program exists"""
    def is_exe(fpath):
        """Deteermines if program is executable"""
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    raise OSError('No program %s found'%program)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Program killed by keyboard interruption")
        print "\nKilled!"
        try:
            sys.exit(0)
        except SystemExit:
            traceback.print_exc(file=sys.stdout)
            sys.exit()
