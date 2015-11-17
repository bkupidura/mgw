#!/usr/bin/env python
import argparse
import logging
import re
import threading
import time

import serial

from moteino_sensors import mqtt
from moteino_sensors import utils

class SrlThread(mqtt.MqttThread):
  # [ID][metric:value] / [10][voltage:3.3]
  _re_sensor_data = re.compile(
    '\[(?P<board_id>\d+)\]\[(?P<sensor_type>.+):(?P<sensor_data>.+)\]')

  def __init__(self, serial, mqtt_config):
    super(SrlThread, self).__init__()
    self.name = 'srl'
    self.enabled = threading.Event()
    self.enabled.set()
    self.serial = serial
    self.mqtt_config = mqtt_config
    self.start_mqtt()

    self.mqtt.message_callback_add(self.mqtt_config['topic'][self.name]+'/write', self._on_message_write)

  def _on_message_write(self, client, userdata, msg):
    data = utils.load_json(msg.payload)
    LOG.debug("Got data for node '%s'", data)

    try:
      r_cmd = "{nodeid}:{cmd}".format(**data)
      self.serial.write(r_cmd)
    except (IOError, ValueError, serial.serialutil.SerialException) as e:
      LOG.error("Got exception '%s' in srl thread", e)

  def _read_sensors_data(self):
    data = {}
    try:
      s_data = self.serial.readline().strip()
      m = self._re_sensor_data.match(s_data)
      # {"board_id": 0, "sensor_type": "temperature", "sensor_data": 2}
      data = m.groupdict()
    except (IOError, ValueError, serial.serialutil.SerialException) as e:
      LOG.error("Got exception '%' in srl thread", e)
      self.serial.close()
      time.sleep(5)
      try:
        self.serial.open()
      except (OSError) as e:
        LOG.warning('Failed to open serial')
    except (AttributeError) as e:
      if len(s_data) > 0:
        LOG.debug('> %s', s_data)

    return data

  def run(self):
    LOG.info('Starting')
    self.loop_start()

    while True:
      self.enabled.wait()

      sensor_data = self._read_sensors_data()
      if not sensor_data:
        continue

      LOG.debug("Got data from serial '%s'", sensor_data)
      self.publish(self.mqtt_config['topic']['mgw']+'/metric', sensor_data)


LOG = logging.getLogger(__name__)

def main():
  parser = argparse.ArgumentParser(description='SRL - mgw serial')
  parser.add_argument('--dir', required=True, help='Root directory, should cotains *.config.json')
  args = parser.parse_args()

  conf = utils.load_config(args.dir + '/global.config.json')

  utils.create_logger(logging.INFO)

  ser = serial.Serial(
    conf['serial']['device'],
    conf['serial']['speed'],
    timeout=conf['serial']['timeout']
  )
  srl = SrlThread(
    serial=ser,
    mqtt_config=conf['mqtt'])

  srl.start()


if __name__ == "__main__":
  main()
