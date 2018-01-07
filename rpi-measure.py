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
import uuid
import sys
import logging
import ConfigParser
import Adafruit_DHT

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from datetime import datetime
from daemonize import Daemonize


class RPiMeasure():
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
            self.myAWSIoTMQTTClient = AWSIoTMQTTClient(self.clientId)
            self.myAWSIoTMQTTClient.configureEndpoint(self.host, 8883)
            self.myAWSIoTMQTTClient.configureCredentials(self.rootCAPath, self.privateKeyPath, self.certificatePath)

            # AWSIoTMQTTClient connection configuration
            self.myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
            self.myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
            self.myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
            self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
            self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

            # Connect and subscribe to AWS IoT
            self.myAWSIoTMQTTClient.connect()
            time.sleep(2)

        def run(self):
                self.configure()
                self.create_mqtt_client()
                while True:
                    self.send_measure()
                    time.sleep(10)

        def read_sensor(self):
            logger.info('Reading sensor')
            sensor = Adafruit_DHT.DHT22
            logger.info('Sensor created')
            # Example using a Raspberry Pi with DHT sensor
            # connected to GPIO23.
            pin = 23

            # Try to grab a sensor reading.  Use the read_retry method which will retry up
            # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
            logger.info('Read sensor')

            # Note that sometimes you won't get a reading and
            # the results will be null (because Linux can't
            # guarantee the timing of calls to read the sensor).
            # If this happens try again!
            if humidity is not None and temperature is not None:
                logger.info('Read sensor again')
                logger.info('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            else:
                logger.info('Failed to get reading. Try again!')

            return (humidity, temperature)

        def send_measure(self):
            humidity, temperature = self.read_sensor()
            message = {}
            message['timestamp'] = str(datetime.now())
            message['msg_id'] = str(uuid.uuid4())
            message['temperature'] = temperature
            message['humidity'] = humidity
            messageJson = json.dumps(message)
            self.myAWSIoTMQTTClient.publish(self.topic, messageJson, 1)
            logger.debug('Published topic %s: %s\n' % (self.topic, messageJson))


pid = "/tmp/test.pid"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler("/tmp/test.log", "w")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

rpi = RPiMeasure()
daemon = Daemonize(app="rpi-measure", pid=pid, action=rpi.run, logger=logger, keep_fds=keep_fds)
daemon.start()
