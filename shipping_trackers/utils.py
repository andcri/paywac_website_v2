"""
this is the script that will be called once the shipping has reached the destination
"""
from tables import Contracts, Oracle
from web3 import Web3, IPCProvider
from web3.middleware import geth_poa_middleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine, DateTime
import json
import glob


def oracle_trigger(uuid):
    # create database session
    uri = 'postgres+psycopg2://postgres:MyPassword@localhost:5432/paywac'

    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()

    contract_row = session.query(Contracts).filter_by(uuid=uuid).first()
    contract_address = contract_row.contract_address
    contract_type = 0 if contract_row.buyer_address == "0x0000000000000000000000000000000000000000" else 1

    oracle = session.query(Oracle).filter_by(id=contract_row.oracle_address).first()
    oracle_is_active = oracle.active
    # TODO add check that the address is still active, if not send a notification via mail to a human
    oracle_address = oracle.address

    return submit_transaction(contract_address, oracle_address, contract_type)

def submit_transaction(contract_address, oracle_address, contract_type):
    
    if contract_type == 0:
        with open('/home/andrea/Desktop/paywac_website_v02/paywac/static/contracts_code/build/paywac.json') as json_file:
            data = json.loadload(json_file)
    else:
        with open('/home/andrea/Desktop/paywac_website_v02/paywac/static/contracts_code/build/paywac_erc20.json') as json_file:
            data = json.load(json_file)
    
    abi = data['abi']
    bytecode = data['bytecode']

    w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)

    gas_price = round(w3.eth.gasPrice /1000000000)
    from_account = oracle_address

    with open('/home/andrea/Desktop/paywac_website_v02/paywac/static/rinkeby_data/rinkeby_passwords.json') as pwd_file:
        password_data = json.load(pwd_file)
    password = password_data[from_account]

    # find via regex the file that has the oracle address inside the filename
    encrypted_key = get_secret_file(from_account)
    print(encrypted_key)
    private_key = w3.eth.account.decrypt(encrypted_key, password)
    
    
    from_account = Web3.toChecksumAddress(from_account)
    Contract = w3.eth.contract(address=contract_address, abi=abi)
    nonce = w3.eth.getTransactionCount(from_account)

    txn = Contract.functions.package_received().buildTransaction({
            'from' :  from_account,
            'gas' : 100000,
            'gasPrice' :  w3.toWei(20, 'gwei'), #we will use the variable gas_price later for now we hardcode 20
            'nonce' : nonce
            })
    
    signed_txn = w3.eth.account.signTransaction(txn, private_key)
    signed_txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    receipt = w3.eth.waitForTransactionReceipt(signed_txn_hash)

    return receipt


def get_secret_file(oracle_address):
    
    path = "/home/andrea/.ethereum/rinkeby/keystore" 

    files = [f for f in glob.glob(path + "/*", recursive=True)]

    for file in files:
        if oracle_address[2:] in file:
            with open(file) as keyfile:
                encrypted_key = keyfile.read()
            
    return encrypted_key