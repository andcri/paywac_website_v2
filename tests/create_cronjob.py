from crontab import CronTab

contract_address = "0xaDd4bF505bf0c78ccfcBF4D874920C348ffCebd3"

cron = CronTab(user='andrea')
job = cron.new(command=f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website_v02/cronjob_scripts/cron_update_info_paywac.py {contract_address} >> /home/andrea/Desktop/paywac_website_v02/logs/cron.log_{contract_address} 2>&1')
job.minute.every(15)

cron.write()