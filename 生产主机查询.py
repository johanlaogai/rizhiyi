#!/usr/local/easyops/python/bin/python
# -- coding: utf-8 --
import json
import logging
import urllib
import hashlib
import hmac
import sys
import requests
import time

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

requests.packages.urllib3.disable_warnings()

# cmdb接口信息
# 用户：cmfopsapi
EASYOPS_OPEN_API_HOST = "cmdb.cmfchina.com"
ACCESS_KEY = "19a1e1f6a6035b26dd24c7a5"
SECRET_KEY = "52424167676f58544945754864564c59744f734b6a494d6d586b754974476e74"

# cmdb日志格式
FORMAT = '[%(asctime)s %(filename)s(line:%(lineno)d) %(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('log')
logger.setLevel(logging.INFO)


# cmdb接口鉴权
class Api:
    def __init__(self, ip=EASYOPS_OPEN_API_HOST, access_key=ACCESS_KEY, secret_key=SECRET_KEY):
        self.session = requests.session()
        self.ip = ip
        self.access_key = access_key
        self.secret_key = secret_key

    def easy_request(self, uri, ip=None, session=False, method='GET', params=None):
        if not params:
            params = dict()

        # 时间戳
        request_time = int(time.time())

        # headers处理
        headers = dict()
        headers['Host'] = 'openapi.easyops-only.com'
        headers['Content-Type'] = 'application/json'

        # 签名构建
        signature = Api.gen_signature(
            access_key=self.access_key,
            secret_key=self.secret_key,
            request_time=request_time,
            method=method,
            uri=uri,
            data=params,
            content_type=headers.get('Content-Type')
        )

        # 默认的三个参数
        keys = {
            "accesskey": self.access_key,
            "signature": signature,
            "expires": str(request_time)
        }

        # 拼接IP和URI
        if not ip:
            url = "http://%s%s" % (self.ip, uri)
        else:
            url = "http://%s%s" % (ip, uri)

        # 整理URL参数
        if method == 'GET' or method == 'DELETE':
            params.update(keys)
            url_params = urllib.urlencode(params)
        else:
            url_params = urllib.urlencode(keys)

        # 拼接URL和URL参数
        if '?' not in url:
            url = '%s?%s' % (url, url_params)
        else:
            url = '%s&%s' % (url, url_params)
        # print("request url: {}".format(url))

        # 是否会话访问
        if session:
            response = self.session.request(url=url, method=method, headers=headers, json=params)
        else:
            response = requests.request(url=url, method=method, headers=headers, json=params)
        # print(response.text)
        # 返回结果
        if response.status_code == 200:
            return json.loads(response.text)

        logger.error("http_request %s return %s" % (response.url, response.status_code))
        raise Exception("http_request %s return %s" % (response.url, response.status_code))

    @staticmethod
    def gen_signature(access_key, secret_key, request_time, method, uri, data=None, content_type='application/json'):
        if method == 'GET' or method == 'DELETE':
            url_params = ''.join(['%s%s' % (key, data[key]) for key in sorted(data.keys())])
        else:
            url_params = ''
        if method == 'POST' or method == 'PUT':
            m = hashlib.md5()
            m.update(json.dumps(data).encode('utf-8'))
            body_content = m.hexdigest()
        else:
            body_content = ''

        str_sign = '\n'.join([
            method,  # 指HTTP请求方法如, GET, POST, PUT, DELETE
            uri,  # 指所访问的资源路径如, /cmdb/object/list
            url_params,  # 指请求中的URL参数, 其构成规则如下: 1. 对参数key进行升序排序 2. 对于所有参数以key+value方式串联
            content_type,  # 请求Header中的Content-Type值
            body_content,  # 请求Header中的Content-MD5值, 等同于对body数据的md5sum
            str(request_time),  # 请求发生时的时间戳
            access_key  # 用户自己的AccessKey
        ])

        # 利用哈希算法，以一个密钥和一个消息为输入，生成一个消息摘要作为输出，即为使用秘钥和消息生成一个签名
        signature = hmac.new(secret_key, str_sign, hashlib.sha1).hexdigest()
        return signature


if __name__ == '__main__':
    page = 1
    while True:
        params = {
            "fields": {
                "ip": True,
                "hostname": True,
                "USER.nickname": True,
                "owner.nickname": True,
                "_deviceList_CLUSTER.name": True,
                "_deviceList_CLUSTER.appId.name": True,
                "_deviceList_CLUSTER.appId.businesses.name": True,
            },
            "query": {
                "_environment": {
                    "$eq": '生产'
                }
            },
            "page_size": 3000,
            "page": page
        }
        responses = Api().easy_request("/cmdb/object/{}/instance/_search".format('HOST'), method="POST", params=params)
        if not responses["data"]["list"]:
            break
        else:
            page += 1
        for info in responses["data"]["list"]:
            hostinfo = {
                'ip': info['ip'],
                'hostname': info['hostname'],  #主机名
                'app': [],   #应用
                'businesses': [],  #业务系统
                'dev': [],  #开发
                'own': [], #负责人
            }
            for cluster in info['_deviceList_CLUSTER']:
                for app in cluster['appId']:
                    hostinfo['app'].append(app['name'])
                    for busin in app['businesses']:
                        hostinfo['businesses'].append(busin['name'])
            for USER in info['USER']:
                hostinfo['dev'].append(USER['nickname'])
            for owner in info['owner']:
                hostinfo['own'].append(owner['nickname'])

            print(json.dumps(hostinfo))