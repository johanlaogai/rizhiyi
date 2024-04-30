import requests
import logging
import json
import time
import os


uuids = None
uuid_ip = None

log_path = '/data/rizhiyi/logs/api/'
uuidIp_path = '/data/rizhiyi/spldata/dictionary/1/files/'
apiLog = logging.getLogger("api")
apiLog.setLevel(logging.DEBUG)


def init():
    leveldict = [
        {'level' : logging.INFO, 'filename' : 'Access.log'},
        {'level' : logging.ERROR, 'filename' : 'Error.log'}
    ]
    
    for ldict in leveldict:
        level, filename = ldict.values()
        handler = logging.FileHandler(filename=os.path.join(log_path,filename))
        handler.setLevel(level=level)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        apiLog.addHandler(handler)
        

def send_req(uri):  #发送请求
    try:
        url = "https://10.49.56.73:8080{uri}?find={params}"
        headers = {"Content-Type":"application/json"}
        errorMsg = {400:'请求参数有误',401:'认证授权失败',403:'被禁止授权访问'}
        user = "rizhiyi"
        apiKey = "Yrwa49CSvgmhMxEkYiB7sJmUA8avdMTdhoG9KTDLsmTQJCWncXfxEGeHveG3GfED"
        auth = (user,apiKey)

        response = requests.get(url=uri, auth=auth, headers=headers, timeout=30, verify=False)
        if response.status_code != 200:
            apiLog.exception(errorMsg.get(response.status_code,response.text))
        return json.loads(response.text)
    except Exception as e:
        apiLog.exception(e)


def get_uuids():  #获取uuid和ip
    global uuid_ip 
    params = {"detail": "true"}  
    response = send_req(uri=url.format(uri='/default/workloadnetwork', params=json.dumps(params)))
    apiLog.info('uuids、ip获取成功')
    uuid_ip = { item['uuid']: item['network'][0]['ip'] for item in response }
    return [ item for item in uuid_ip.keys()]


def start_exec(uri,api_name): 
    try:
        with open('/opt/api/config.json','r+') as fp:
            conf = json.load(fp)
            if conf['lastdetecttimestamp'][api_name] is not None:
                params = {"uuids": uuids, "lastdetecttimestamp": conf['lastdetecttimestamp'][api_name]}
            else:
                params = {"uuids": uuids}

            response = send_req(uri.format(uri=uri, params=json.dumps(params)))
            if response is not None:
                apiLog.info("已获取接口数据")             
                response.sort(key=lambda x: x['lastdetecttimestamp'])
                conf['lastdetecttimestamp'][api_name] = response[-1]['lastdetecttimestamp'] 

                time_format = time.strftime('%Y%m%d', time.localtime())
                file_name = f"{api_name}_{time_format}.log"
                with open(os.path.join(log_path, file_name), 'a', buffering=-1) as f:
                    for item in response:
                        item['dstaddr'] = uuid_ip.get(item['uuid'],'') if item.get('uuid', None) is not None else ''
                        if 'srcaddr' not in item:
                            item['srcaddr'] =  uuid_ip.get(item['srcuuid'],'') if item.get('srcuuid', None) is not None else ''
                        f.write(str(item) + '\n')
                    apiLog.info("日志文件已保存在{}".format(os.path.join(log_path, file_name)))
            fp.seek(0)
            fp.truncate()
            json.dump(conf,fp)
            apiLog.info("已更新配置文件")

    except Exception as e:
        apiLog.exception(e)


if __name__ == '__main__':
    init()
    uuids = get_uuids()
    start_exec('/beaccessedrelation','accessRelationText')
    start_exec('/default/beblockedrelation','blockLogText')