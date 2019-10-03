event_add_founds : event({ _from : indexed(address), _to : indexed(address), _value: wei_value})
deployer: public(address)
contract_cost: public(wei_value)

@public
def __init__(_deployer : address):
    self.deployer = _deployer

@payable
@public
def add_founds():
    log.event_add_founds(msg.sender, self.deployer, msg.value)
    send(self.deployer, msg.value)