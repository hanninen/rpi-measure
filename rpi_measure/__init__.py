#!/usr/bin/env python
'''
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

import time
import json
import sys
import logging
import ConfigParser
import Adafruit_DHT

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from datetime import datetime


class RPiMeasure():
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.DEBUG)
            self.logger.propagate = False

        def configure(self):
            config = ConfigParser.ConfigParser()

            try:
                config.readfp(open('/Users/ahannine/src/personal/rpi-measurement/measure.conf'))
            except:
                print("Unable to read measure.conf")
                sys.exit(3)

            self.host = config.get("connection", "host")
            self.clientId = config.get("connection", "clientId")
            self.topic = config.get("connection", "topic")
            self.rootCAPath = config.get("cert", "rootCAPath")
            self.certificatePath = config.get("cert", "certificatePath")
            self.privateKeyPath = config.get("cert", "privateKeyPath")

        def create_mqtt_client(self):
            # Init AWSIoTMQTTClient
            self.mqtt_client = AWSIoTMQTTClient(self.clientId)
            self.mqtt_client.configureEndpoint(self.host, 8883)
            self.mqtt_client.configureCredentials(self.rootCAPath, self.privateKeyPath, self.certificatePath)

            # AWSIoTMQTTClient connection configuration
            self.mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
            # Infinite offline Publish queueing
            self.mqtt_client.configureOfflinePublishQueueing(-1)
            # Draining: 2 Hz
            self.mqtt_client.configureDrainingFrequency(2)
            self.mqtt_client.configureConnectDisconnectTimeout(10)
            self.mqtt_client.configureMQTTOperationTimeout(5)

        def connect_mqtt_client(self):
            # Connect and subscribe to AWS IoT
            self.logger.debug('Connecting to %s/%s MQTT queue' % (self.host, self.topic))
            self.mqtt_client.connect()
            self.logger.debug('Connected')
            time.sleep(2)

        def disconnect_mqtt_client(self):
            self.logger.debug('Disconnecting from %s/%s MQTT queue' % (self.host, self.topic))
            self.mqtt_client.disconnect()
            self.logger.debug('Disconnected')

        def run(self):
                self.configure()
                self.create_mqtt_client()
                while True:
                    self.send_measure()
                    time.sleep(58)

        def read_sensor(self):
            self.logger.info('Reading sensor')
            sensor = Adafruit_DHT.DHT22
            self.logger.info('Sensor created')
            # Example using a Raspberry Pi with DHT sensor
            # connected to GPIO23.
            pin = 23

            # Try to grab a sensor reading.  Use the read_retry method which will retry up
            # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
            self.logger.info('Read sensor')

            # Note that sometimes you won't get a reading and
            # the results will be null (because Linux can't
            # guarantee the timing of calls to read the sensor).
            # If this happens try again!
            if humidity is not None and temperature is not None:
                self.logger.info('Read sensor again')
                self.logger.info('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            else:
                self.logger.info('Failed to get reading. Try again!')

            return (humidity, temperature)

        def send_measure(self):
            humidity, temperature = self.read_sensor()
            message = {}
            message['msg_timestamp'] = str(datetime.utcnow())
            message['device_id'] = self.clientId
            message['temperature'] = temperature
            message['humidity'] = humidity
            messageJson = json.dumps(message)
            self.connect_mqtt_client()
            self.mqtt_client.publish(self.topic, messageJson, 1)
            self.logger.debug('Published topic %s: %s\n' % (self.topic, messageJson))
            self.disconnect_mqtt_client()
