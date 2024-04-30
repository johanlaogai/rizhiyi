import requests
import time
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

log_path = '/data/rizhiyi/logs/yunaq/'
# apiLog = logging.getLogger("api")
# apiLog.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename=os.path.join(log_path,'Run.log'))
# formatter = logging.Formatter('%(asctime)s - %(message)s')
# handler.setFormatter(formatter)
# apiLog.addHandler(handler)


try:
    for item in cf.items('domain_sid'):
        domain_name = item[0].split('_')[0]
        domain_sid = item[1]

        for ty in log_type:
            timestamp=int(time.time())
            date = time.strftime("%Y%m%d%H")
            
            content='date={}&date_type=hour&sid={}&time={}&type={}'.format(date,domain_sid,timestamp,ty)
            # content='date=2023071704&date_type=hour&sid={}&time={}&type={}'.format(domain_sid,timestamp,ty)
            h_mac=hmac.new(cf.get('script', 'api_key').encode('utf-8'),content.encode('utf-8'),hashlib.sha1)
            sign=h_mac.hexdigest()
            auth=HTTPBasicAuth(cf.get('script', 'api_id'),sign)

            data={
                'date':date,
                # 'date':2023071704,  #时间
                'date_type':'hour',
                'sid':domain_sid,
                'time':timestamp,
                'type':ty
            }

            # filename = os.path.join(log_path, domain_name + '_' + ty + '_' + str(date) + '.log.gz')
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), domain_name + ty + '_' + str(date) + '.log.gz')
            resp=requests.get(cf.get('script', 'url_download'),params=data,auth=auth,headers=headers,allow_redirects=True,timeout=30)
            
            if resp.text.startswith('{'): 
                print(json.loads(resp.text))
                # apiLog.info(resp.text)
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
    print(traceback.format_exc())
    # apiLog.exception(e.args)
    # apiLog.exception("===========")
    # apiLog.exception(traceback.format_exc())