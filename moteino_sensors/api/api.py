#!/usr/bin/env python
import json
import os
import time

import bottle
import bottle.ext.sqlite
import netaddr

from moteino_sensors import mqtt
from moteino_sensors import utils


app = bottle.Bottle()

@app.hook('after_request')
def after_request():
  bottle.response.headers['Access-Control-Allow-Origin'] = '*'


@app.hook('before_request')
def before_request():
  client_ip = bottle.request.environ['REMOTE_ADDR']
  allowed = bool(netaddr.all_matching_cidrs(client_ip, app.config['appconfig']['allowed_cidrs']))
  if not allowed:
    raise bottle.HTTPError(403, 'Forbidden')


@app.route('/')
@app.route('/front')
@app.route('/front/')
def redirect2index():
  bottle.redirect('/front/index.html')


@app.route('/front/<filepath:path>')
def static(filepath):
  return bottle.static_file(filepath, root=app.config['appconfig']['static_dir'])


@app.route('/api/action/status')
def get_action_status():
  return app.config['mqtt'].status


@app.route('/api/action/status', method=['POST'])
def set_action_status():
  data = bottle.request.json
  if data:
    app.config['mqtt'].publish_status(data)


@app.route('/api/action/mqtt', method=['POST'])
def set_action_mqtt():
  if (bottle.request.json):
    topic = bottle.request.json.get('topic')
    data = bottle.request.json.get('data')
    retain = bottle.request.json.get('retain', False)
    if topic and data:
      app.config['mqtt'].publish(topic, data, retain)


@app.route('/api/node', method=['GET', 'POST'])
@app.route('/api/node/', method=['GET', 'POST'])
@app.route('/api/node/<node_id>', method=['GET', 'POST'])
def get_nodes(db, node_id=False):
  now = int(time.time())
  start = now - 60 * 60 * 1
  end = now

  if (bottle.request.json):
    start = bottle.request.json.get('start', start)
    end = bottle.request.json.get('end', end)

  if (node_id):
    node_id = str(node_id)
    desc = dict(db.execute('SELECT board_id,board_desc FROM board_desc where board_id=?', (node_id, )).fetchall())
  else:
    desc = dict(db.execute('SELECT board_id,board_desc FROM board_desc').fetchall())

  output = list()
  for node in desc:
    o_metric = list()
    metrics = db.execute('SELECT sensor_type,data FROM last_metrics WHERE board_id=? and last_update >= ? and last_update <= ?',
      (node, start, end)).fetchall()
    for metric in metrics:
      o_metric.append(tuple(metric))
    output.append({"name": node, "desc": desc[node], "data": o_metric})

  return json.dumps(output)


@app.route('/api/graph/<graph_type>', method=['GET', 'POST'])
def get_graph(db, graph_type='uptime'):
  now = int(time.time())
  start = now - 60 * 60 * 24
  end = now
  last_available = 0

  if (bottle.request.json):
    start = bottle.request.json.get('start', start)
    end = bottle.request.json.get('end', end)
    last_available = bottle.request.json.get('last_available', last_available)

  graph_type = str(graph_type)

  nodes = db.execute('SELECT board_id FROM last_metrics WHERE sensor_type = ?', (graph_type, )).fetchall()

  output = list()

  for node in nodes:
    o_metric = list()
    node_id = node[0]

    desc = dict(db.execute('SELECT board_id,board_desc FROM board_desc WHERE board_id=?', (node_id, )).fetchall())
    metrics = db.execute('SELECT last_update,data FROM metrics WHERE sensor_type = ? AND board_id = ? AND last_update >= ? AND last_update <= ?',
      (graph_type, node_id, start, end)).fetchall()

    if (len(metrics) == 0 and last_available):
      metrics = db.execute('''SELECT last_update,data FROM (SELECT id,last_update,data from metrics WHERE
        sensor_type = ? AND board_id = ? ORDER BY id DESC LIMIT ?) order by id''',
        (graph_type, node_id, last_available)).fetchall()

    for metric in metrics:
      tmp = ((metric[0] * 1000), float(metric[1]))
      o_metric.append(tmp)

    output.append({"name": desc[node_id], "data": o_metric})

  return json.dumps(output)


class SyncThread(mqtt.MqttThread):
  def __init__(self, conf):
    super(SyncThread, self).__init__()
    self.app_config = conf
    self.daemon = True
    self.mqtt_config = conf['mqtt']
    self.start_mqtt()

  def run(self):
    while True:
      self.mqtt.loop()


def main():
  parser = utils.create_arg_parser('Moteino gateway API')
  args = parser.parse_args()

  api_config = utils.load_config(args.dir + '/global.config.json')

  # static_dir in config file should be specified only if
  # static files are located somewhere else than app package
  if not api_config.get('static_dir'):
      api_config['static_dir'] = os.path.join(os.path.dirname(__file__), 'static')

  app.config['appconfig'] = api_config

  app.config['mqtt'] = SyncThread(app.config['appconfig'])
  app.config['mqtt'].start()

  plugin = bottle.ext.sqlite.Plugin(dbfile=app.config['appconfig']['db'])
  app.install(plugin)

  app.run(host='0.0.0.0', port=8080, debug=app.config['appconfig']['debug'])


if __name__ == "__main__":
  main()
