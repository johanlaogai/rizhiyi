import json
import requests

dst_ip = "192.168.40.105"
base_url="http://{}:8090/api/v2{}"
user = "admin"
password = "admin@rizhiyi.com"
auth = (user,password)
headers = {"Content-Type": "application/json"}

def get_request(url_profix,ip,param=''):
    full_url = base_url.format(ip,url_profix)
    if param != '':
        response = requests.get(url=full_url,auth=auth,json=param,headers=headers)
    else:
        response = requests.get(url=full_url,auth=auth,headers=headers)
    return json.loads(response.text)

def isexist(dict_name):
    return get_request('/dictionaries/verify/',dst_ip,{'defination_name':dict_name})["object"]["is_duplicate"]




def update_dict():
    pass

def get_dict():
    res = get_request('/dictionaries/',dst_ip,{'defination_name__contains':'xxx'})
    return res

if __name__ == "__main__":
    if isexist('xx'):
        res = get_dict()
        dict_id = res['objects'][0]['id']
        param = {
            'defination_name': 'xxx',
            'file_name': 'xxx',
            'dictionary_id': dict_id,
            "content": 'xxxxxx'
        }

