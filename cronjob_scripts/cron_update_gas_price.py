"""
Read from an api the current standard gas price and update the value in the database
"""

from web3 import Web3, IPCProvider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine
import time
import json
import requests

Base = declarative_base()

class Gas_price(Base):
    __tablename__='gas_price'
    id = Column(Integer, primary_key=True)
    standard_gas_price = Column(Float)
    contract_cost = Column(Integer)

uri = 'postgres+psycopg2://postgres:MyPassword@localhost:5432/paywac'

engine = create_engine(uri)
Session = sessionmaker(bind=engine)
session = Session()

try:
    URL = "https://ethgasstation.info/json/ethgasAPI.json"

    request = requests.get(url=URL)
    data = request.json()
    avg_price = data['average']/10
    
except:
    print(str(datetime.now())+' -- error retrieving data')
    # TODO log and send email

gas_price = session.query(Gas_price).filter_by(id=1).first()
gas_price.standard_gas_price = avg_price
session.add(gas_price)
session.commit()
session.close()
print(str(datetime.now())+' -- price updated')