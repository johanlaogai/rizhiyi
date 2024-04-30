from datetime import datetime, timedelta
import requests
import json

src_ip = "10.9.9.202"
base_url="http://{}:8090/api/v2{}"
user = "admin"
password = "admin@rizhiyi.com"  
auth = (user,password)
headers = {"Content_Type": "application/json"}


def get_agent():
    url_profix = '/agent/'
    response = get_request(url_profix,src_ip,{"group_ids": "all","size":400})
    for item in response['objects']:
        if item['status'] == "Running" and item['ip'] != "" and is_not_expired(item['last_update_timestamp']) and item['platform']=="win-386":
            ip_port = "{}:{}".format(item['ip'],item['port'])
            yield ip_port


def is_not_expired(lasttime):
    ts_datetime = datetime.strptime(lasttime, "%Y-%m-%dT%H:%M:%S")  
    current_time = datetime.now()  
    time_difference = current_time - ts_datetime  
    return time_difference <= timedelta(minutes=15)
    

def check_config(params={}):
    url_profix = '/agent/config/'
    response = get_request(url_profix,src_ip,params)
    return response


def get_request(url_profix,ip,params={}):
    full_url = base_url.format(ip,url_profix)
    response = requests.get(url=full_url,auth=auth,params=params,timeout=10)
    formatted = json.loads(response.text)
    return formatted


if __name__ == "__main__":
    # with open('/data/rizhiyi/logs/heka/failed_update.json','r') as fp:
    #     data = json.load(fp)
    # for item in data.keys():
    #     try:
    #         accum = 0
    #         ip_port = "{}:10001".format(item)
    #         content = check_config({"ip_port":ip_port})
    #         for item in content['objects']:
    #             if item['type'] == "WinlogInput":
    #                 accum += 1
    #         if accum>4:
    #             print("deduplication"+ip_port)
    #         else:
    #             print("good"+ip_port)
    #     except Exception:
    #         print("disconnection"+ip_port)
    ip_port = "10.17.8.121:10001"
    content = check_config({"ip_port":ip_port})
    print(content)

