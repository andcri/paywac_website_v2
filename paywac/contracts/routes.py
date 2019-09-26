from flask import render_template, url_for, flash, redirect, request, Blueprint, request
from flask_login import login_user, current_user, logout_user, login_required
from paywac import db, bcrypt
from paywac.contracts.forms import CreateContract, ButtonData, DeliverTo, ReviewAndDeploy, ShippingNumber
from paywac.contracts.utils import gwei_to_eth, deploy, secondsToText
from paywac.models import Deployer, Oracle, User, Contracts_info, Button_data, Shipping_info, Contracts, Shipping_tracking, Gas_price
from uuid import uuid4
import os
from crontab import CronTab
from datetime import datetime

contracts = Blueprint('contracts', __name__)

@contracts.route('/contract/<string:address>')
def contract(address):
    """
    given a contract address it will display the details of the contract reading
    from the contract_info table
    """
    # data from the contracts deployed
    row = Contracts.query.filter_by(contract_address=address).first()
    # extract the data from the database
    uid = row.uuid
    contract_title = row.title
    seller = row.seller_address
    price = row.item_price
    shipping_price = row.shipping_price
    status = row.status

    # data from the contracts info
    row_info = Contracts_info.query.filter_by(contract_address=address).first()
    contract_start = row_info.contract_start
    contract_end = row_info.contract_end
    time_item_delivered = row_info.time_item_delivered
    has_buyer_paid = row_info.has_buyer_paid
    ranking = row_info.ranking

    return render_template('contract.html', contract_start=contract_start, contract_end=contract_end, time_item_delivered=time_item_delivered,\
                            has_buyer_paid=has_buyer_paid, ranking=ranking, status=status, title=contract_title)


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
                                            city=form.city.data, country=form.country.data, state=form.state.data, postal_code=form.postal_code.data,\
                                                buyer_name=form.name.data, buyer_surname=form.surname.data)
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

        # TODO calculate contract deployment price based on the avg gas price and the contract price inside the gas table
        # display based on that calculation and the ammount of eth that the user has in his account under wac_credits

        table_gas_price = Gas_price.query.filter_by(id=1).first()
        gas_price = table_gas_price.standard_gas_price
        contract_cost = table_gas_price.contract_cost


        user_avaiable_eth = user_wac.wac_credits
        eth_needed_for_deployment = gwei_to_eth(gas_price * contract_cost)

        # TODO understand in witch format the eth has being saved from the add_founds cron and then convert it to eth if is not already
        deployments_avaiables = gwei_to_eth(user_avaiable_eth) / eth_needed_for_deployment

        # form that require the user to accept and let the user submit and doing so the contract will be deployed
        form = ReviewAndDeploy()
        form.seller_address.data = contract.seller_address

        if form.validate_on_submit() and eth_needed_for_deployment >= user_wac.wac_credits:
            # reduce by one the deployment count for the user
            user_wac.wac_credits -= eth_needed_for_deployment
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
                
                # execute the cronjob funcion one time manually to have immediately some data to display
                # TO BE TESTED
                
                # create cronjob for that reads the data inside the contract and insert it into the database
                try:
                    cron = CronTab(user='andrea')
                    job = cron.new(command=f'/home/andrea/anaconda3/envs/vyper/bin/python /home/andrea/Desktop/paywac_website_v02/cronjob_scripts/cron_update_info_paywac.py {contract_address} >> /home/andrea/Desktop/paywac_website_v02/logs/cron.log_{contract_address} 2>&1')
                    job.minute.every(15)

                    cron.write()
                except:
                    print("error creating the cronjob for the newly deployed contract")

                flash(f'Contract Deployed successfully at address {contract_address}', 'success')
                flash('It may take up to 15 minutes to be able to see the contract in the website', 'success')

                # TODO send email notification to the buyer
                return redirect(url_for('main.home'))
            except:
                flash("Error Deploying the contract","danger")

        elif form.validate_on_submit() and eth_needed_for_deployment < user_wac.wac_credits:
            flash('You dont have enough founds to deploy a contract','warning')
            # TODO add instructions to add tokens for contract deployment
        
        return render_template('deploy_contract.html', form=form, uuid=uid, insertion_link=contract.name, insertion_title=contract.title, seller_address=contract.seller_address,\
                                contract_time=secondsToText(contract.contract_time), shipping_eta=secondsToText(contract.shipping_eta), item_price=contract.item_price, shipping_price=contract.shipping_price,\
                                    city=shipping_info.city, street=shipping_info.street, country=shipping_info.country, state=shipping_info.state, postal_code=shipping_info.postal_code,\
                                        name=shipping_info.buyer_name, surname=shipping_info.buyer_surname, deployments_avaiables=round(deployments_avaiables))
    elif current_user.email == contract_owner and contract_status != 0:
        flash("This contract has already been deployed")
        return redirect(url_for('main.home'))
    else:
        flash("You are not the owner of this contract, if you think you are please contact support", "warning")
        return redirect(url_for('main.home'))


# display a list of the contract wich you are the owner of
@contracts.route("/my_contracts", methods=['GET', 'POST'])
@login_required
def my_contracts():
    rows = Contracts.query.filter_by(owner=current_user.email).order_by(Contracts.request_created.desc()).all()
    form = ShippingNumber()
    if form.validate_on_submit():
        
        # add data in the shipping database
        shipping_tracking = Shipping_tracking(uuid=form.uuid.data, tracking_number=form.tracking_number.data, shipper=form.shipper.data, status='pending',\
                                                last_location='')
        # change the status of the tracked variable in the contract table
        contract = Contracts.query.filter_by(uuid=form.uuid.data).first()
        contract.tracked = 1

        db.session.add(shipping_tracking)
        db.session.add(contract)
        db.session.commit()

        # TODO start cronjob that retrieves data from the shipping

    return render_template('my_contracts.html', _contracts=rows, form=form)

# display a list of the buttons wich you are the owner of
@contracts.route("/my_buttons")
@login_required
def my_buttons():
    rows = Button_data.query.filter_by(creator_mail=current_user.email).order_by(Button_data.id.desc()).all()
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