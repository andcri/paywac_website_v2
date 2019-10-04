"""
script that will be a cronjob, called with the contract address at argv[1] by the deployer in the contract creation phase
it will call the function update_contract_erc20_info_cron of the file update_deployed_contracts_data
"""
import sys
from update_deployed_contracts_data import update_contract_erc20_info_cron

# get the contract address from the argument
contract_address = sys.argv[1]

# call the method
update_contract_erc20_info_cron(contract_address)