import os

contract_address = '0x93D2736107428690F25E4A912F5dfaaC2C53e7da'

command_to_delete = f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website/cronjob_scripts/cron_update_info_paywac.py {contract_address} > /home/andrea/logs/cron.log 2>&1'

os.system(f"crontab -u andrea -l | grep -v '{command_to_delete}'  | crontab -u andrea -")