import logging
import smtplib
import socket


LOG = logging.getLogger(__name__)


def send_mail(data, action_config):
  if not action_config.get('enabled'):
    return False

  if 'message' in data:
    msg = data['message']
  else:
    msg = '{sensor_type} on board {board_desc} ({board_id}) reports value {sensor_data}'.format(**data)

  LOG.info('Sending mail')

  message = "From: {sender}\nTo: {recipient}\nSubject: {subject}\n\n{msg}\n\n".format(msg=msg, **action_config)
  try:
    s = smtplib.SMTP(action_config['host'], action_config['port'], timeout=5)
    s.starttls()
    s.login(action_config['user'], action_config['password'])
    s.sendmail(action_config['sender'], action_config['recipient'], message)
    s.quit()
  except (socket.gaierror, socket.timeout, smtplib.SMTPAuthenticationError, smtplib.SMTPDataError) as e:
    LOG.warning("Got exception '%s' in send_mail", e)
    return False
  else:
    return True