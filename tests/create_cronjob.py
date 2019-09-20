from crontab import CronTab

contract_address = "0x5a2dE45686F5a838ccE0db862adbE218eC946578"

cron = CronTab(user='andrea')
job = cron.new(command=f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website_v02/cronjob_scripts/cron_update_info_paywac.py {contract_address} > /home/andrea/Desktop/paywac_website_v02/logs/cron.log 2>&1')
job.minute.every(1)

cron.write()