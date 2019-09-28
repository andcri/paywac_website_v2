from web3 import Web3, IPCProvider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine
from datetime import datetime
import json

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

contract_address = '0xFd7bA9c21397B564B7b7277fA930e57eA4A1B449'

try:

    # establish connection with testnet
    w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

    # load json file and collect contract abi and bytecode
    with open('/home/andrea/Desktop/paywac_website_v02/paywac/static/contracts_code/build/add_founds.json') as json_file:
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

        try:
            user = session.query(User).filter_by(recharge_address=user_address).first()
            user.wac_credits += value
            session.add(user)
            print(str(datetime.now())+' -- added to database')
        except:
            # TODO add logs detailing the user address, the value and the blockHeight
            print(str(datetime.now())+' -- cannot add to database')

    # update last_blockHeight with the latest recorded blockHeight
    try:
        add_founds.last_blockHeight = blockHeight + 1
        session.add(add_founds)
        session.commit()
        session.close()
    except:
        print(str(datetime.now())+' -- nothing to update')
        session.close()
        
except:
    print(str(datetime.now())+' -- cannot connect to the chain, skipping this update')
    session.close()