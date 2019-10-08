"""
functions that will be used during the shipping tracking
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tables import Gas_price
from web3 import Web3, IPCProvider

def oracle_call(oracle_address, contract_address):
    """
    This method will be called automatically when a signature has been found and 
    the status will be "Delivered"
    Send a transaction from the valid oracle address specified in the contract creation
    and let the seller recieve his money for the successfull item delivery
    """
    # load json file and collect contract abi and bytecode
    with open('../paywac/static/contracts_code/build/paywac.json') as json_file:
        data = json.load(json_file)
    abi = data['abi']
    bytecode = data['bytecode']

    w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)

    from_account = oracle_address
    # load password json file
    with open('../paywac/static/rinkeby_data/rinkeby_passwords.json') as pwd_file:
        password_data = json.load(pwd_file)
    password = password_data[from_account]

    # decrypt the privatekey of the account using the password
    with open('/home/andrea/.ethereum/rinkeby/keystore/UTC--2019-09-09T12-24-24.166335508Z--032e15e5531f6a542fe70fd78d1bbd63497ab105') as keyfile:
        encrypted_key = keyfile.read()
        private_key = w3.eth.account.decrypt(encrypted_key, password)


    from_account = Web3.toChecksumAddress(from_account)
    Contract = w3.eth.contract(address=contract_address, abi=abi)
    nonce = w3.eth.getTransactionCount(from_account)
    gas_price = get_gas_price()
    gas_limit = 106684

    txn = Contract.functions.change_package_recieved_status().buildTransaction({
                'from' : from_account,
                'gas' : gas_limit,
                'gasPrice' : w3.toWei(gas_price, 'gwei'),
                'nonce' : nonce,
            })

    signed_txn = w3.eth.account.signTransaction(txn, private_key)
    signed_txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    receipt = w3.eth.waitForTransactionReceipt(signed_txn_hash)

    print(receipt)
    return receipt

def get_gas_price():

    uri = 'postgres+psycopg2://postgres:MyPassword@localhost:5432/paywac'
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()

    gas_price = session.query(Gas_price).filter_by(id=1).first().standard_gas_price
    session.close()

    return gas_price