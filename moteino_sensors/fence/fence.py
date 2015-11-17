#!/usr/bin/env python
import json
import logging
import requests
import threading
import time

from moteino_sensors import mqtt
from moteino_sensors import utils

class FenceThread(mqtt.MqttThread):
  def __init__(self, conf):
    super(FenceThread, self).__init__()
    self.name = 'fence'
    self.enabled = threading.Event()
    self.enabled.set()
    self.conf = conf
    self.mqtt_config = conf['mqtt']
    self.start_mqtt()

  def run(self):
    LOG.info('Starting')
    self.loop_start()
    while True:
      self.enabled.wait()
      req = api_request(self.conf['geo_api'], auth=(self.conf['geo_user'], self.conf['geo_pass']))
      if req:
        self._check_action(req)
      elif self.status.get('armed') == 0:
        self._set_armed()
      time.sleep(self.conf['loop_time'])

  def _check_action(self, data):
    status = {
      'enter': 0,
      'exit': 0,
    }
    for device in data:
      action = data[device]['action']
      if device in self.conf['geo_devices']:
        if self.conf['enter_status'] == action:
          status['enter'] += 1
        elif self.conf['exit_status'] == action:
          status['exit'] += 1

    armed = self.status.get('armed')
    if (armed == 1) and (status['enter'] > 0):
      LOG.info('Disarm alarm')
      self._unset_armed()
    elif (armed == 0) and (status['exit'] == len(self.conf['geo_devices'])):
      LOG.info('Arm alarm')
      self._set_armed()

  def _set_armed(self):
    self.publish_status({'armed': 1})

  def _unset_armed(self):
    self.publish_status({'armed': 0})


def api_request(url, method='GET', params=None, data=None, auth=None, headers=None, verify_ssl=False):
  try:
    req = requests.request(method, url, params=params,
            data=data, headers=headers, auth=auth, verify=verify_ssl, timeout=2)
    req.raise_for_status()
  except (requests.HTTPError, requests.ConnectionError, requests.exceptions.Timeout) as e:
    LOG.error('Fail to connect to url %s', e)
    return {}
  try:
    data = json.loads(req.text)
  except (ValueError) as e:
    return {}
  return data


LOG = logging.getLogger(__name__)


def main():
  parser = utils.create_arg_parser('Fence')
  args = parser.parse_args()

  conf = utils.load_config(args.dir + '/global.config.json')

  utils.create_logger(logging.INFO)
  logging.getLogger("requests").setLevel(logging.CRITICAL)
  requests.packages.urllib3.disable_warnings()

  fence = FenceThread(conf=conf)
  fence.start()


if __name__ == "__main__":
  main()
