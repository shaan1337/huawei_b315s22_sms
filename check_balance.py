import requests
import re
import hashlib
import base64
import html
import time
import telegram
import config
from datetime import datetime

ok_response = '<?xml version="1.0" encoding="UTF-8"?><response>OK</response>'

def get_csrf_tokens(session):
    response = session.get('http://{0}'.format(config.host))
    content = response.content.decode('utf-8')
    pattern = '<meta name="csrf_token" content="(.*)"\/>'
    return re.findall(pattern, content)

def login(session):
    print('login: fetching csrf tokens')
    csrf_tokens = get_csrf_tokens(session)

    pass_hash = base64.b64encode(hashlib.sha256(config.password.encode('utf-8')).hexdigest().encode('utf-8')).decode('utf-8')
    user_pass_token = config.username + pass_hash + csrf_tokens[0]
    user_pass_token_hash = base64.b64encode(hashlib.sha256(user_pass_token.encode('utf-8')).hexdigest().encode('utf-8')).decode('utf-8')
    request_data = '<?xml version="1.0" encoding="UTF-8"?><request><Username>{0}</Username><Password>{1}</Password><password_type>4</password_type></request>'.format(config.username, user_pass_token_hash)

    print('login: sending request')
    headers = {
          'X-Requested-With': 'XMLHttpRequest',
          '__RequestVerificationToken' : csrf_tokens[0]
    }

    response = session.post('http://{0}/api/user/login'.format(config.host),
                        data=request_data,
                        headers = headers)
    
    if response.content.decode('utf-8').replace('\r\n', '') != ok_response:
        print('Unexpected response: {0}'.format(response.content.decode('utf-8')))
        exit(1)
    print('login: succeeded')

def send_sms(session, recipient, message):
    print('send_sms: fetching csrf tokens')
    csrf_tokens = get_csrf_tokens(session)
    date = datetime.now().isoformat().replace('T',' ')[:19]
    request_data = '<?xml version="1.0" encoding="UTF-8"?><request><Index>-1</Index><Phones><Phone>{0}</Phone></Phones><Sca></Sca><Content>{1}</Content><Length>{2}</Length><Reserved>1</Reserved><Date>{3}</Date></request>'.format(
        recipient, message, len(message), date
    )
    headers = {
          'X-Requested-With': 'XMLHttpRequest',
          '__RequestVerificationToken' : csrf_tokens[0]
    }
    print('send_sms: sending request')
    response = session.post('http://{0}/api/sms/send-sms'.format(config.host),
                        data=request_data,
                        headers = headers)
    if response.content.decode('utf-8').replace('\r\n', '') != ok_response:
        print('Unexpected response: {0}'.format(response.content.decode('utf-8')))
        exit(1)
    print('send_sms: succeeded')

def read_last_sms(session):
    print('read_last_sms: fetching csrf tokens')
    csrf_tokens = get_csrf_tokens(session)
    date = datetime.now().isoformat().replace('T',' ')[:19]
    request_data = '<?xml version="1.0" encoding="UTF-8"?><request><PageIndex>1</PageIndex><ReadCount>1</ReadCount><BoxType>1</BoxType><SortType>0</SortType><Ascending>0</Ascending><UnreadPreferred>0</UnreadPreferred></request>'
    headers = {
          'X-Requested-With': 'XMLHttpRequest',
          '__RequestVerificationToken' : csrf_tokens[0]
    }
    print('read_last_sms: sending request')
    response = session.post('http://{0}/api/sms/sms-list'.format(config.host),
                        data=request_data,
                        headers = headers)
    response_content = response.content.decode('utf-8')
    message = html.unescape(re.findall('<Content>(.*?)</Content>', response_content)[0])
    print('read_last_sms: succeeded')
    return message

def send_telegram_msg(message):
    print('send_telegram_msg: sending message')
    bot = telegram.Bot(token=config.telegram_token)
    bot.sendMessage(chat_id=config.telegram_chat_id, text=message, timeout=60)
    print('send_telegram_msg: done')

def passes_conditions(message):
    try:
        balance = float(re.findall('Balance: Rs (.*?) on number', message)[0])
        print('passes_conditions: balance = {0}'.format(balance))
        day_of_week = datetime.today().weekday()
        print('passes_conditions: day_of_week = {0}'.format(day_of_week))
        return day_of_week == config.day_of_week_to_always_send or balance <= config.low_balance_threshold
    except:
        return True #fail-safe message send

def sleep():
    print('sleep: 15 seconds')
    time.sleep(15)

session = requests.Session()
login(session)
send_sms(session, config.sms_recipient, config.sms_message)
sleep()
msg = read_last_sms(session)
if passes_conditions(msg):
    send_telegram_msg(msg)