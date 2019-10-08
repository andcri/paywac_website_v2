"""
contains all the tables that we will access in the shipping_tracker module
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine, DateTime
import json

Base = declarative_base()

class Shipping_info(Base):
    __tablename__ = 'shipping_info'
    id = Column(Integer, primary_key=True)
    uuid = Column(String())
    seller_email = Column(String())
    buyer_email = Column(String())
    buyer_name = Column(String())
    buyer_surname = Column(String())
    city = Column(String())
    street = Column(String())
    country = Column(String())
    state = Column(String())
    postal_code = Column(String())

class Shipping_tracking(Base):
    __tablename__ = 'shipping_tracking'
    id = Column(Integer, primary_key=True)
    uuid = Column(String())
    shipper = Column(String())
    tracking_number = Column(String())
    status = Column(String())
    last_location = Column(String())

class Gas_price(Base):
    __tablename__ = 'gas_price'
    id = Column(Integer, primary_key=True)
    standard_gas_price = Column(Float)
    contract_cost = Column(Integer)

class Contracts(Base):
    __tablename__ = 'contracts'
    id = Column(Integer, primary_key=True)
    uuid = Column(String)
    name = Column(String)
    title = Column(String)
    owner = Column(String)
    contract_address = Column(String)
    seller_address = Column(String)
    oracle_address = Column(Integer)
    deployer_address = Column(Integer)
    contract_time = Column(Integer)
    shipping_eta = Column(Integer)
    item_price = Column(Float)
    shipping_price = Column(Float)
    status = Column(Integer)
    request_created = Column(DateTime)
    deployed_date = Column(DateTime)
    buyer_address = Column(String)

class Oracle(Base):
    __tablename__="oracle"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    active = Column(Integer)