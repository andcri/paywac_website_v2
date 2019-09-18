from web3 import Web3, IPCProvider 
from decimal import Decimal
import os
import json

def gas_to_eth(gas_ammount, gas_price=10):
    """
    given an ammount of gas and the price that i want to pay default=10Gwei
    it shows the price of eth that i need to send in order to deploy the contract
    """
    w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

    gas_price_wei = w3.toWei(gas_price, 'gwei')

    wei_ammount = gas_ammount * gas_price_wei

    eth_amount = w3.fromWei(wei_ammount, 'ether')

    return eth_amount

# deploy the contract to the rinkeby network
def deploy(deployer, seller, buyer, oracle, contract_time, contract_shipping_eta, item_price):

    deployer = Web3.toChecksumAddress(deployer)
    seller = Web3.toChecksumAddress(seller)
    buyer = Web3.toChecksumAddress(buyer)
    oracle = Web3.toChecksumAddress(oracle)

    # convert item price to wei
    item_price = Web3.toWei(item_price, 'ether')

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

    # calculate fee based on item price
    fee = int((item_price * 0.8) / 100)
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(from_account))
    print(nonce)

    # transaction_price_estimate = Contract.constructor(deployer, seller, buyer, oracle, contract_time, contract_shipping_eta, item_price, fee).estimateGas()
    # print(transaction_price_estimate)
    # print(Web3.toChecksumAddress(from_account))

    # build transaction
    transaction = Contract.constructor(deployer, seller, buyer, oracle, contract_time, contract_shipping_eta, item_price, fee)\
                .buildTransaction({'from': Web3.toChecksumAddress(from_account),\
                                    'gas' : 2000000,\
                                    'gasPrice' : w3.toWei('10', 'gwei'),\
                                    'nonce' : nonce })

    signed = w3.eth.account.signTransaction(transaction, private_key)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print(tx_receipt)
    return tx_receipt