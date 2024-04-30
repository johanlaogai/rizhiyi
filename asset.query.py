import requests
import json
import csv
import sys

url = 'http://10.120.54.231:8380/issue/statistics'

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
            # 计算 starttime 和 endtime
            data = { "start_time": int(result[0]), "end_time": int(result[1]) }
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                asset_info = response.json()['data']
                # 将结果写入文件
                result.append(asset_info['total_num'])
                result.append(asset_info['high_num'])
                result.append(asset_info['mid_num'])
                result.append(asset_info['low_num'])
                result.append(asset_info['pend_num'])
                result.append(asset_info['process_num'])
                result.append(asset_info['closed_num'])
                # 处理返回的结果
                w.writerow(result)                   
            except Exception as e:
                pass

main()



