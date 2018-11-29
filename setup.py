import os

from crontab import CronTab

cron = CronTab(user="pi")
command = "sleep 60 && python "+os.getcwd()+"/main.py"
job = cron.new(command=command, comment="run countIT at boot")
job.every_reboot()
cron.write()

os.system(command)