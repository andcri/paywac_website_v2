from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from paywac import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    wac_credits = db.Column(db.Integer, default=0)
    receiving_address = db.Column(db.String(), default='')
    recharge_address = db.Column(db.String(), unique=True, nullable=True)
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
        
class Contracts_deployed(db.Model, UserMixin):
    # pk for the table
    id = db.Column(db.Integer, primary_key=True)
    # uuid for the request
    request_id = db.Column(db.String(), unique=True, nullable=False)
    # paywac user that created the contract
    contract_creator_user = db.Column(db.String(), nullable=False)
    # address of the deployed contract
    contract_address = db.Column(db.String(), nullable=False)
    # name of the contract used (default paywac)
    contract_name = db.Column(db.String(), nullable=False)
    # variables used to create the contract
    deployer = db.Column(db.String(), nullable=False)
    seller = db.Column(db.String(), nullable=False)
    buyer = db.Column(db.String(), nullable=False)
    oracle = db.Column(db.String(), nullable=False)
    contract_time = db.Column(db.Integer, nullable=False)
    contract_delivery_eta = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float, nullable=False)
    # status of the request(contract is online = 1, contract request created but contract is not online = 0)
    status = db.Column(db.Integer, nullable=False)
    # email to notify the other party
    email = db.Column(db.String(200), nullable=True)

    def __repr__():
        return f"Payment_promess('{self.id}', '{self.request_id}')"

# this contains all the contracts info that the user can deploy from the website for now it will contain just the info about the paywac contract
class Contracts_types(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    contract_name = db.Column(db.String(), nullable=False)
    source_path = db.Column(db.String(), nullable=False)
    json_path = db.Column(db.String(), nullable=False)
    gas_needed_for_deployment = db.Column(db.Integer, nullable=False)

    def __repr__():
        return f"Contracts_types('{self.id}', '{self.contract_name}', '{self.gas_needed_for_deployment}')"
    
# this contains the info about the status of a specific contract, identified by his contract address
class Contracts_info(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    contract_address = db.Column(db.String(), unique=True, nullable=False)
    contract_start = db.Column(db.DateTime, nullable=False)
    contract_end = db.Column(db.DateTime, nullable=False)
    time_item_delivered = db.Column(db.DateTime, nullable=False)
    has_buyer_paid = db.Column(db.Boolean, nullable=False)
    paid_ammount = db.Column(db.Float, nullable=False)
    refounded = db.Column(db.Boolean, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)

    def __repr__():
        return f"Contract_info('{self.id}', '{self.name}', '{self.address}, '{self.active}')"

class Deployer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    active = db.Column(db.Integer, nullable=False)

    def __repr__():
        return f"Deployer('{self.id}', '{self.name}', '{self.address}, '{self.active}')"

class Oracle(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    active = db.Column(db.Integer, nullable=False)

    def __repr__():
        return f"Oracle('{self.id}', '{self.name}', '{self.address}, '{self.active}')"

# the details that are embedded in the button
class Button_data(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(), unique=True)
    # the user that has created this button
    creator_mail = db.Column(db.String(), nullable=False)
    # the link to the insertion, this can be ommited
    name = db.Column(db.String(), nullable=True)
    title = db.Column(db.String(), nullable=False)
    seller_address = db.Column(db.String(), nullable=False)
    contract_time = db.Column(db.Integer, nullable=False)
    shipping_eta = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float, nullable=False)
    shipping_price = db.Column(db.Float, nullable=False)
    clicked = db.Column(db.Integer, nullable=False)
    button_code = db.Column(db.String(), nullable=False)


    def __repr__():
        return f"Button_data('{self.id}', '{self.uuid}', '{self.title}, '{self.seller_address}')"

# the shipping info for each request
class Shipping_info(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(), unique=True)
    seller_email = db.Column(db.String(), nullable=False)
    buyer_email = db.Column(db.String(), nullable=True)
    buyer_name = db.Column(db.String(), nullable=False)
    buyer_surname = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(), nullable=False)
    street = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)
    state = db.Column(db.String(), nullable=False)
    postal_code = db.Column(db.String(), nullable=False)

    def __repr__():
        return f"Button_data('{self.id}', '{self.uuid}', '{self.seller_mail}, '{self.street}')"


# the contract info for each request
# this will contain all the necessary info to deploy the contract
# and a status wich indicates if the seller has deployed or not the 
# contract
class Contracts(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(), unique=True)
    name = db.Column(db.String(), nullable=True)
    title = db.Column(db.String(), nullable=False)
    owner = db.Column(db.String(), nullable=False)
    # here will be setted the contract address, the string will be empty and will be update to the real value once the contract will be deployed
    contract_address = db.Column(db.String(), nullable=False, default='')
    seller_address = db.Column(db.String(), nullable=False)
    contract_time = db.Column(db.Integer, nullable=False)
    shipping_eta = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float, nullable=False)
    shipping_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    request_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # this will be update once the contract will be actually deployed on the network
    deployed_date = db.Column(db.DateTime, nullable=True)
    tracked = db.Column(db.Integer, nullable=True)

    def __repr__():
        return f"Contracts('{self.id}', '{self.uuid}', '{self.title}, '{self.status}')"

class Shipping_tracking(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(), unique=True)
    shipper = db.Column(db.String(), nullable=False)
    tracking_number = db.Column(db.String(), nullable=False)
    status = db.Column(db.String(), nullable=False)
    last_location = db.Column(db.String(), nullable=False)

    def __repr__():
        return f"Shipping_tracking('{self.id}', '{self.uuid}', '{self.status}' , '{self.tracking_number})"