"""
simulate a tracked contract with fake json data
this will be called by a cronjob every n hours to check the shipping progress
it will update the shipping_tracking table values with the obtained ones calling the api
"""
import json
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine, Boolean, DateTime
import time
from datetime import datetime
from fuzzywuzzy import fuzz

# 1 -- initialization of the tables

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

tracking_number=sys.argv[1]
tracking_number='fdgsdfgs'


# TODO make it read from an external json
uri = 'postgres+psycopg2://postgres:MyPassword@localhost:5432/paywac'

engine = create_engine(uri)
Session = sessionmaker(bind=engine)
session = Session()

shipping_tracking = session.query(Shipping_tracking).filter_by(tracking_number=tracking_number).first()
shipping_info = session.query(Shipping_info).filter_by(uuid=shipping_tracking.uuid).first()

# 2 -- start logic

# TODO (with the real thing)call the dhl api and check for an answer, if an answer is not being received yet dont do anything and wait for next cronjob iteration
# use quit() if this condition is sadisfied

# check if the status is pending in the shipping_tracking table, if yes:

with open('dhl_response.json') as json_file:
    data = json.load(json_file)

shipment = data['shipments'][0]

if shipping_tracking.status == 'pending':

    table_street =  shipping_info.street
    table_city = shipping_info.city
    table_country = shipping_info.country
    table_postal_code = shipping_info.postal_code
    # compare the delivery details from the table and the ones from dhl and check for a match
    # here i retrive the data from the api, the json in this case
    api_destination_data = shipment['destination']['address']

    api_postal_code = api_destination_data['postalCode']
    api_address = api_destination_data['addressLocality'] # composed by address and the city of the delivery format: [address, CITY]
    # check if the address given matches the one retrieved from the api
    # build the table address in a similar format
    table_address = table_street+', '+table_city
    # check similarity between addresses
    ratio_street_address = fuzz.token_set_ratio(api_address, table_address)
    ratio_postal_code = fuzz.token_set_ratio(api_postal_code, table_postal_code)

    # if the ratio is sathisfing we proceed to change the status from pending to in transit, else we send this to a human to make a more detailed check.
    if ratio_street_address >= 95 and ratio_postal_code >= 99:
        # change status to 'in transit'
        print("changing status")
        shipping_tracking.status = "in transit"
        session.commit()
    else:
        print("addresses too different, a human needs to check them")
        # send to support human to check
        pass

elif shipping_tracking.status != 'pending':
    print("here")
# start with the check from the api about the status and the location and update the shipping_tracking table accordingly
# when we reach the status delivered, we check for a signature
# if the signature and the proof of delivery are present we unlock the founds and the seller will get his money

    shipment = data['shipments'][0]

    # get shipment status and check for delivered word, if found than we check for a signature in ['details']['proofOfDelivery']['signed'] and add to the shipping tracking this data
    # if not delivered word is found we get the current word and compare it with the one in the database,
    # if they are different we can update the status in the database
    # also if not delivered wird is found we will collect more data about the shipping in order to display it to the user

    shipment_status = shipment['status']['status']
    
# print(shipment.keys())
# # print(shipment['events'])
# print(shipment['destination'])
# # print(shipment['status'])
# # from the status i can extract the status key
# status = shipment['status']['status']
# if status == 'DELIVERED':
#     print(status)
# print(shipment['details']['proofOfDelivery']['signed'])