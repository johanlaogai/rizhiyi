import requests
import time
import datetime
import hmac
import traceback
import gzip
import os
import logging
import json
import hashlib
from requests.auth import HTTPBasicAuth
from configparser import ConfigParser


file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
cf = ConfigParser()
cf.read(file_path, encoding='utf-8')

log_type = ['access','attack','anticc']
headers={
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0'
}

url='https://defense.yunaq.com/api/v3/log_download'
domain_sid= '646dd8a4796db405258e42e4'
api_key = b'a0ec5459f26f4d5abbd64aba46a0f445'
api_id = '64ab857388304960328a319b'


# log_path = '/data/rizhiyi/logs/yunaq/'
# apiLog = logging.getLogger("api")
# apiLog.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename=os.path.join(log_path,'Run.log'))
# formatter = logging.Formatter('%(asctime)s - %(message)s')
# handler.setFormatter(formatter)
# apiLog.addHandler(handler)


try:
        
    timestamp=int(time.time())
    # date = time.strftime("%Y%m%d%H")
    date = (datetime.datetime.now()-datetime.timedelta(hours=2)).strftime("%Y%m%d%H")
    print(date)
    content='date={}&date_type=hour&sid={}&time={}&type=access'.format(date,domain_sid,timestamp)
    h_mac=hmac.new(api_key,content.encode('utf-8'),hashlib.sha1)
    sign=h_mac.hexdigest()
    auth=HTTPBasicAuth(api_id,sign)

    data={
        'date':date,
        # 'date':2023071704,  #时间
        'date_type':'hour',
        'sid':domain_sid,
        'time':timestamp,
        'type':'access'
    }

    filename = os.path.join(log_path, 'solution_access' + '_' + str(date) + '.log.gz')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), domain_name + ty + '_' + str(date) + '.log.gz')
    resp=requests.get(url,params=data,auth=auth,headers=headers,allow_redirects=True)
    
    if resp.text.startswith('{'): 
        print(json.loads(resp.text))
        # apiLog.info(json.loads(resp.text))
    elif resp.text != '\n':
        print(resp.text)
        with open(filename,'wb') as f:
            f.write(resp.content)
        f_name = filename.replace('.gz',"")
        g_file = gzip.GzipFile(filename)
        open(f_name,"wb+").write(g_file.read())
        g_file.close()
        os.remove(filename)

except Exception as e:
    # apiLog.exception(e.args)
    # apiLog.exception("===========")
    # apiLog.exception(traceback.format_exc())
    pass