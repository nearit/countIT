import getopt
import json
import netifaces
import os
import platform
import subprocess
import sys
import threading
import time
import traceback
import uuid

from crontab import CronTab
from oui import oui
from pick import pick

def main():
    # Set config defaults
    scan_time = 1200
    max_rssi = -70
    adapter = "wlan1"
    upload_frequency = "daily"

    # Parse config
    with open('config.json', 'r') as f:
        config = json.load(f)
        if "scan_time" in config:
            scan_time = config["scan_time"]
        if "max_rssi" in config:
            max_rssi = config["max_rssi"]
        if not("id" in config and "customer" in config and "env" in config):
            print "You MUST define \"customer\", \"env\" and \"id\" value in config.json"
            sys.exit(1)
        else:
            folder_name = config["customer"]+"/"+config["env"]+"/"+config["id"]
        if "upload_frequency" in config:
            upload_frequency = config["upload_frequency"]
        print("Config:")
        print("\tscan period: {}".format(scan_time))
        print("\tmax tx power: {}".format(max_rssi))
        print("\tcontainer folder: {}".format(folder_name))
        print("\tupload frequency: {}".format(upload_frequency))

        # Define jobs
        schedule_upload_jobs(upload_frequency)

        # Infinite scan
        while True:
            adapter = scan(adapter, scan_time, max_rssi, folder_name)

def schedule_upload_jobs(upload_frequency):
    cron = CronTab(user="pi")
    path = os.getcwd()+"/upload_files.py"
    command = "sleep 60 && python "+path

    # Remove existing identical commands
    jobs = cron.find_command(command)
    for job in jobs:
        cron.remove(job)

    new_job = cron.new(command=command)
    reboot_job = cron.new(command=command)

    # Set cron default (on every reboot and everyday/midnight)
    reboot_job.every_reboot()
    new_job.every(1).day()

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


def scan(adapter, scantime, maxpower, outfolder):
    try:
        tshark = which("tshark")
    except:
        print('tshark not found, install using\n\napt-get install tshark\n')
        return
    
    # If, for some reason, the adapter name is empty, show a picker
    if len(adapter) == 0:
        title = 'Please choose the adapter you want to use: '
        adapter, index = pick(netifaces.interfaces(), title)

    print("Using %s adapter and scanning for %s seconds..." %
          (adapter, scantime))

    # Start timer
    t1 = threading.Thread(target=showTimer, args=(scantime,))
    t1.daemon = True
    t1.start()

    # Scan with tshark
    command = [tshark, '-I', '-i', adapter, '-a',
               'duration:' + str(scantime), '-w', '/tmp/tshark-temp']
    
    run_tshark = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, nothing = run_tshark.communicate()

    # Read tshark output
    command = [
        tshark, '-r',
        '/tmp/tshark-temp', '-T',
        'fields', '-e',
        'wlan.sa', '-e',
        'wlan.bssid', '-e',
        'radiotap.dbm_antsignal'
    ]

    run_tshark = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, nothing = run_tshark.communicate()

    foundMacs = {}
    for line in output.decode('utf-8').split('\n'):
        if line.strip() == '':
            continue
        mac = line.split()[0].strip().split(',')[0]
        dats = line.split()
        if len(dats) == 3:
            if ':' not in dats[0] or len(dats) != 3:
                continue
            if mac not in foundMacs:
                foundMacs[mac] = []
            dats_2_split = dats[2].split(',')
            if len(dats_2_split) > 1:
                rssi = float(dats_2_split[0]) / 2 + float(dats_2_split[1]) / 2
            else:
                rssi = float(dats_2_split[0])
            foundMacs[mac].append(rssi)

    if not foundMacs:
        print("Found no signals, are you sure %s supports monitor mode?" % adapter)
        return

    for key, value in foundMacs.items():
        foundMacs[key] = float(sum(value)) / float(len(value))

    cellphone_people = []
    for mac in foundMacs:
        oui_id = 'Not in OUI'
        if mac[:8] in oui:
            oui_id = oui[mac[:8]]
        if foundMacs[mac] > maxpower:
            cellphone_people.append({'Manufacturer': oui_id, 'rssi': foundMacs[mac], 'mac': mac})
        cellphone_people.sort(key=lambda x: x['rssi'], reverse=True)

    num_people = len(cellphone_people)

    if num_people == 0:
        print("No one around (not even you!).")
    elif num_people == 1:
        print("No one around, but you.")
    else:
        print("There are about %d people around." % num_people)

    # Create log file with count and found devices
    if outfolder:
        if not(os.path.exists(outfolder)):
            os.makedirs(outfolder)
        with open(outfolder+'/'+time.strftime('%Y-%m-%d_%H:%M:%S'), 'w') as f:
            data_dump = {'count': num_people, 'devices': cellphone_people}
            f.write(json.dumps(data_dump) + "\n")

    # Remove tmp tshark output
    os.remove('/tmp/tshark-temp')
    return adapter

def showTimer(timeleft):
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
    print("")

def which(program):
    """Determines whether program exists
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "\nKilled!"
        sys.exit()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)