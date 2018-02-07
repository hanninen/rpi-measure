# -*- coding: utf-8 -*-
from setuptools import setup


setup(name='rpi_measure',
      version='0.1',
      description='Temperature and humidity measurement from Raspberry Pi with DHT22 sensor to AWS IoT',
      url='http://github.com/hanninen/rpi-measurement',
      author='Aki Hänninen',
      author_email='aki@hanninen.net',
      license='Apache-2.0',
      install_requires=[
        'AWSIoTPythonSDK',
        'pigpio'
      ],
      include_package_data=True,
      packages=['rpi_measure'],
      scripts=['bin/rpi-measure'],
      zip_safe=False)
