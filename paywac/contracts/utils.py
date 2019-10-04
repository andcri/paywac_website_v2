from web3 import Web3, IPCProvider 
from decimal import Decimal
from paywac.models import Gas_price
import os
import json

# TODO refactor this to directly get latest price not from the table but from the website
#      table will update every 5 or 10 minutes, but when we are actually doing a transaction we call this one
# IMPORTANT: there will be a try and except, if we cannot retrieve the live gas price via a direct api
#            call we will use the value saved in the database
def get_deployment_price():
    """
    query the gas_price table and calculate the wei value to subtract to the user
    """
    table_gas_price = Gas_price.query.filter_by(id=1).first()
    # both values are expressed in gwei
    gas_price = table_gas_price.standard_gas_price

    return gas_price 

def gwei_to_wei(ammount):
    wei_amount = Decimal(ammount) * (Decimal(10) ** 9)
    return wei_amount

def gwei_to_eth(amount):
    wei_amount = Decimal(amount) * (Decimal(10) ** 9)
    eth_amount = Web3.fromWei(wei_amount,'ether')
    return eth_amount

def wei_to_eth(amount):
    eth_amount = Web3.fromWei(amount,'ether')
    return eth_amount

def deploy(deployer, seller, oracle, contract_time, contract_shipping_eta, item_price, shipping_price, gas_price):

    deployer = Web3.toChecksumAddress(deployer)
    seller = Web3.toChecksumAddress(seller)
    oracle = Web3.toChecksumAddress(oracle)

    # convert item price and shipping price to wei
    item_price = Web3.toWei(item_price, 'ether')
    shipping_price = Web3.toWei(shipping_price, 'ether')

    # load json file
    with open('paywac/static/contracts_code/build/paywac.json') as json_file:
        data = json.load(json_file)

    abi = data['abi']

    bytecode = data['bytecode']

    # connect to the rinkeby endpoint
    w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # set the account that will deploy the contract
    from_account = "0xb773c20a88c56f4458ae6ddb3e542ac60e4b9f8f"
    # load password json file
    with open('paywac/static/rinkeby_data/rinkeby_passwords.json') as pwd_file:
        password_data = json.load(pwd_file)

    password = password_data[from_account]

    with open('/home/andrea/.ethereum/rinkeby/keystore/UTC--2019-09-03T12-19-47.104595283Z--b773c20a88c56f4458ae6ddb3e542ac60e4b9f8f') as keyfile:
        encrypted_key = keyfile.read()
        private_key = w3.eth.account.decrypt(encrypted_key, password)

    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(from_account))

    # build transaction
    transaction = Contract.constructor(deployer, seller, oracle, contract_time, contract_shipping_eta, item_price, shipping_price)\
                .buildTransaction({'from': Web3.toChecksumAddress(from_account),\
                                    'gas' : 2000000,\
                                    'gasPrice' : w3.toWei(gas_price, 'gwei'),\
                                    'nonce' : nonce })

    signed = w3.eth.account.signTransaction(transaction, private_key)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print(tx_receipt)
    return tx_receipt


def deploy_erc20(buyer, seller, oracle, token_address, contract_time, contract_shipping_eta, shipping_price, item_price, gas_price):
    buyer = Web3.toChecksumAddress(buyer)
    seller = Web3.toChecksumAddress(seller)
    oracle = Web3.toChecksumAddress(oracle)
    token_address = Web3.toChecksumAddress(token_address)

    # Right now this is the conversion needed to use with Pcoin
    # TODO convert price to proper USDT format, need to research that
    item_price = int(item_price * 1000)
    shipping_price = int(shipping_price * 1000)

    # load json file
    with open('paywac/static/contracts_code/build/paywac_erc20.json') as json_file:
        data = json.load(json_file)

    abi = data['abi']

    bytecode = data['bytecode']

    # connect to the rinkeby endpoint
    w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # set the account that will deploy the contract
    from_account = "0xb773c20a88c56f4458ae6ddb3e542ac60e4b9f8f"
    # load password json file
    with open('paywac/static/rinkeby_data/rinkeby_passwords.json') as pwd_file:
        password_data = json.load(pwd_file)

    password = password_data[from_account]

    with open('/home/andrea/.ethereum/rinkeby/keystore/UTC--2019-09-03T12-19-47.104595283Z--b773c20a88c56f4458ae6ddb3e542ac60e4b9f8f') as keyfile:
        encrypted_key = keyfile.read()
        private_key = w3.eth.account.decrypt(encrypted_key, password)

    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(from_account))

    # build transaction
    transaction = Contract.constructor(buyer, seller, oracle, token_address, contract_time, contract_shipping_eta, shipping_price, item_price)\
                .buildTransaction({'from': Web3.toChecksumAddress(from_account),\
                                    'gas' : 2000000,\
                                    'gasPrice' : w3.toWei(gas_price, 'gwei'),\
                                    'nonce' : nonce })

    signed = w3.eth.account.signTransaction(transaction, private_key)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print(tx_receipt)
    return tx_receipt


def secondsToText(secs):
    days = secs//86400
    hours = (secs - days*86400)//3600
    minutes = (secs - days*86400 - hours*3600)//60
    seconds = secs - days*86400 - hours*3600 - minutes*60
    result = ("{} days ".format(days) if days else "") + \
    ("{} hours ".format(hours) if hours else "") + \
    ("{} minutes ".format(minutes) if minutes else "") + \
    ("{} seconds ".format(seconds) if seconds else "")
    return result