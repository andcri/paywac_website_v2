seller: public(address)
buyer: public(address)
oracle: public(address)
deployer: public(address)

contractStart: public(timestamp)
contractEnd : public(timestamp)
contractLife: public(timedelta)
time_item_delivered: public(timestamp)

item_price: public(wei_value)
shipping_price: public(wei_value)
payed_ammount: public(wei_value)
fee: public(wei_value)

has_buyer_paid: public(bool)
is_package_recieved: public(bool)
refounded: public(bool)

@public
def __init__(_deployer : address, _seller : address,  _oracle : address, _contract_time: timedelta, _contract_shipping_eta : timedelta, _item_price: wei_value, _shipping_price : wei_value):
    self.deployer = _deployer
    self.seller = _seller
    self.oracle = _oracle
    self.item_price = _item_price
    self.shipping_price = _shipping_price
    self.contractStart = block.timestamp
    self.contractEnd = self.contractStart + _contract_time
    self.contractLife = _contract_shipping_eta
    self.refounded = False
    
# @dev function that the buyer calls to make a payment
@public
@payable
def pay():
    assert block.timestamp < self.contractEnd
    assert msg.value >= self.item_price + self.shipping_price
    assert not self.has_buyer_paid

    self.buyer = msg.sender
    self.has_buyer_paid = True
    self.fee = (msg.value * 1) / 100
    self.payed_ammount = msg.value - self.fee
    self.contractEnd = block.timestamp + self.contractLife #+ 259200
    send(self.oracle, self.fee)

# @dev function called from the oracle when the item arrived to the destination
@public
def change_package_recieved_status():
    assert msg.sender == self.oracle
    assert self.is_package_recieved == False
    assert self.refounded == False
    assert self.has_buyer_paid == True

    self.is_package_recieved = True
    self.time_item_delivered = block.timestamp
    send(self.seller, self.payed_ammount)

# @dev function that can be called by the buyer when the contract expires
#      if he didnt recieved the package to get a refound - fee of his payment
@public
def refound():
    assert block.timestamp > self.contractEnd
    assert self.is_package_recieved == False
    assert self.has_buyer_paid == True
    assert msg.sender == self.buyer

    self.refounded = True
    send(self.buyer, self.payed_ammount)