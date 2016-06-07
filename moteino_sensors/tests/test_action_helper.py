import copy
import os
import sys

import pytest

from moteino_sensors.executor import executor
from moteino_sensors import utils

default_sensor_config = {
  'priority': 100,
  'value_count': 1,
  'actions': [
    {'check_status': {
      'armed': 'lambda x: int(x)==1',
    },
    'action_interval': 0,
    'threshold': 'lambda x: True',
    'fail_count': 0,
    'fail_interval': 0,
    'message_template': 'Template message for {board_id}',
    'action': [{'name': 'action'}],
    'action_config': {'action_name': {'test': 10}},
    'board_ids': [],
    }
  ]
}


board_id = '1'
check_status_test_data = (
  (
    {
        'armed': 'lambda x: int(x)==1',
    },
    True
  ),
  (
    {
        'armed': 'lambda x: int(x)==1',
        'fence': 'lambda x: int(x)==0',
    },
    True
  ),
  (
    {
        'armed': 10,
    },
    False
  ),
  (
    {
        'armed': {},
    },
    False
  ),
  (
    {
        'armed': [],
    },
    False
  ),
  (
    {
        'armed': None,
    },
    False
  )
)

@pytest.mark.parametrize('check_status, expected', check_status_test_data)
def test_should_check_status(check_status, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['check_status'] = check_status

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

actions_test_data = (
  (
    [],
    False
  ),
  (
    [{}],
    False
  ),
  (
    'asd',
    False
  ),
  (
    10,
    False
  ),
  (
    [10],
    False
  ),
  (
    [{'asd': 10}],
    False
  )
)

@pytest.mark.parametrize('check_actions, expected', actions_test_data)
def test_actions(check_actions, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'] = check_actions

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

config_for_board_test_data = (
  (
    'asd',
    False
  ),
  (
    ['asd'],
    False
  ),
  (
    ['asd-1'],
    False
  ),
  (
    [],
    True
  ),
  (
    [board_id, ],
    True
  ),
  (
    [board_id, 'asd'],
    True
  ),
)

@pytest.mark.parametrize('board_ids, expected', config_for_board_test_data)
def test_config_for_board(board_ids, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['board_ids'] = board_ids

  ada = executor.SensorActionAdapter(sensor_config['actions'][0])

  assert ada.action_for_board(board_id) == expected

board_ids_test_data = (
  (
    ['test'],
    True
  ),
  (
    ['test-1'],
    False
  ),
  (
    '',
    False
  ),
  (
    10,
    False
  ),
  (
    [],
    True
  ),
  (
    [1, ],
    False
  ),
  (
    {},
    False
  ),
  (
    {'test': 10},
    False
  ),
  (
    None,
    False
  ),
  (
    True,
    False
  ),
  (
    False,
    False
  )
)

@pytest.mark.parametrize('board_ids, expected', board_ids_test_data)
def test_board_ids(board_ids, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['board_ids'] = board_ids

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

dict_of_dict_test_data = (
  (
    {},
    True
  ),
  (
    {'1': {'1': 'asd'}},
    True
  ),
  (
    {'1': 10},
    False
  ),
  (
    {'1': {'1': 'asd'}, '2': []},
    False
  ),
  (
    [],
    False
  ),
  (
    [1],
    False
  ),
  (
    'asd',
    False
  ),
)

@pytest.mark.parametrize('action_config, expected', dict_of_dict_test_data)
def test_action_config(action_config, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['action_config'] = action_config

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

integer_bigger_than_0_test_data = (
  (
    10,
    True
  ),
  (
    0,
    True
  ),
  (
    -10,
    False
  ),
  (
    'asd',
    False
  ),
  (
    [],
    False
  ),
  (
    [1, ],
    False
  ),
  (
    {},
    False
  ),
  (
    {'test': 10},
    False
  ),
  (
    None,
    False
  ),
)

@pytest.mark.parametrize('action_interval, expected', integer_bigger_than_0_test_data)
def test_action_interval(action_interval, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['action_interval'] = action_interval

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

@pytest.mark.parametrize('fail_count, expected', integer_bigger_than_0_test_data)
def test_fail_count(fail_count, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['fail_count'] = fail_count

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

@pytest.mark.parametrize('fail_interval, expected', integer_bigger_than_0_test_data)
def test_fail_interval(fail_interval, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['fail_interval'] = fail_interval

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

@pytest.mark.parametrize('priority, expected', integer_bigger_than_0_test_data)
def test_priority(priority, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['priority'] = priority

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

@pytest.mark.parametrize('value_count, expected', integer_bigger_than_0_test_data)
def test_value_count(value_count, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['value_count'] = value_count

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

not_empty_string_test_data = (
  (
    'test',
    True
  ),
  (
    '',
    False
  ),
  (
    10,
    False
  ),
  (
    [],
    False
  ),
  (
    [1, ],
    False
  ),
  (
    {},
    False
  ),
  (
    {'test': 10},
    False
  ),
  (
    None,
    False
  ),
  (
    True,
    False
  ),
  (
    False,
    False
  ),
)

@pytest.mark.parametrize('threshold, expected', not_empty_string_test_data)
def test_threshold(threshold, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['threshold'] = threshold

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

@pytest.mark.parametrize('message_template, expected', not_empty_string_test_data)
def test_message_template(message_template, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['message_template'] = message_template

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

action_test_data = (
  (
    [{'name': 'test'}],
    True
  ),
  (
    [{'name': 'test'}, {'name': 'test2'}],
    True
  ),
  (
    [{'name': 'test', 'failback': [{'name': 'test2'}]}, {'name': 'test3'}],
    True
  ),
  (
    [{'name': 'test', 'failback': [{'name': 'test2', 'failback': [{'name': 'test3'}]}, {'name': 'test4'}]}],
    True
  ),
  (
    [],
    False
  ),
  (
    10,
    False
  ),
  (
    [10],
    False
  ),
  (
    [1, ],
    False
  ),
  (
    {},
    False
  ),
  (
    [{}],
    False
  ),
  (
    {'test': 10},
    False
  ),
  (
    [{'test': 10}],
    False
  ),
  (
    None,
    False
  ),
  (
    [None],
    False
  ),
  (
    True,
    False
  ),
  (
    [True],
    False
  ),
  (
    False,
    False
  ),
  (
    [False],
    False
  ),
  (
    [{'name': 'test'}, {'action': 'test2'}],
    False
  ),
  (
    [{'name': 10}],
    False
  ),
  (
    [{'name': None}],
    False
  ),
  (
    [{'name': False}],
    False
  ),
  (
    [{'name': 'test', 'failback': [{'action': 'test2'}]}, {'name': 'test3'}],
    False
  ),
)

@pytest.mark.parametrize('action, expected', action_test_data)
def test_action(action, expected):
  sensor_config = copy.deepcopy(default_sensor_config)
  sensor_config['actions'][0]['action'] = action

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == expected

default_test_data = (
  (
    {
      'actions': [
        {
          'action': [
            {'name': 'test'}
          ]
        }
      ]
    },
    {
      "priority": 500,
      "value_count": 0,
      "actions": [
        {
          "action_interval": 0,
          "check_status": {},
          "threshold": "lambda: True",
          "fail_count": 0,
          "fail_interval": 600,
          "message_template": "{sensor_type} on board {board_desc} ({board_id}) reports value {sensor_data}",
          "action_config": {},
          "board_ids": [],
          "action": [
            {"name": "test"}
          ]
        }
      ]
    }
  ),
)

@pytest.mark.parametrize('default, expected', default_test_data)
def test_default_values(default, expected):
  sensor_config = default

  ada, data = utils.validate_sensor_config(sensor_config)

  assert ada == True
  assert data == expected
