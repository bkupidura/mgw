#!/usr/local/bin/python
import socket
import json
import time
import os
import netaddr
from datetime import datetime
import bottle
import bottle.ext.sqlite

def load_config(config_name):
  if not os.path.isfile(config_name):
    raise KeyError('Config {} is missing'.format(config_name))

  with open(config_name) as json_config:
    config = json.load(json_config)

  return config

conf = load_config('global.config.json')

app = bottle.Bottle()

def write2socket(data, response = False):
  client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  client.connect(conf['mgmt_socket'])
  client.send(data)
  if (response):
    return client.recv(1024)

@app.hook('after_request')
def after_request():
  bottle.response.headers['Access-Control-Allow-Origin'] = '*'

@app.hook('before_request')
def before_request():
  client_ip = bottle.request.environ['REMOTE_ADDR']
  allowed = bool(netaddr.all_matching_cidrs(client_ip, conf['allowed_cidrs']))
  if not allowed:
    raise bottle.HTTPError(403, 'Forbidden')

@app.route('/')
@app.route('/front')
@app.route('/front/')
def redirect2index():
  bottle.redirect('/front/index.html')

@app.route('/front/<filepath:path>')
def static(filepath):
  return bottle.static_file(filepath, root=conf['static_dir'])

@app.route('/api/action/status')
def get_action_status():
  output = write2socket('{"action": "status"}', response = True)
  return output

@app.route('/api/action/status', method = ['POST'])
def set_action_status():
  if (bottle.request.json):
    data = json.dumps(bottle.request.json)
    write2socket('{{"action": "set", "data": {}}}'.format(data))

@app.route('/api/action/invert_armed')
def get_action_invert_armed():
  status = json.loads(get_action_status())
  inverted = not int(status['armed'])
  write2socket('{{"action": "set", "data": {{"armed": "{}"}}}}'.format(int(inverted)))

@app.route('/api/node', method = ['GET', 'POST'])
@app.route('/api/node/', method = ['GET', 'POST'])
@app.route('/api/node/<node_id:int>', method = ['GET', 'POST'])
def get_nodes(db, node_id = False):
  now = int(time.time())
  start = now - 60*60*1
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
    metrics = db.execute('SELECT sensor_type,data FROM sensors WHERE board_id=? and last_update >= ? and last_update <= ? group by sensor_type',
      (node, start, end)).fetchall()
    for metric in metrics:
      o_metric.append(tuple(metric))
    output.append({"name": node, "desc": desc[node], "data": o_metric})
 
  return json.dumps(output)

@app.route('/api/graph/<graph_type>', method = ['GET', 'POST'])
def get_graph(db, graph_type = 'uptime'):
  now = int(time.time())
  start = now - 60*60*24
  end = now
  last_available = 0

  if (bottle.request.json):
    start = bottle.request.json.get('start', start)
    end = bottle.request.json.get('end', end)
    last_available = bottle.request.json.get('last_available', last_available);

  graph_type = str(graph_type)

  nodes = db.execute('SELECT DISTINCT(board_id) FROM sensors WHERE sensor_type = ?', (graph_type, )).fetchall()

  output = list()

  for node in nodes:
    o_metric = list()
    node_id = node[0]

    desc = dict(db.execute('SELECT board_id,board_desc FROM board_desc WHERE board_id=?', (node_id, )).fetchall())
    metrics = db.execute('SELECT last_update,data FROM sensors WHERE sensor_type = ? AND board_id = ? AND last_update >= ? AND last_update <= ?',
      (graph_type, node_id, start, end)).fetchall()

    if (len(metrics) == 0 and last_available):
      metrics = db.execute('''SELECT last_update,data FROM (SELECT id,last_update,data from sensors WHERE
        sensor_type = ? AND board_id = ? ORDER BY id DESC LIMIT ?) order by id''',
        (graph_type, node_id, last_available)).fetchall()

    for metric in metrics:
      tmp = ((metric[0]*1000), float(metric[1]))
      o_metric.append(tmp)

    output.append({"name": desc[node_id], "data": o_metric})

  return json.dumps(output)

plugin = bottle.ext.sqlite.Plugin(dbfile=conf['db'])
app.install(plugin)

app.run(host='localhost', port=8080, debug=conf['debug'])
