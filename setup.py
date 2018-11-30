#!/usr/bin/python

import os

from crontab import CronTab

cron = CronTab(user="pi")
command = os.getcwd()+"/countit.py"
job = cron.new(command=command, comment="run countIT at boot")
job.every_reboot()
cron.write()

os.system(command)