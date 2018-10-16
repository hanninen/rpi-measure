import time
import json
import verisure
import boto3

from datetime import datetime
from datetime import timedelta
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    devices = event['devices']

    ssm = boto3.client('ssm')
    password = ssm.get_parameter(
        Name='/lambda/vsure/password', 
        WithDecryption=True
    )
    password = password['Parameter']['Value']
    login = ssm.get_parameter(Name='/lambda/vsure/login')
    login = login['Parameter']['Value']

    for device_id in devices.keys():
        session = verisure.Session(login, password, cookieFileName='/tmp/verisure-cookie')
        session.login()
        values = session.get_climate(devices[device_id])
        measurement = values[0]['simpleClimateSamples'][-1]

        if not is_latest_measurement(measurement, device_id):
            endpoint = 'a1gq7cu6baut56-ats.iot.eu-west-1.amazonaws.com'
            client = get_iot_client(device_id, endpoint)
            connect_iot(client, device_id, measurement)


def fix_timestamp(timestamp):
    return timestamp.replace('T', ' ').replace('Z', '000')

def is_latest_measurement(measurement, device_id):
    table = boto3.resource('dynamodb').Table('indoor')
    measurement = fix_timestamp(measurement['time'])
    two_h_ago = str(datetime.utcnow() - timedelta(hours=2))[:-9]

    latest_entry = table.query(
        Select='SPECIFIC_ATTRIBUTES',
        KeyConditionExpression=Key('device_id').eq(device_id) & Key('msg_timestamp').gt(two_h_ago),
        ProjectionExpression='msg_timestamp',
        ScanIndexForward=False,
        Limit=1
    )
    try:
        latest_entry = latest_entry['Items'][0]['msg_timestamp']
    except IndexError:
        latest_entry = ''

    return latest_entry == measurement


def get_iot_client(device_id, endpoint):
    client = AWSIoTMQTTClient(device_id, useWebsocket=True)
    client.configureEndpoint(endpoint, 443)
    client.configureCredentials('AmazonRootCA1.pem')
    return client

def connect_iot(client, device_id, measurement):
    connected = client.connect()

    if not connected:
        raise Exception('Connection to AWS IoT failed')
    
    message = {}
    message['msg_timestamp'] = fix_timestamp(measurement['time'])
    message['device_id'] = device_id
    message['temperature'] = measurement['temperature']
    message['humidity'] = measurement['humidity']
    # expire parameter for DynamoDB TTL
    expire = datetime.utcnow() + timedelta(31)
    message['expire'] = int(time.mktime(expire.timetuple()))
    messageJson = json.dumps(message)
    client.publish("measures/{}".format(device_id), messageJson, 1)
    print("Published: {}".format(messageJson))
    time.sleep(0.5)
    
    client.disconnect()