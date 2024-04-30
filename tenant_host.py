import requests
import json
import csv
import sys


url = 'http://10.120.54.231:8380/tenant/host/batch'

headers = {
    'Rizhiyi-User-ID': '1',
    'Content-Type': 'application/json'
}

def main():
    infile = sys.stdin
    outfile = sys.stdout
    r = csv.reader(infile)
    w = csv.writer(outfile)
    for result in r:
        if result:
            expired_time = int(result[0])
            data = [{"domain_name": "ops","domain_ip": "10.120.54.230","service_expired_time": expired_time},{"domain_name": "ops","domain_ip": "10.120.54.228","service_expired_time": expired_time},{"domain_name": "ops","domain_ip": "10.120.54.229","service_expired_time": expired_time},{"domain_name": "ops","domain_ip": "10.120.54.231","service_expired_time": expired_time},{"domain_name": "ops","domain_ip": "10.120.59.73","service_expired_time": expired_time},{"domain_name": "ops","domain_ip": "10.120.59.74","service_expired_time": expired_time},{"domain_name": "ops","domain_ip": "10.120.59.75","service_expired_time": expired_time},{"domain_name": "ops","domain_ip": "10.120.59.76","service_expired_time": expired_time}]
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                res = response.text
                # 将结果写入文件
                result.append(res)
                # 处理返回的结果
                w.writerow(result)                   
            except Exception as e:
                pass

main()