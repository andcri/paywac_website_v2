# connect to the erc20 token methods
contract Pcoin():
    def transfer(_to : address, _value : uint256) -> bool: modifying
    def balanceOf(_address: address) -> uint256: constant

buyer : public(address)
seller: public(address)
oracle: public(address)
token_address : public(address)

contractStart: public(timestamp)
# @dev the time that the contract will last after the fist deployment
contractEnd : public(timestamp)
# @dev the time that the contract will last after the payment is being verified
contractLife: public(timedelta)
time_item_delivered: public(timestamp)

is_paid: public(bool)
is_package_received: public(bool)
refounded: public(bool)

contract_balance: public(uint256)
item_price: public(uint256)
shipping_price: public(uint256)
fee:public(uint256)

@public
def __init__(_buyer: address, _seller: address, _oracle: address, _token_address: address, _contract_time: timedelta, _contract_shipping_eta : timedelta, _shipping_price : uint256, _item_price: uint256):
    self.buyer = _buyer
    self.seller = _seller
    self.oracle = _oracle
    self.token_address = _token_address
    self.contractStart = block.timestamp
    self.contractEnd = self.contractStart + _contract_time
    self.contractLife = _contract_shipping_eta 
    self.shipping_price = _shipping_price
    self.item_price = _item_price

# @dev return the balance of erc20 tokens that this contract has
@private
@constant
def get_balance() -> uint256:
    return Pcoin(self.token_address).balanceOf(self)

# @dev function that the buyer calls after making the payment to
#      prove that he has made it
# @conditions the contract has to be still live for the buyer to
#             be able to confirm his payment
# @future this could be called from the oracle when the event is registered
#         this will result in a higher fee to cover the cost of the call
#         for now we leave it like this.
@public
def check_buyer_payment() -> bool:
    assert msg.sender == self.buyer
    assert block.timestamp < self.contractEnd
    assert self.is_paid == False

    self.contract_balance = self.get_balance()
    
    assert self.contract_balance >= self.item_price + self.shipping_price
    
    self.contractEnd = block.timestamp + self.contractLife
    self.fee = (self.contract_balance * 1) / 100
    self.contract_balance = self.contract_balance - self.fee
    self.is_paid = True

    return Pcoin(self.token_address).transfer(self.oracle, self.fee)

# @dev function callable only from the oracle that send the tokens to the
#      seller once the shippment arrived to the destination
@public
def package_received() -> bool:
    assert msg.sender == self.oracle
    assert self.is_paid == True
    assert self.is_package_received == False
    assert self.refounded == False

    founds_to_send: uint256 = self.contract_balance
    self.is_package_received = True
    self.time_item_delivered = block.timestamp
    self.contract_balance = 0

    return Pcoin(self.token_address).transfer(self.seller, founds_to_send)
    
# @dev function callable by the buyer if the package is not recieved or
#      not accepted from the seller
@public
def refound() -> bool:
    assert msg.sender == self.buyer
    assert block.timestamp > self.contractEnd
    assert self.is_paid == True
    assert self.is_package_received == False

    founds_to_send: uint256 = self.contract_balance
    self.refounded = True
    self.contract_balance = 0
    return Pcoin(self.token_address).transfer(self.buyer, founds_to_send)