from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
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

import numpy as np
from six.moves import urllib
import tensorflow as tf
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

tf.logging.set_verbosity(tf.logging.ERROR)

FLAGS = None

 pylint: disable=line-too-long
DATA_URL = 'http://download.tensorflow.org/models/image/imagenet/inception-2015-12-05.tgz'
# pylint: enable=line-too-long

# yyyy-mm-dd hh:mm:ss
currenttime= strftime("%Y-%m-%d %H:%M:%S",gmtime())

host = os.uname()[1]

def randomword(length):
  return ''.join(random.choice(string.lowercase) for i in range(length))

class NodeLookup(object):
  """Converts integer node ID's to human readable labels."""

  def __init__(self,
               label_lookup_path=None,
               uid_lookup_path=None):
    if not label_lookup_path:
      label_lookup_path = os.path.join(
          '/tmp/imagenet', 'imagenet_2012_challenge_label_map_proto.pbtxt')
    if not uid_lookup_path:
      uid_lookup_path = os.path.join(
          '/tmp/imagenet', 'imagenet_synset_to_human_label_map.txt')
    self.node_lookup = self.load(label_lookup_path, uid_lookup_path)


  def load(self, label_lookup_path, uid_lookup_path):
    """Loads a human readable English name for each softmax node.

    Args:
      label_lookup_path: string UID to integer node ID.
      uid_lookup_path: string UID to human-readable string.

    Returns:
      dict from integer node ID to human-readable string.
    """
    if not tf.gfile.Exists(uid_lookup_path):
      tf.logging.fatal('File does not exist %s', uid_lookup_path)
    if not tf.gfile.Exists(label_lookup_path):
      tf.logging.fatal('File does not exist %s', label_lookup_path)

    # Loads mapping from string UID to human-readable string
    proto_as_ascii_lines = tf.gfile.GFile(uid_lookup_path).readlines()
    uid_to_human = {}
    p = re.compile(r'[n\d]*[ \S,]*')
    for line in proto_as_ascii_lines:
      parsed_items = p.findall(line)
      uid = parsed_items[0]
      human_string = parsed_items[2]
      uid_to_human[uid] = human_string

    # Loads mapping from string UID to integer node ID.
    node_id_to_uid = {}
    proto_as_ascii = tf.gfile.GFile(label_lookup_path).readlines()
    for line in proto_as_ascii:
      if line.startswith('  target_class:'):
        target_class = int(line.split(': ')[1])
      if line.startswith('  target_class_string:'):
        target_class_string = line.split(': ')[1]
        node_id_to_uid[target_class] = target_class_string[1:-2]

    # Loads the final mapping of integer node ID to human-readable string
    node_id_to_name = {}
    for key, val in node_id_to_uid.items():
      if val not in uid_to_human:
        tf.logging.fatal('Failed to locate: %s', val)
      name = uid_to_human[val]
      node_id_to_name[key] = name

    return node_id_to_name

  def id_to_string(self, node_id):
    if node_id not in self.node_lookup:
      return ''
    return self.node_lookup[node_id]


def create_graph():
  """Creates a graph from saved GraphDef file and returns a saver."""
  # Creates graph from saved graph_def.pb.
  with tf.gfile.FastGFile(os.path.join(
      '/tmp/imagenet', 'classify_image_graph_def.pb'), 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    _ = tf.import_graph_def(graph_def, name='')


def run_inference_on_image(image):
  """Runs inference on an image.

  Args:
    image: Image file name.

  Returns:
    row
  """
  if not tf.gfile.Exists(image):
    tf.logging.fatal('File does not exist %s', image)
  image_data = tf.gfile.FastGFile(image, 'rb').read()

  # Creates graph from saved GraphDef.
  create_graph()

  with tf.Session() as sess:
    # Some useful tensors:
    # 'softmax:0': A tensor containing the normalized prediction across
    #   1000 labels.
    # 'pool_3:0': A tensor containing the next-to-last layer containing 2048
    #   float description of the image.
    # 'DecodeJpeg/contents:0': A tensor containing a string providing JPEG
    #   encoding of the image.
    # Runs the softmax tensor by feeding the image_data as input to the graph.
    softmax_tensor = sess.graph.get_tensor_by_name('softmax:0')
    predictions = sess.run(softmax_tensor,
                           {'DecodeJpeg/contents:0': image_data})
    predictions = np.squeeze(predictions)

    # Creates node ID --> English string lookup.
    node_lookup = NodeLookup()

	tfrow  = { }

    top_k = predictions.argsort()[-1]
    human_string = node_lookup.id_to_string(top_k)
    score = predictions[top_k]
    tfrow['human_string'] =  str(human_string)
    tfrow['score'] = str(score)
    
    return tfrow


def maybe_download_and_extract():
  """Download and extract model tar file."""
  dest_directory = '/tmp'
  if not os.path.exists(dest_directory):
    os.makedirs(dest_directory)
  filename = DATA_URL.split('/')[-1]
  filepath = os.path.join(dest_directory, filename)
  if not os.path.exists(filepath):
    def _progress(count, block_size, total_size):
      sys.stdout.write('\r>> Downloading %s %.1f%%' % (
          filename, float(count * block_size) / float(total_size) * 100.0))
      sys.stdout.flush()
    filepath, _ = urllib.request.urlretrieve(DATA_URL, filepath, _progress)
    print()
    statinfo = os.stat(filepath)
    print('Successfully downloaded', filename, statinfo.st_size, 'bytes.')
  tarfile.open(filepath, 'r:gz').extractall(dest_directory)

# TODO:  send status message to screen
def do_nothing(obj):
    pass

def send_tcp(s, message):
    try:
        s.sendall(message)
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

TCP_PORT = 5005  # define somewhere
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ipaddress, TCP_PORT))

# tensorflow model
maybe_download_and_extract()

# start camera
time.sleep(0.5)
cap = cv2.VideoCapture(0)
time.sleep(3)

# loop forever
try:
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
     tfrow = run_inference_on_image(filename)
     end = time.time()
     row['human_string'] = tfrow['human_string']
     row['score'] = tfrow['score']
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
     send_tcp(s,json_string)
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
except:
     print("Fail to send.")
