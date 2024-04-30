from datetime import datetime, timedelta
import requests
import json

src_ip = "192.168.40.105"
# base_url="http://{}:8090/api/v2{}"
base_url="http://{}/api/v0{}"
# http://192.168.40.105/api/v0
user = "admin"
password = "admin@rizhiyi.com"  
auth = (user,password)
headers = {"Content_Type": "application/json"}


def get_agent():
    url_profix = '/agent/'
    response = get_request(url_profix,src_ip,{"group_ids": "all"})
    for item in response['objects']:
        # print(item)
        if item['status'] == "Running" and item['ip'] != "" and is_expired(item['last_update_timestamp']):
            ip_port = "{}:{}".format(item['ip'],item['port'])
            if check_config({"ip_port": ip_port, "type": "LogstreamerInput"}) or check_config({"ip_port": ip_port}):
                print("ip:",item['ip'],",端口：",item['port'],",系统类型：",item['os'],",平台：",item['platform'])
            

def is_expired(lasttime):
    ts_datetime = datetime.strptime(lasttime, "%Y-%m-%dT%H:%M:%S")  
    current_time = datetime.now()  
    time_difference = current_time - ts_datetime  
    return time_difference <= timedelta(minutes=15)
    

def check_config(params={}):
    url_profix = '/agent/config/'
    response = get_request(url_profix,src_ip,params)
    print(response)
    return response['objects'] == []


def get_request(url_profix,ip,params={}):
    full_url = base_url.format(ip,url_profix)
    response = requests.get(url=full_url,auth=auth,params=params)
    formatted = json.loads(response.text)
    return formatted


if __name__ == "__main__":
    # get_agent()
    # ?action=getFullConfig&ip_port=192.168.1.19:10006
    url_profix = '/agent/talk_to_agent/'
    res = get_request(url_profix,src_ip,{"action":'getFullConfig','ip_port':'192.168.1.19:10006'})
    print(res)