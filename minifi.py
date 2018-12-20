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
import base64
import json
import cv2
import math
import time
import psutil
import socket
from time import gmtime, strftime
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
#
# Sensors
#
from bh1745 import BH1745
import VL53L1X
import ltr559
import bme680
from lsm303d import LSM303D

# TODO:  continuous loop, send status message to screen

def do_nothing(obj):
    pass
    
def send_tcp(ipaddress, message):
	try:
	    TCP_PORT = 5005  # define somewhere
	    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    s.connect((ipaddress, TCP_PORT))
	    s.sendall(message)
	    s.close()
	except:
     print("Failed to send message")

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
    return(res.replace("temp=","").replace("'C\n",""))

# - start timing                
starttime = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') 
start = time.time()

external_IP_and_port = ('198.41.0.4', 53)  # a.root-servers.net
socket_family = socket.AF_INET

# Set up OLED
oled = sh1106(i2c(port=1, address=0x3C), rotate=2, height=128, width=128)
oled.cleanup = do_nothing

# Set Constants
MAX_DISTANCE_MM = 800 # Distance at which our bar is full
TRIGGER_DISTANCE_MM = 80

# Ip address
ipaddress = IP_address()

# options
# 1 - read each sensor once per full call
# 2 - have app stream sensor values to MiniFi via File, TCP, MQTT, REST

# bh1745
bh1745 = BH1745()
bh1745.setup()
bh1745.set_leds(1)
r, g, b, c = bh1745.get_rgbc_raw()
bh1745.set_leds(0)

# VL53L1X
tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
tof.open() # Initialise the i2c bus and configure the sensor
tof.start_ranging(2) # Start ranging, 1 = Short Range, 2 = Medium Range, 3 = Long Range
tof.stop_ranging() # Stop ranging
distance_in_mm = tof.get_distance() # Grab the range in mm
distance_in_mm = min(MAX_DISTANCE_MM, distance_in_mm) # Cap at our MAX_DISTANCE
    
# ltr559
lux = ltr559.get_lux()
prox = ltr559.get_proximity()
        
# bme680
try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except IOError:
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)
            
# lsm303d
lsm = LSM303D(0x1d)
lsm3accl = lsm.accelerometer()
lsm3mag = lsm.magnetometer()
    
# start camera
time.sleep(0.5)
cap = cv2.VideoCapture(0)  
time.sleep(3)

# loop forever
#try:
while True:
     row = { }
     distance_in_mm = tof.get_distance() # Grab the range in mm
	 distance_in_mm = min(MAX_DISTANCE_MM, distance_in_mm) # Cap at our MAX_DISTANCE
	 lsm3accl = lsm.accelerometer()
     lsm3mag = lsm.magnetometer()
     lux = ltr559.get_lux()
     prox = ltr559.get_proximity()
     bh1745.set_leds(1)
     r, g, b, c = bh1745.get_rgbc_raw()
     bh1745.set_leds(0)
     ret, frame = cap.read()
     uuid2 = '{0}_{1}'.format(strftime("%Y%m%d%H%M%S",gmtime()),uuid.uuid4())
     filename = 'images/bog_image_{0}.jpg'.format(uuid2)
     filename2 = 'images/bog_image_p_{0}.jpg'.format(uuid2)
     cv2.imwrite(filename, frame)
     cpuTemp=int(float(getCPUtemperature()))
     end = time.time()
     row['imgname'] = filename
     row['imgnamep'] = filename2
     row['host'] = os.uname()[1]
     row['cputemp'] = round(cpuTemp,2)
     row['ipaddress'] = ipaddress
     row['end'] = '{0}'.format( str(end ))
     row['te'] = '{0}'.format(str(end-start))
     row['BH1745_red'] = '{:3.1f}'.format(r)
     row['BH1745_green'] = '{:3.1f}'.format(g)
     row['BH1745_blue'] = '{:3.1f}'.format(b)
     row['BH1745_clear'] = '{:3.1f}'.format(c)
     row['VL53L1X_distance_in_mm'] = distance_in_mm
     row['ltr559_lux'] = '{:06.2f}'.format(lux)
     row['ltr559_prox'] = '{:04d}'.format(prox)
     row['bme680_tempc'] = '{0:.2f}'.format(sensor.data.temperature)
     row['bme680_tempf'] = '{0:.2f}'.format((sensor.data.temperature * 1.8) + 32)
     row['bme680_pressure'] = '{0:.2f}'.format(sensor.data.pressure)
     row['bme680_humidity'] = '{0:.3f}'.format(sensor.data.humidity)
     row['lsm303d_accelerometer'] = "{:+06.2f}g : {:+06.2f}g : {:+06.2f}g".format(*lsm3accl)
     row['lsm303d_magnetometer'] = "{:+06.2f} : {:+06.2f} : {:+06.2f}".format(*lsm3mag)           
     row['systemtime'] = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')      
     row['starttime'] = starttime  
     usage = psutil.disk_usage("/")
     row['diskusage'] = "{:.1f}".format(float(usage.free) / 1024 / 1024)
     row['memory'] = psutil.virtual_memory().percent
     row['uuid'] = str(uuid2)
     json_string = json.dumps(row)  
     json_string += str("\n")
     send_tcp(ipaddress, json_string)
     json_string = ""
     with canvas(oled) as draw:
         draw.rectangle(oled.bounding_box, outline="white", fill="black")
         draw.text((0, 0), "- Apache NiFi MiniFi -", fill="white")
         draw.text((0, 10), ipaddress, fill="white")
         draw.text((0, 20), starttime, fill="white")
         draw.text((0, 30), 'Temp: {}'.format( sensor.data.temperature ), fill="white")
         draw.text((0, 40), 'Humidity: {}'.format( sensor.data.humidity ), fill="white")  
         draw.text((0, 50), 'Pressure: {}'.format( sensor.data.pressure ), fill="white")    
         draw.text((0, 60), 'Distance: {}'.format(str(distance_in_mm)), fill="white")      
         draw.text((0, 70), 'CPUTemp: {}'.format( cpuTemp ), fill="white")      
         draw.text((0, 80), 'TempF: {}'.format( row['bme680_tempf'] ), fill="white") 
         draw.text((0, 90), 'A: {}'.format(row['lsm303d_accelerometer']), fill="white") 
         draw.text((0, 100), 'M: {}'.format(row['lsm303d_magnetometer']), fill="white") 
         draw.text((0, 110), 'DU: {}'.format(row['diskusage']), fill="white") 
         time.sleep(0.5)
#except:
#     print("Fail to send.")        
