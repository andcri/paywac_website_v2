"""
This file is called every 30 minutes by a cronjob to update the values inside the contract if any event(payment, delivery or refound)
happened.
"""

from web3 import Web3, IPCProvider
import sys
import time
import json
from update_deployed_contracts_data import update_contract_info, update_contract_status

# contract_address = '0x93D2736107428690F25E4A912F5dfaaC2C53e7da'
contract_address = sys.argv[1]

# establish connection with testnet
w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

# load json file and collect contract abi and bytecode
with open('/home/andrea/Desktop/paywac_website/paywac/static/contracts_code/build/paywac.json') as json_file:
    data = json.load(json_file)

abi = data['abi']

Contract = w3.eth.contract(address=contract_address, abi=abi)
event_filter = Contract.events.Notification.createFilter(fromBlock=1)


identified_event = event_filter.get_new_entries()
print(identified_event)
print(len(identified_event))
for event in identified_event:
    # retrive info about the event
    message = event.get('args').get('_message')
    block_number = event.get('args').get('blockNumber')
    # call the update_deployed_contract_data function passing the contract address as an argument
    update_contract_info(contract_address)
    # check if the message is 'refound' or 'delivered'
    if message == 'delivered':
        update_contract_status(contract_address, 2)
    elif message == 'refound':
        update_contract_status(contract_address, 3)
    else:
        pass