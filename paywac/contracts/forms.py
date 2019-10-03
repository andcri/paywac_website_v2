from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional

class CreateContract(FlaskForm):
    # choose contract(right now defaults to the only contract)
    # give a name to your contract
    name = StringField('Contract Name', validators=[DataRequired()])
    # address of the seller 
    seller = StringField('The Ethereum address where you want to be payed', validators=[DataRequired(), Length(min=40, max=42)])
    # address of the buyer
    buyer = StringField('The Ethereum address that will send the money to make the purchease', validators=[DataRequired(), Length(min=40, max=42)])
    # the time that the contract stay online without recieving any payment
    contract_time = SelectField('The ammount of days that the contract will stay online in accept payment status', choices=[('86400', '1 day'), ('172800', '2 days'), ('259200', '3 days'), ('345600', '4 days'), ('432000', '5 days'), ('518400', '6 days'), ('604800', '1 week')], default='259200')
    # the eta of the shipping after the package has been payed
    shipping_eta = SelectField('The eta of the shipping after the package has been payed', choices=[('86400', '1 day'), ('172800', '2 days'), ('259200', '3 days'), ('345600', '4 days'), ('432000', '5 days'), ('518400', '6 days'), ('604800', '1 week'), ('864000', '10 days'), ('1209600', '2 weeks')])
    # the price of the item
    item_price = DecimalField('The price of the item', validators=[DataRequired()])
    # optional to notify the user about the deployment of the contract
    email = StringField('Email notifier', validators=[Optional(), Email()])
    confirm = BooleanField('I confirm the contract creation', validators=[DataRequired()])
    submit = SubmitField('Deploy contract on Ethereum')

# specifiy the delivery info
# class DeliveryInfo(FlaskForm):
#     pass

# collect info to put in the generated button
class ButtonData(FlaskForm):
    # insertion link (optional)
    name = StringField('Insertion Link (optional)')
    # title of insertion
    title = StringField('Insertion Title', validators=[DataRequired()])
    # ethereum address where to recieve the money
    seller_address = StringField('The Ethereum address where you want to be payed', validators=[DataRequired(), Length(min=40, max=42)])
    # contract time
    contract_time = SelectField('The ammount of days that the contract will stay online in accept payment status', choices=[('86400', '1 day'), ('172800', '2 days'), ('259200', '3 days'), ('345600', '4 days'), ('432000', '5 days'), ('518400', '6 days'), ('604800', '1 week')], default='259200')
    # shipping time
    shipping_eta = SelectField('The eta of the shipping after the package has been payed', choices=[('86400', '1 day'), ('172800', '2 days'), ('259200', '3 days'), ('345600', '4 days'), ('432000', '5 days'), ('518400', '6 days'), ('604800', '1 week'), ('864000', '10 days'), ('1209600', '2 weeks')], default='432000')
    # the price of the item   
    item_price = DecimalField('The price of the item', validators=[DataRequired()])
    # selector that determin if you accept ETH, USDT or both
    currency = SelectField('Currency accepted', choices=[('0', 'ETH'), ('1', 'USDT')])
    # shipping price
    shipping_price = DecimalField('The price of the item', validators=[DataRequired()])
    submit = SubmitField('Generate Button')

# here the user can input the street address and all the info about the delivery
# right now everything will be done manually, later i will put selectors
class DeliverTo(FlaskForm):
    # street address, country, state, postal code
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    buyer_address = StringField('The Ethereum from where you will pay', validators=[DataRequired(), Length(min=40, max=42)])
    street = StringField('Street Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    # TODO this must become a selector
    country = StringField('Country', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    postal_code = StringField('postal code', validators=[DataRequired()])
    email = StringField('Write here your email to get Notifications', validators=[DataRequired(), Email()])
    confirm = BooleanField('I confirm the purchase of the item', validators=[DataRequired()])
    # TODO add chapta here
    submit = SubmitField('Send purchase promess')

# here i have the seller accept and deploy the contract
class ReviewAndDeploy(FlaskForm):
    # seller
    seller_address = StringField('The Ethereum address where you want to be payed', validators=[DataRequired(), Length(min=40, max=42)])
    confirm = BooleanField('I have reviewed the data and i want to deploy the contract', validators=[DataRequired()])
    submit = SubmitField('Deploy the contract')

# let seller add the shipping number
class ShippingNumber(FlaskForm):
    uuid = StringField('', validators=[DataRequired()])
    tracking_number = StringField('Your Tracking number', validators=[DataRequired()])
    shipper = SelectField('Shipping Company', choices=[('DHL', 'DHL')])
    submit = SubmitField('Add Tracking Number')