# -*- coding: utf-8 -*-
# Author: Yottabyte
# Email: wu.guoquan@yottabyte.cn
# Date: 2023.06.26

import csv
import requests
import sys
import json
import time

def main():

    # data = {
    #     "host":"10.120.53.106",
    #     "loophole_name":"CVE-2020-8625",
    #     "scanner_start_time":"2023-07-03 04:31:23",
    #     "loophole_id":"QT012021000782",
    #     "risk_level":1,
    #     "siem_risk_level":1,
    #     "source":"青藤云"
    #     }
    data = {
        "host": "10.120.53.106", 
        "loophole_name": "CentOS 7 glib2 and ibus (CESA-2020 3978)", 
        "scanner_start_time": "2023-07-03 04:31:23", 
        "loophole_id": "QT012020004082", 
        "risk_level": "2", 
        "siem_risk_level": "2", 
        "source": "\u9752\u85e4\u4e91"
        }
    data = json.dumps(data)
    headers = {
        'Content-Type': 'application/json',
        'Rizhiyi-User-ID': '1'
    }
    url = 'http://10.120.54.231:8380/loopholes/create'
    resp = requests.post(url=url, data=data, headers=headers,timeout=30)
    text = json.loads(resp.text)
    if text['code'] == 0:
        respdata = "请求成功"
    else:
        respdata = text
    print(respdata)
main()