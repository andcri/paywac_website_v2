from flask import render_template, url_for, flash, redirect, request, Blueprint, request
from flask_login import login_user, current_user, logout_user, login_required
from paywac import db, bcrypt
from paywac.contracts.forms import CreateContract, ButtonData, DeliverTo, ReviewAndDeploy
from paywac.contracts.utils import gas_to_eth, deploy, secondsToText
from paywac.models import Contracts_deployed, Deployer, Oracle, User, Contracts_info, Button_data, Shipping_info, Contracts
from uuid import uuid4
import os
from crontab import CronTab
from datetime import datetime

contracts = Blueprint('contracts', __name__)

# OLD
@contracts.route('/intent/new_contract', methods=['GET', 'POST'])
@login_required
def new_contract():
    """
    Create and deploy the contract to the network, create a cronjob to update the contract status
    """
    # TODO autofill fields if a request comes with args
    # reuqire data insertion from the user inserting all the info to create and deploy a new contract
    form = CreateContract()
    # retrieve active oracle and deployer
    oracle = Oracle.query.filter(Oracle.active==1).first().address
    deployer = Deployer.query.filter(Deployer.active==1).first().address
    # generate a unique request_id
    request_id = str(uuid4())
    # validate data
    if form.validate_on_submit():
        # check if user has enough founds to deploy a contract to determine the status variable value of the Table
        status = 1 if current_user.wac_credits > 0 else 0

        # TODO check if the email field was empty, if not send a notification of the operation at the end of the deployment
        
        # if the status is 0 create the entry in the database withoud deploying the contract
        if status == 0:
            # save the data in the database
            # row = Contracts_deployed(request_id=request_id, contract_creator_user=current_user.email, contract_address='', contract_name=form.name.data,\
            #                             deployer=deployer, seller=form.seller.data, buyer=form.buyer.data, oracle=oracle, contract_time=form.contract_time.data,\
            #                                 contract_delivery_eta=form.shipping_eta.data, item_price=form.item_price.data, status=status, email=form.email.data)

            # db.session.add(row)
            # db.session.commit()
            flash('Not enough founds to deploy the contract, please add founds create and deploy a contract', 'danger')
            return redirect(url_for('main.home'))
        # the user has enough founds to deploy the contract
        else:
            # decrese by one the credit of the user        
            user_wac = User.query.filter_by(email=current_user.email).first()
            user_wac.wac_credits -= 1
            db.session.add(user_wac)

            try:
                # deploy the contract
                tx_receipt = deploy(deployer, form.seller.data, form.buyer.data, oracle, int(form.contract_time.data), int(form.shipping_eta.data), form.item_price.data)
                # the contract address will be retrieved from the receipt
                contract_address = tx_receipt.get('contractAddress')
                # get the transaction status, 1 if the transaction succede, 0 if not, if we have a 0
                # an error will be reported
                transaction_status = tx_receipt.get('status')
                # get the block where the transaction is inside
                block_number = tx_receipt.get('blockNumber')
                # the gas used for the transaction
                gas_used = tx_receipt.get('gasUsed')
                # enter data in the table
                row = Contracts_deployed(request_id=request_id, contract_creator_user=current_user.email, contract_address=contract_address, contract_name=form.name.data,\
                                        deployer=deployer, seller=form.seller.data, buyer=form.buyer.data, oracle=oracle, contract_time=form.contract_time.data,\
                                            contract_delivery_eta=form.shipping_eta.data, item_price=form.item_price.data, status=status, email=form.email.data)
                # redirect user to the contract page
                db.session.add(row)
                db.session.commit()

                # start the script that listen to the contract notifications as a backgroud process
                # PATH_TO_SUBSCRIBER_PAYWAC this will be in a json file
                # PATH_TO_SUBSCRIBER_PAYWAC = '/home/andrea/Desktop/paywac_website/cronjob_scripts/paywac_subscriber.py'
                # os.system(f"nohup {PATH_TO_SUBSCRIBER_PAYWAC} {contract_address} &")
                # TODO create a cronjob that execute every 30 minutes the script cron_update_info_paywac.py
                # sample_cronjob_creator.py mimics the code that will be written here
                cron = CronTab(user='andrea')
                job = cron.new(command=f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website/cronjob_scripts/cron_update_info_paywac.py {contract_address} > /home/andrea/Desktop/paywac_website/logs/cron.log 2>&1')
                job.minute.every(15)

                cron.write()

                flash('Contract Deployed, here you can see the status and real time updates', 'success')
                return redirect(url_for('main.home'))
            except:
                print('error in deploying the contract')
                # TODO notify via email to me that something went wrong
                # put the status of the contract pending approvation
                # flash the message to the user that the contract will be deployed in 1 hour max
    
    # LOGIC: if not save the data in the database and set the flag that is not deployed, redirect to the account page
    # of the user and notify that he has to recharge his founds then he can go to the page of the contract and
    # click the deploy button w/o having to reinput all the data
    result = gas_to_eth(695333, 9)
    return render_template('create_contract.html', form=form)


# TODO modify with the new implementation
@contracts.route('/contract/<string:address>')
def contract(address):
    """
    given a contract address it will display the details of the contract reading
    from the contract_info table
    """
    # data from the contracts deployed
    row = Contracts_deployed.query.filter_by(contract_address=address).first()
    # extract the data from the database
    request_id = row.request_id
    contract_name = row.contract_name
    seller = row.seller
    buyer = row.buyer
    price = row.item_price
    status = row.status

    # data from the contracts info
    row_info = Contracts_info.query.filter_by(contract_address=address).first()
    contract_start = row_info.contract_start
    contract_end = row_info.contract_end
    time_item_delivered = row_info.time_item_delivered
    has_buyer_paid = row_info.has_buyer_paid
    ranking = row_info.ranking

    return render_template('contract.html')


# generate the html code for a button that will be embedded to a third party website to create a request for a new contract
@contracts.route('/intent/generate_button', methods=['GET', 'POST'])
@login_required
def create_button():
    """
    generate the html code for a button that will redirect the user to the contract request
    a form will be used to include specific info about the insertion
    """
    # generate uuid that will identify this button
    uuid = str(uuid4())

    # form that let the user insert the info

    form = ButtonData()

    # generate html for the button
    # the uuid will be the id that we will search in the table to retrieve all the data needed later
    if form.validate_on_submit():

        if form.name.data:
            button_html = f"""
            <a class="button" href="http://127.0.0.1:5000/intent/buy?uid={uuid}" data-size="large">
            <img src="../static/website_img/twitter.png" alt="" style="width:59px; height:24px;">
            </a>
            """

        else:
            button_html = f"""
                <a class="button" href="http://127.0.0.1:5000/intent/buy?uid={uuid}" data-size="large">
                <img src="../static/website_img/twitter.png" alt="" style="width:59px; height:24px;">
                </a>
            """

            # insert button data in the database
        row = Button_data(uuid=uuid, creator_mail=current_user.email, name=form.name.data, title=form.title.data, seller_address=form.seller_address.data, contract_time=form.contract_time.data,\
                            shipping_eta=form.shipping_eta.data, item_price=form.item_price.data, shipping_price=form.shipping_price.data, clicked=0,\
                            button_code=button_html)

        db.session.add(row)
        db.session.commit()

        return render_template('button_creation.html',display_form=False, form=form, generated_code=button_html)

    # LATER STEPS: when a request will be made we check for every value to match the insertion in the database, if
    # there will be a match we get the uuid and we create the request for the seller
    # if there is not a match it means that the data somehow got tampered and we do not create a new request

    return render_template('button_creation.html', display_form=True, form=form)


# page where the buyer is redirected when he press the button
@contracts.route('/intent/buy', methods=['GET', 'POST'])
def buy():
    uid = request.args.get('uid')
    # check if the uuid passed exists and check if the clicked field is set to False, if both this requirements are sadisfied we
    # and we can proceed to ask the user for the info that we need
    row = Button_data.query.filter_by(uuid=uid).first()
    if row != None and row.clicked == 0:
        # change the status of the button, it will not be able to make another request for this button
        row.clicked = 1
        creator_mail = row.creator_mail
        contract_time_formatted = secondsToText(row.contract_time)
        shipping_eta_formatted = secondsToText(row.shipping_eta)
        # form with the info that the user has to input(shipping address)
        form = DeliverTo()
        # confirmation, and creation of buy_request that the seller will review and accept(or that accepts automaticaly if setted to do so)
        if form.validate_on_submit():
            # add the shipping info binded to the uid to the database
            shipping_row = Shipping_info(uuid=uid, seller_email=creator_mail, buyer_email=form.email.data, street=form.street.data,\
                                            city=form.city.data, country=form.country.data, state=form.state.data, postal_code=form.postal_code.data)
            # create new contract in pending seller approval status
            contract_row = Contracts(uuid=uid, name=row.name, title=row.title, owner=creator_mail, seller_address=row.seller_address,\
                                        contract_time=row.contract_time, shipping_eta=row.shipping_eta, item_price=row.item_price,\
                                            shipping_price=row.shipping_price, status=0)

            db.session.add(shipping_row)
            db.session.add(contract_row)
            db.session.commit()
            # buyer will recieve a email when the contract is actually deployed, this will redirect him to the contract page where he will be
            # able to see the contract address and provide the payment
            flash('Your request has been submitted successfully, please wait on your email for a notification with the payment info', 'success')
            # TODO send email notification to the seller
            return redirect(url_for('main.home'))
        return render_template('buy.html', response="info about the item", form=form, insertion_link=row.name, insertion_title=row.title,\
                                seller_address=row.seller_address, contract_time=contract_time_formatted, shipping_eta=shipping_eta_formatted,\
                                    item_price=row.item_price, shipping_price=row.shipping_price)
    elif row == None:
        flash("This request does not exists", 'danger')
        return redirect(url_for('main.home'))
    elif row.clicked == 1:
        flash("This request has already been done by somebody else already", 'warning')
        return redirect(url_for('main.home'))


#route that will allow the seller to review the complete info and decide if to accept and deploy the contract or not
@contracts.route("/intent/deploy_contract/<string:uid>", methods=['GET', 'POST'])
@login_required
def deploy_contract(uid):
    # check if the uid of the contract has as owner the user that is currently logged in, if not redirect the user to the home page
    # with flash message
    # check also if the contract has been deployed yet, it is if the status is != 0
    contract = Contracts.query.filter_by(uuid=uid).first()
    # check if the uuid exists
    if contract is None:
        flash('Nope', 'danger')
        return redirect(url_for('main.home'))
    
    shipping_info = Shipping_info.query.filter_by(uuid=uid).first()
    contract_owner = contract.owner
    contract_status = contract.status
    contract_time = contract.contract_time
    contract_shipping_eta = contract.shipping_eta
    contract_item_price = contract.item_price
    contract_shipping_price = contract.shipping_price
    oracle = Oracle.query.filter(Oracle.active==1).first().address
    deployer = Deployer.query.filter(Deployer.active==1).first().address
    user_wac = User.query.filter_by(email=current_user.email).first()

    if current_user.email == contract_owner and contract_status == 0:

        # form that require the user to accept and let the user submit and doing so the contract will be deployed
        form = ReviewAndDeploy()
        form.seller_address.data = contract.seller_address

        if form.validate_on_submit() and user_wac.wac_credits > 0:
            # reduce by one the deployment count for the user
            user_wac.wac_credits -= 1
            db.session.add(user_wac)

            # deploy contract on ethereum and collect response info(contract address ecc)
            try:
            
                tx_receipt = deploy(deployer, form.seller_address.data, oracle, contract_time, contract_shipping_eta, contract_item_price, contract_shipping_price)
                
                contract_address = tx_receipt.get('contractAddress')
                # get the transaction status, 1 if the transaction succede, 0 if not, if we have a 0
                # an error will be reported
                transaction_status = tx_receipt.get('status')
                # get the block where the transaction is inside
                block_number = tx_receipt.get('blockNumber')
                # the gas used for the transaction
                gas_used = tx_receipt.get('gasUsed')

                if transaction_status == 0:
                    # there was an error with the transaction that creates the contract, in this case we will signal the error to the user
                    # and an email with priority max will be sent to the tech support to fix the issue
                    flash("Contract creation went wrong", 'danger')
                    return redirect(url_for('main.home'))

                # change status from 0 to 1
                contract.status = 1
                contract.contract_address = contract_address
                contract.deployed_date = datetime.now()
                db.session.commit()
                
                # TODO execute the cronjob funcion one time manually to have immediately some data to display

                # create cronjob for that reads the data inside the contract and insert it into the database
                try:
                    cron = CronTab(user='andrea')
                    job = cron.new(command=f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website_v02/cronjob_scripts/cron_update_info_paywac.py {contract_address} > /home/andrea/Desktop/paywac_website_v02/logs/cron.log 2>&1')
                    job.minute.every(15)

                    cron.write()
                except:
                    print("error creating the cronjob for the newly deployed contract")

                flash('Contract Deployed successfully', 'success')

                # TODO send email notification to the buyer
                return redirect(url_for('main.home'))
            except:
                flash("Error Deploying the contract","danger")

        elif form.validate_on_submit() and user_wac.wac_credits == 0:
            flash('You dont have enough founds to deploy a contract','warning')
            # TODO add instructions to add tokens for contract deployment
        
        return render_template('deploy_contract.html', form=form, uuid=uid, insertion_link=contract.name, insertion_title=contract.title, seller_address=contract.seller_address,\
                                contract_time=secondsToText(contract.contract_time), shipping_eta=secondsToText(contract.shipping_eta), item_price=contract.item_price, shipping_price=contract.shipping_price,\
                                    city=shipping_info.city, street=shipping_info.street, country=shipping_info.country, state=shipping_info.state, postal_code=shipping_info.postal_code)
    elif current_user.email == contract_owner and contract_status != 0:
        flash("This contract has already been deployed")
        return redirect(url_for('main.home'))
    else:
        flash("You are not the owner of this contract, if you think you are please contact support", "warning")
        return redirect(url_for('main.home'))


# display a list of the contract wich you are the owner of
@contracts.route("/my_contracts")
@login_required
def my_contracts():
    rows = Contracts.query.filter_by(owner=current_user.email).all()
    # TODO if the contract is not in status 0 we will display for each contract a button that contains shipping info
    # and a form to add the tracking number if the contract is in status 2 (item payed)
    return render_template('my_contracts.html', contracts=rows)

# display a list of the buttons wich you are the owner of
@contracts.route("/my_buttons")
@login_required
def my_buttons():
    rows = Button_data.query.filter_by(creator_mail=current_user.email).all()
    return render_template('my_buttons.html', buttons=rows)

# this can be called only from the seller and will allow him to reject the contract creation after a user
# has submitted a payment promess
@contracts.route("/intent/<string:uid>/delete", methods=['POST'])
@login_required
def delete_contract(uid):
    # get all the row from the Contracts, Shipping_info relative to this contract to drop them
    # modify the status of the button(the user will be able to recieve other contract offers)
    contract = Contracts.query.filter_by(uuid=uid).first()
    if contract is None:
        flash('Nope', 'danger')
        return redirect(url_for('main.home'))
    shipping_info = Shipping_info.query.filter_by(uuid=uid).first()
    button_data = Button_data.query.filter_by(uuid=uid).first()
    if contract.owner != current_user.email:
        abort(403)
    db.session.delete(contract)
    db.session.delete(shipping_info)
    button_data.clicked = 0
    db.session.commit()
    flash('Contract proposal refused', 'success')
    return redirect(url_for('main.home'))