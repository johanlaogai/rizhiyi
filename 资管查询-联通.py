import requests  
import json  
import copy

asset_dict = {
    'asset_end_time': '',
    'asset_start_time': '',
    'create_time': '',
    'select_count': '',
    'status': '',
    'task_id': '',
    'task_type': '',
    'task_type_str': '',
    'upload_time': '',
    'total': ''
}

def login():
    # 登录URL  
    url = 'https://10.120.53.212:443/api/v1/login'  
    # 准备POST数据  
    data = {  
        'username': 'superapi',   
        'password': 'WebRAY@497'  
    }  
    headers = {  'Content-Type': 'application/x-www-form-urlencoded'  }  
    # 发送POST请求  
    response = requests.post(url, data=data, verify=False)  # 使用verify=False跳过SSL验证 
    response.raise_for_status()  # 如果请求返回了不成功的状态码，将引发HTTPError异常 
    data = response.json()['data'] 
    print(data)
    return data['csrf_token'],data['sid']


def query_data():
    # 查询URL  
    url = 'https://10.120.53.212:443/api/v1/openapi/manage_instuct/query'  
    # 设置请求头  
    headers = { 'Content-Type': 'multipart/form-data'}  
    csrf_token,sid = login()
    headers['X-CSRFToken'] = csrf_token
    headers['Cookie'] = "sid="+sid
    # 发送POST请求  
    response = requests.post(url, headers=headers, verify=False)  
    data = response.json()['data']['data']
    write_csv(44,data,asset_dict)


def write_csv(id,query_result,model):
    url = "http://10.120.54.228:8090/api/v2/dictionaries/upload/"
    res = []
    res.append(",".join(model.keys()))
    for item in query_result:
        content = copy.deepcopy(model) 
        content.update(item)
        for i,j in content.items():
            if not isinstance(j,int):
                content[i] = str(j)
        res.append(",".join(content.values()))
    data = {
        "dictionary_id": id,
        "content": "\n".join(res)
    }
    headers = {'Content-Type': 'application/json'}  
    auth = ("admin","Cug#13579@hk")
    # 将数据转换为JSON字符串  
    json_data = json.dumps(data)
    response = requests.post(url, data=json_data,auth=auth,headers=headers)  
    print(response.text)

query_data()