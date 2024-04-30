import hmac
import hashlib
import requests
import json
import os
import time
from requests.auth import HTTPBasicAuth
from configparser import ConfigParser

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
cf = ConfigParser()
cf.read(file_path, encoding='utf-8')


# for item in cf.items('domain'):
#     domain_name = item[1]
timestamp=int(time.time())
content='time={}'.format(timestamp)
h_mac=hmac.new(cf.get('script', 'api_key').encode('utf-8'),content.encode('utf-8'),hashlib.sha1) 
sign=h_mac.hexdigest()

data={
# 'domain':domain_name,
'time':timestamp
}

auth=HTTPBasicAuth(cf.get('script', 'api_id'),sign)
res=requests.get(cf.get('script', 'url_query'),params=data,auth=auth)
rsep = json.loads(res.text)
print(rsep)
if rsep['status'] != "success":
    print("request error:",rsep['message'])
    exit(1)
for index,mesg in enumerate(rsep['data']['sites']):
    cf.set('domain_sid', mesg['domain']+'_'+str(index), mesg['id'])

cf.write(open(file_path, 'w'))