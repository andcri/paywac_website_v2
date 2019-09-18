#!/home/andrea/anaconda3/envs/vyper/bin/python -u

from web3 import Web3, IPCProvider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine
import time
import json

# create connection to the database
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    image_file = Column(String)
    password = Column(String)
    wac_credits = Column(Integer)
    receiving_address = Column(String)
    recharge_address = Column(String)

# TODO make it read from an external json
uri = 'postgres+psycopg2://postgres:MyPassword@localhost:5432/paywac'

engine = create_engine(uri)
Session = sessionmaker(bind=engine)
session = Session()

contract_address = '0xd65Df0270595F59aD0CCeAdCD4801FDE9b08EbE3'

# establish connection with testnet
w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

# load json file and collect contract abi and bytecode
with open('/home/andrea/Desktop/paywac_website/paywac/static/contracts_code/build/paywac.json') as json_file:
    data = json.load(json_file)

abi = data['abi']

Contract = w3.eth.contract(address=contract_address, abi=abi)
event_filter = Contract.events.event_add_founds.createFilter(fromBlock=1)

while True:
    identified_event = event_filter.get_new_entries()
    print(identified_event)
    print(len(identified_event))
    for event in identified_event:
        print('inside loop')
        # check the ammount and add it to the corrispondent user
        user_address = event.get('args').get('_from')
        print(user_address)
        value = event.get('args').get('_value')
        # insert into paywac database, user table the value using as a reference the address
        # update the values in the table
        # retrieve the correct row
        try:
            user = session.query(User).filter_by(recharge_address=user_address).first()
            user.wac_credits += value
            session.add(user)
            session.commit()
            print('added to database')
        except:
            # TODO add logs
            print('cannot add to database')

    time.sleep(60)