import boto3
from datetime import datetime, timedelta


def get_value(attributeName, device_id, minutes=30):
    client = boto3.client('dynamodb')
    time1 = str(datetime.utcnow())
    time2 = str(datetime.strptime(time1, '%Y-%m-%d %H:%M:%S.%f') - timedelta(minutes=minutes))
    response = client.query(
        TableName='indoor', 
        ProjectionExpression=attributeName, 
        Limit=1, 
        KeyConditionExpression="device_id = :device AND #time BETWEEN :time2 AND :time1", 
        ExpressionAttributeValues={
            ':time1': {'S': time1}, 
            ':time2': {'S': time2}, 
            ':device': {'S': device_id}
        }, 
        ExpressionAttributeNames={'#time': 'msg_timestamp'}, 
        ScanIndexForward=False
    )

    try:
        value = response['Items'][0][attributeName]['N']
    except IndexError:
        value = None

    return value


def send_notification(temperature, humidity, device):
    client = boto3.client('sns')
    response = client.publish(
        PhoneNumber='+358400184758', 
        Message="[rpi-measure] Could not read data from {}".format(device)
        )
    print(response)
    
#    client = boto3.client('ses')
#    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#    response = client.send_email(
#        Source='monitoring@hanninen.net',
#        Destination={
#            'ToAddresses': [
#                'aki@hanninen.net',
#            ]
#        },
#        Message={
#            'Subject': {
#                'Data': '[rpi-measure] Could not read data'
#            },
#            'Body': {
#                'Text': {
#                    'Data': "Failed to read valid temperature %s) or humidity (%s) at %s" %(temperature, humidity, now)
#                }
#            }
#        }
#    )
#    print("Email %s sent" % (response['MessageId'],))
    
    
def lambda_handler(event, context):
    for device in ['pi-1', 'vsure-1', 'vsure-2']:
        temperature = get_value('temperature', device, minutes=60)
        humidity = get_value('humidity', device, minutes=60)
    
        if temperature == None or humidity == None:
            send_notification(temperature, humidity, device)
