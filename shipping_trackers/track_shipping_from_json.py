import json

with open('dhl_response.json') as json_file:
    data = json.load(json_file)

for shipment in data['shipments']:
    print(shipment.keys())
    print(shipment['events'])
    print(shipment['destination'])
    print(shipment['status'])
    # from the status i can extract the status key
    status = shipment['status']['status']
    if status == 'DELIVERED':
        print(status)
    print(shipment['details']['proofOfDelivery']['signed'])