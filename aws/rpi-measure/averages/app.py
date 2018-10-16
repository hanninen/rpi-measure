import os
import boto3
from datetime import datetime, timedelta

def get_device_id(device_id, timeValue, timeFormat):
    return '{}-avg-{}{}'.format(device_id, timeValue, timeFormat)

def gen_msg_timestamp(current_time, timeFormat):
    if timeFormat == 'hours':
        return datetime.strftime(current_time, '%Y-%m-%d %H:00:00.000000')
    else:
        return datetime.strftime(current_time, '%Y-%m-%d 00:00:00.000000')

def get_value(timeValue, timeFormat, device_id):
    print("rpi-measure-averages: {}-{}-{}".format(device_id, timeValue, timeFormat))
    # vsure devices report only once per hour, look past 60 minutes
    if ((device_id == 'vsure-1' or device_id == 'vsure-2') and timeFormat == 'hours'):
        timeValue = 1.15
    params = { timeFormat: timeValue }
    client = boto3.client('dynamodb')
    time1 = datetime.utcnow()
    time2 = str(datetime.strptime(str(time1), '%Y-%m-%d %H:%M:%S.%f') - timedelta(**params))
    response = client.query(
        TableName='indoor', 
        KeyConditionExpression="device_id = :device AND #time BETWEEN :time2 AND :time1", 
        ExpressionAttributeValues={
            ':time1': {'S': str(time1)}, 
            ':time2': {'S': time2}, 
            ':device': {'S': device_id}
        }, 
        ExpressionAttributeNames={'#time': 'msg_timestamp'}, 
        ScanIndexForward=False
    )
    total = int(response['Count'])
    temperature_avg = sum(float(d['temperature']['N']) for d in response['Items'] if 'N' in d['temperature']) / total
    humidity_avg = sum(float(d['humidity']['N']) for d in response['Items'] if 'N' in d['temperature']) / total
    
    if (timeValue == 1.15):
        timeValue = 1
    
    # TODO msg_timestamp and device_id matches timeFormat
    client.put_item(
        Item={
            'device_id': {
                'S': get_device_id(device_id, timeValue, timeFormat)
            },
            'msg_timestamp': {
                'S': gen_msg_timestamp(time1, timeFormat)
            },
            'temperature': {
                'N': str(temperature_avg)
            },
            'humidity': {
                'N': str(humidity_avg)
            }
        },
        TableName='indoor'
    )

def lambda_handler(event, context):
    print(event)
    for device in event['device_ids']:
        get_value(event['timeValue'], event['timeFormat'], device)
