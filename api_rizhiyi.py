import requests
import json
import csv

src_ip = "192.168.40.105"
base_url="http://{}:8090/api/v2{}"
auth = ("admin","admin@rizhiyi.com")
headers = {"CONTENT_TYPE":"application/x-www-form-urlencoded"}


def get_request(url_profix,ip):
    full_url = base_url.format(ip,url_profix)
    response = requests.get(url=full_url,auth=auth)
    formatted = json.loads(response.text)
    return formatted


def post_request(url_profix,params,ip):
    full_url = base_url.format(ip,url_profix)
    data = {
        'data': json.dumps(params)
    }
    response2 = requests.post(url=full_url, auth=auth, data=data, headers=headers)
    if json.loads(response2.text).get('result','') == True:
        print("创建成功")
    else:
        print("创建失败")
        print(response2.text)
        exit()


def create_same_report():
    report_replics = get_request('/reports/7/',src_ip)['object']   #使用者需要更改把7改为其他id
    template_content = json.loads(json.loads(report_replics['content']))  #原报表内容

    with open('./test/report.csv','r',encoding='utf8') as f:
        f_csv = csv.reader(f)  #生成csv迭代器
        col_types = [str,int,int,int,int,int] #类型转换
        header = list(convert(value) for convert, value in zip(col_types, next(f_csv))) #获取headers        
        for row in f_csv:  #获取每一行内容
            for i in zip(header,row):
                if isinstance(i[0],int):  
                    modify = template_content[i[0]-1]['data']
                    if modify.get('query',None) is not None:  
                        modify['query'] = i[1]
                        template_content[i[0]-1]['data'] = modify
                    else:
                        print("报表第",i[0],"列没覆盖，无法修改")
                if isinstance(i[0],str):
                    report_replics['name'] = i[1]
            report_replics['content'] = json.dumps(json.dumps(template_content))
            post_request('/reports/',report_replics,src_ip)


if __name__ == "__main__":
    create_same_report()