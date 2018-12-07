#!/usr/bin/python
"""Setup: schedules and runs countit and setups logs"""
import os

from crontab import CronTab

cron = CronTab(user="pi")
command = os.getcwd()+"/countit.py"
job = cron.new(command=command, comment="run countIT at boot")
job.every_reboot()
cron.write()

open("/var/log/countit.log", 'a').close()
os.chmod("/var/log/countit.log", 0o666)

os.system(command)
