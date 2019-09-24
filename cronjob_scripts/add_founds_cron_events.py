from web3 import Web3, IPCProvider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine
import time
import json

# get latest block height that we checked

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

class Add_founds(Base):
    __tablename__ = 'add_founds'
    id = Column(Integer, primary_key=True)
    last_blockHeight = Column(Integer)

uri = 'postgres+psycopg2://postgres:MyPassword@localhost:5432/paywac'

engine = create_engine(uri)
Session = sessionmaker(bind=engine)
session = Session()

add_founds = session.query(Add_founds).filter_by(id=1).first()

contract_address = '0xd65Df0270595F59aD0CCeAdCD4801FDE9b08EbE3'

# establish connection with testnet
w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

# load json file and collect contract abi and bytecode
with open('build/add_founds.json') as json_file:
    data = json.load(json_file)

abi = data['abi']

Contract = w3.eth.contract(address=contract_address, abi=abi)
event_filter = Contract.events.event_add_founds.createFilter(fromBlock=add_founds.last_blockHeight)

all_entries = event_filter.get_all_entries()

for event in all_entries:
    print(event)
    user_address = event.get('args').get('_from')
    value = event.get('args').get('_value')
    blockHeight = event.get('blockNumber')
    # insert into paywac database, user table the value using as a reference the address
    # update the values in the table
    # retrieve the correct row
    try:
        user = session.query(User).filter_by(recharge_address=user_address).first()
        user.wac_credits += value
        session.add(user)
        print('added to database')
    except:
        # TODO add logs detailing the user address, the value and the blockHeight
        print('cannot add to database')

# update last_blockHeight with the latest recorded blockHeight
try:
    add_founds.last_blockHeight = blockHeight + 1
    session.add(add_founds)
    session.commit()
    session.close()
except:
    print("nothing to update")
    session.close()