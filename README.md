Python script to send an SMS with the Huawei B315s-22 LTE router and forward the SMS reply to a Telegram chat.  

In this particular context, the script is used to check the remaining balance and sends an alert either weekly or daily (depending on cron configuration) when the balance is below a certain threshold but it can be modified as needed.  

Tested with firmware version: *21.333.01.00.00*

### Pre-requisites
Python 3 with the following libraries:
- requests
- python-telegram-bot
- hashlib
- base64
- html

### Usage
1. Copy `config.py.example` to `config.py` and modify configuration parameters as required

2. Run it manually
```
$ python3 check_balance.py
```

3. Or add a cron job:
```
# run every day at 7 am
0 7 * * * python3 /path/to/check_balance.py
```

