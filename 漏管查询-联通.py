import requests  
import json  
import subprocess 
import copy

telTicList_dict = {
    'id': '',
    'orderID': '',
    'ispCode': '',
    'orgCode': '',
    'orderType': '',
    'orderSubType': '',
    'procTime': '',
    'starProcTime': '',
    'endProcTime': '',
    'createTime': '',
    'backTime': '',
    'vulRange': '',
    'vulInfoRange': '',
    'tktInfo': '',
    'srcTktProcer': '',
    'srcTktProcerDept': '',
    'tktPriority': '',
    'tkt_resp': ''
}

telTaskList_dict = {
    'id': '',
    'orderID': '',
    'ispCode': '',
    'orgCode': '',
    'orderType': '',
    'orderSubType': '',
    'procTime': '',
    'createTime': '',
    'backTime': '',
    'vulRange': '',
    'vulInfoRange': '',
    'tskInfo': '',
    'statusCode': '',
    'statusText': ''
}


def get_token():
    # 定义要执行的命令  
    command = "/opt/rizhiyi/java/bin/java -cp /opt:/opt/vms-auth-sdk-2.1.0.jar  BuildToken"
    # 使用subprocess.run()执行命令，并捕获输出  
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)  
    date,token,_ = result.stdout.split('\n')
    return date,token


def login():
    # 登录URL  
    url = 'https://10.120.59.93:3718/api/login2'  
    # 准备POST数据  
    data = {  
        'account': 'superapi',   
        'appId': 'demo'  
    }  
    date,token = get_token()
    data['dateTime'] = date
    data['token'] = token
    # 将数据转换为JSON字符串  
    json_data = json.dumps(data) 
    # 发送POST请求  
    response = requests.post(url, data=json_data, verify=False)  # 使用verify=False跳过SSL验证 
    response.raise_for_status()  # 如果请求返回了不成功的状态码，将引发HTTPError异常  
    return response.headers['token']


def query_data():
    # 查询URL  
    url = 'https://10.120.59.93:3718/api/va/tel/queryOrder'  
    # 设置请求头  
    headers = {'Content-Type': 'application/json'}  
    headers['Authorization'] = login()
    # 发送POST请求  
    response = requests.post(url, headers=headers, verify=False)  
    telTicList = response.json()['content']['telTicList']
    telTaskList = response.json()['content']['telTaskList']
    write_csv(41,telTicList,telTicList_dict)
    write_csv(42,telTaskList,telTaskList_dict)


def write_csv(id,query_result,model):
    url = "http://10.120.54.228:8090/api/v2/dictionaries/upload/"
    res = []
    res.append(",".join(model.keys()))
    for item in query_result:
        content = copy.deepcopy(model) 
        content.update(item)
        for i,j in content.items():
            if isinstance(j,int):
                content[i] = str(j)
            else:
                content[i] = content[i].replace('\n','<br>')
        res.append(",".join(content.values()))
    data = {
        "dictionary_id": id,
        "content": "\n".join(res)
    }
    headers = {'Content-Type': 'application/json'}  
    auth = ("admin","Cug#13579@hk")
     # 将数据转换为JSON字符串  
    json_data = json.dumps(data)
    response = requests.post(url, data=json_data,auth=auth,headers=headers)  # 使用verify=False跳过SSL验证 
    print(response.text)

query_data()