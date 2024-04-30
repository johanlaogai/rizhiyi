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
    infile = sys.stdin
    outfile = sys.stdout
    r = csv.reader(infile)
    w = csv.writer(outfile)
    for result in r:
        loophole_id = result[0]
        loophole_name = result[1].replace(":","-")
        description = ""
        solution = ""
        risk_level = 2
        siem_risk_level = 2
        app_classif = ""
        system_classif = ""
        cve_id = result[2]
        host = result[3]
        scanner_start_time = result[4]
        scanner_end_time = result[4]
        source = "360天擎"
        scan_id = result[5]
        loophole_tags =""
        data = {
            'loophole_id':loophole_id,
            'loophole_name':loophole_name,
            'description':description,
            'solution': solution,
            'risk_level': risk_level,
            'siem_risk_level': siem_risk_level,
            'app_classif': app_classif,
            'system_classif': system_classif,
            'cve_id': cve_id,
            'host': host,
            'scanner_start_time': scanner_start_time,
            'scanner_end_time': scanner_end_time,
            'source': source,
            'scan_id': scan_id,
            'loophole_tags': loophole_tags
        }
        data = json.dumps(data)
        headers = {
            'Content-Type': 'application/json',
            "Rizhiyi-User-ID": '1'
        }
        url = 'http://10.120.54.231:8380/loopholes/create'
        resp = requests.post(url=url, data=data, headers=headers)
        text = json.loads(resp.text)
        if text['code'] == 0:
            respdata = "请求成功"
        else:
            respdata = text
        result.append(respdata)
        w.writerow(result)
        time.sleep(1)
main()