import requests
import json
import re
import sys

ti = []
dict = {}

def vt(ip):
    url = 'https://www.virustotal.com/api/v3/ip_addresses/{ip}'.format(ip=ip)
    headers = {"accept": "application/json",'x-apikey': '1fa6f1bd1e1082823383181501a5018f97b1352f8051537fa0150a57adeafcd9'}
    response = requests.get(url, headers=headers)
    r = json.loads(response.text)
    r['ip'] = ip
    return r


if __name__ == '__main__':
    query_data = sys.argv[1]
    query_list = query_data.split(",")
    result = []
    for ip in query_list:
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            continue
        try:
            result.append(vt(ip))
        except:
            pass
    dict['content'] = result
    print(json.dumps(dict))