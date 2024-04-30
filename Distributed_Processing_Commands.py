import requests
import json
import csv
import re
import time

# src_ip = "172.51.246.173"
src_ip = "192.168.40.106"
base_url="http://{}:8090/api/v2{}"
# auth = ("admin","13579@nocGd")
auth = ("admin","admin@rizhiyi.com")
# headers = {"CONTENT_TYPE":"application/x-www-form-urlencoded"}
headers = {"CONTENT_TYPE":"application/json"}


def get_request(url_profix,ip):
    full_url = base_url.format(ip,url_profix)
    response = requests.get(url=full_url,auth=auth)
    formatted = json.loads(response.text)
    return formatted


def put_request(url_profix,params):
    full_url = base_url.format(src_ip,url_profix)

    response2 = requests.put(url=full_url, auth=auth, json=params, headers=headers)
    if json.loads(response2.text).get('result','') == True:
        print("更新成功")
    else:
        print("创建失败")
        print(response2.text)
        exit()


def post_request(url_profix,params):
    full_url = base_url.format(src_ip,url_profix)
    data = {'data': params}
    response2 = requests.post(url=full_url, auth=auth, data=data, headers=headers)
    if json.loads(response2.text).get('result','') == True:
        print("更新成功")
    else:
        print("创建失败")
        print(response2.text)
        exit()


def modify_report(report_url,report_object,name):
    print('开始更新SPL语句....')
    mapping_content = ''
    with open('./report.csv','r',encoding='utf8') as f:
        f_csv = csv.reader(f)  #生成csv迭代器
        headers = [int(value) for value in next(f_csv)]
        mapping_content = dict(zip(headers,next(f_csv)))  
        
    mapping_company = {}
    with open('./mapping_cp.csv','r',newline='') as file:  
        f_csv = csv.reader(file)
        for row in f_csv:
            mapping_company[row[0]] = row[1]

    report_object = json.loads(report_object)
    for index in mapping_content.keys():
        if report_object[index]['data'].get('trendName',None) is not None:
            report_object[index]['data']['query'] = mapping_content[index].replace('comany_name',mapping_company[name])
        else:
            print("没修改过的SPL,下标为：",index+1)
            print(report_object[index]['data'])
            
    data = {
        'content': json.dumps(report_object)
    }
            
    put_request(report_url,data)


def preview_result(report_object):
    print('开始下载预览....')
    report_url = "/reports/preview/?send_email=false"
    post_request(report_url,report_object)
    time.sleep(60)


def adjust_time(frequency="day",triggertime="000100"):
    """
    frequency:
    triggertime:
    """
    if frequency not in ("day","mon"):
        print("执行周期输入错误")
        exit()
    if len(triggertime) != 6:
        print("执行时间输入错误")
        exit()
    
    day = int(triggertime[0:2])
    hour = int(triggertime[2:4])
    minute = int(triggertime[4:])

    def accler(report_url,interval):
        print('开始更新执行时间....')
        nonlocal day,hour,minute
        total_minute = minute + interval
        minute = total_minute%60 if total_minute//60 >= 1 else total_minute 
        total_hour = total_minute//60 + hour
        hour = total_hour%24 if total_hour//24 >=1 else total_hour
        day += total_hour//31
        res = str(day).zfill(2) + str(hour).zfill(2) + str(minute).zfill(2)

        data = {
            'frequency': frequency,
            'triggertime': res
        }
        print(data)
        put_request(report_url,data)

    return accler


if __name__ == "__main__":
    #修改执行时间
    func = adjust_time(triggertime="000104")  
    report_replics = get_request('/reports/',src_ip)  
    for item in report_replics['objects']:    
        if item['name'].endswith("testtt"):
            print(item['name'],'开始更新....')
            # name = re.search(r'-\s*(\S+)\s*-',item['name']).group(1)
            report_url = "/reports/{}/".format(item['id'])
            item['content'] = json.loads(item['content'])
            #修改spl语句
            # modify_report(report_url,item['content'],name)
            # 修改执行时间
            func(report_url,5)  #5分钟
            # 预览下载
            item = json.dumps(item)
            preview_result(item)