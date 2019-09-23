# this script will be triggered when an event of the paywac contract is identified by the event catch method
# in this script we will update all the values in the Contracts_info table for the given contract
from web3 import Web3, IPCProvider
from web3.middleware import geth_poa_middleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, create_engine, Boolean, DateTime
import time
from datetime import datetime
import json
import os

# this is the method that will be called in the cronjob
def update_contract_info_cron(contract_addr):
    try:
        Base = declarative_base()

        class Contracts(Base):
            __tablename__ = 'contracts'
            id = Column(Integer, primary_key=True)
            uuid = Column(String)
            name = Column(String)
            title = Column(String)
            owner = Column(String)
            contract_address = Column(String)
            seller_address = Column(String)
            contract_time = Column(Integer)
            shipping_eta = Column(Integer)
            item_price = Column(Float)
            shipping_price = Column(Float)
            status = Column(Integer)
            request_created = Column(DateTime)
            deployed_date = Column(DateTime)

        class Contracts_info(Base):
            __tablename__ = 'contracts_info'
            id = Column(Integer, primary_key=True)
            contract_address = Column(String)
            contract_start = Column(Integer)
            contract_end = Column(Integer)
            time_item_delivered = Column(Integer)
            has_buyer_paid = Column(Boolean)
            paid_ammount = Column(Float)
            refounded = Column(Boolean)
            ranking = Column(Integer)

        # create database session
        # TODO make it read from an external json
        uri = 'postgres+psycopg2://postgres:MyPassword@localhost:5432/paywac'

        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()

        current_contract = session.query(Contracts).filter_by(contract_address = contract_addr).first()

        # open the contract json file
        with open('/home/andrea/Desktop/paywac_website/paywac/static/contracts_code/build/paywac.json') as json_file:
            data = json.load(json_file)

        address = contract_addr

        abi = data['abi']

        bytecode = data['bytecode']

        # establish connection with testnet
        w3 = Web3(IPCProvider('/home/andrea/.ethereum/rinkeby/geth.ipc'))

        w3.middleware_stack.inject(geth_poa_middleware, layer=0)

        Contract = w3.eth.contract(address=address, abi=abi)

        contract_start = datetime.fromtimestamp(Contract.functions.contractStart().call())
        contract_end = datetime.fromtimestamp(Contract.functions.contractEnd().call())
        time_item_delivered = datetime.fromtimestamp(Contract.functions.time_item_delivered().call())
        time_item_delivered_unix = Contract.functions.time_item_delivered().call()
        has_buyer_paid = Contract.functions.has_buyer_paid().call()
        # convert the paid ammount from wei to eth
        paid_ammount = float(Web3.fromWei(Contract.functions.payed_ammount().call(), 'ether'))
        refounded = Contract.functions.refounded().call()

        # check for the status of variables refounded, time_item_delivered
        # and change the status of the contract in the contract deployed_table

        #TODO maybe send a notification when the contract is modified to one of this two status
        if refounded == True or refounded == 'true' or refounded == 'True':

            current_contract.status = 4
            session.commit()
            #remove the cronjob
            command_to_delete = f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website_v02/cronjob_scripts/cron_update_info_paywac.py {contract_addr} >> /home/andrea/Desktop/paywac_website_v02/logs/cron.log_{contract_addr} 2>&1'
            os.system(f"crontab -u andrea -l | grep -v '{command_to_delete}'  | crontab -u andrea -")
        elif time_item_delivered_unix != 0 and has_buyer_paid == True:

            current_contract.status = 3
            session.commit()
            #remove the cronjob
            command_to_delete = f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website_v02/cronjob_scripts/cron_update_info_paywac.py {contract_addr} >> /home/andrea/Desktop/paywac_website_v02/logs/cron.log_{contract_addr} 2>&1'
            os.system(f"crontab -u andrea -l | grep -v '{command_to_delete}'  | crontab -u andrea -")

        elif time_item_delivered_unix == 0 and has_buyer_paid == True:
            current_contract.status = 2
            session.commit()
            # TODO here we could send a notification to the seller when the buyer has payed the item


        # build transaction and commit changes to the database
        try:
            row = session.query(Contracts_info).filter_by(contract_address=contract_addr).first()
            row.contract_start = contract_start
            row.contract_end = contract_end
            row.time_item_delivered = time_item_delivered
            row.has_buyer_paid = has_buyer_paid
            row.paid_ammount = paid_ammount
            row.refounded = refounded
            session.commit()
        except:
            row = Contracts_info(contract_address=contract_addr, contract_start=contract_start, contract_end=contract_end, time_item_delivered=time_item_delivered,\
                                    has_buyer_paid=has_buyer_paid, paid_ammount=paid_ammount, refounded=refounded, ranking=0)
            session.add(row)
            session.commit()
        
        print(str(datetime.now())+' -- terminated correctly')
    except:
        print(str(datetime.now())+' -- cannot connect to the chain, skipping this update')