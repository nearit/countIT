import os

from crontab import crontab

cron = CronTab(user="pi")
command = "python "+os.getcwd()+"/main.py"
job = cron.new(command=command, comment="run countIT at boot")
job.every_reboot()
cron.write()

os.system(command)