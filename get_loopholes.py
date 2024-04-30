import requests
import json
import csv
import sys

url = 'http://192.168.40.104:8380/loopholes/info/unit/search'

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
                if result[2] == 'total':
                    # 将结果写入文件
                    result.append(asset_info['total_count'])
                elif result[2] == 'fixed':
                    total_fixed = 0
                    for info in asset_info['infos']:
                        if info["status"] == 1:
                            total_fixed+=1
                    result.append(total_fixed)
                
                # 处理返回的结果
                w.writerow(result)                   
            except Exception as e:
                pass

main()
# data = { "start_time": 1696574363000, "end_time": 1696919963000 }
# response = requests.post(url, headers=headers, data=json.dumps(data))
# asset_info = response.json()['data']
# total_fixed = 0
# for info in asset_info['infos']:
#     if info["status"] == 1:
#         total_fixed+=1
# print(total_fixed)