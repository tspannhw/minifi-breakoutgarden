from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os.path
import re
import sys
import tarfile
import os
import datetime
import math
import random, string
import base64
import json
import time
from time import sleep
from time import gmtime, strftime

import sys
import datetime
import subprocess
import os
import base64
import uuid
import datetime
import traceback
import math
import random, string
import socket
import json
import math
import time
import psutil
#
# Sensors
#
import bme680
import time

# MQTT
import paho.mqtt.client as paho
client = paho.Client()
client.username_pw_set("user","password")

# yyyy-mm-dd hh:mm:ss
currenttime = strftime("%Y-%m-%d %H:%M:%S", gmtime())

host = os.uname()[1]


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

# TODO:  send status message to screen
def do_nothing(obj):
    pass

def IP_address():
    try:
        s = socket.socket(socket_family, socket.SOCK_DGRAM)
        s.connect(external_IP_and_port)
        answer = s.getsockname()
        s.close()
        return answer[0] if answer else None
    except socket.error:
        return None

def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return (res.replace("temp=", "").replace("'C\n", ""))


# - start timing
starttime = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')
start = time.time()

external_IP_and_port = ('198.41.0.4', 53)  # a.root-servers.net
socket_family = socket.AF_INET

# Ip address
ipaddress = IP_address()

# MQTT Connect
client.connect("cloud.com", 17769, 60)

# --- Reuse from bme680 indoor airquality sample
try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except IOError:
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# start_time and curr_time ensure that the
# burn_in_time (in seconds) is kept track of.

start_time = time.time()
curr_time = time.time()
burn_in_time = 300
burn_in_data = []

try:
    # Collect gas resistance burn-in values, then use the average
    # of the last 50 values to set the upper limit for calculating
    # gas_baseline.
    print('Collecting gas resistance burn-in data for 5 mins\n')
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            burn_in_data.append(gas)
            time.sleep(1)

    gas_baseline = sum(burn_in_data[-50:]) / 50.0

    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25

    while True:
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            gas_offset = gas_baseline - gas

            hum = sensor.data.humidity
            hum_offset = hum - hum_baseline

            # From BME680 Example Library
            # Calculate hum_score as the distance from the hum_baseline.
            if hum_offset > 0:
                hum_score = (100 - hum_baseline - hum_offset)
                hum_score /= (100 - hum_baseline)
                hum_score *= (hum_weighting * 100)

            else:
                hum_score = (hum_baseline + hum_offset)
                hum_score /= hum_baseline
                hum_score *= (hum_weighting * 100)

            # Calculate gas_score as the distance from the gas_baseline.
            if gas_offset > 0:
                gas_score = (gas / gas_baseline)
                gas_score *= (100 - (hum_weighting * 100))

            else:
                gas_score = 100 - (hum_weighting * 100)

            # Calculate air_quality_score.
            air_quality_score = hum_score + gas_score

            # New Row
            row = {}
            uuid2 = '{0}_{1}'.format(strftime("%Y%m%d%H%M%S", gmtime()), uuid.uuid4())
            cpuTemp = int(float(getCPUtemperature()))
            end = time.time()
            row['host'] = os.uname()[1]
            row['cputemp'] = round(cpuTemp, 2)
            row['ipaddress'] = ipaddress
            row['end'] = '{0}'.format(str(end))
            row['te'] = '{0}'.format(str(end - start))
            row['bme680_tempc'] = '{0:.2f}'.format(sensor.data.temperature)
            row['bme680_tempf'] = '{0:.2f}'.format((sensor.data.temperature * 1.8) + 32)
            row['bme680_pressure'] = '{0:.2f}'.format(sensor.data.pressure)
            row['bme680_gas'] = '{0:.2f}'.format(gas)
            row['bme680_humidity'] = '{0:.2f}'.format(hum)
            row['bme680_air_quality_score'] = '{0:.2f}'.format(air_quality_score)
            row['bme680_gas_baseline'] = '{0:.2f}'.format(gas_baseline)
            row['bme680_hum_baseline'] = '{0:.2f}'.format(hum_baseline)
            row['systemtime'] = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')
            row['starttime'] = starttime
            usage = psutil.disk_usage("/")
            row['diskusage'] = "{:.1f}".format(float(usage.free) / 1024 / 1024)
            row['memory'] = psutil.virtual_memory().percent
            row['uuid'] = str(uuid2)
            json_string = json.dumps(row)
            json_string += str("\n")
            client.publish("aqsensor", payload=json_string)
            time.sleep(1)

except KeyboardInterrupt:
    pass
