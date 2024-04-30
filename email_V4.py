# -*- coding: utf-8 -*-
# wu.ranbo@yottabyte.cn
# 2016-05-19
# Copyright 2016 Yottabyte
# filename: yottaweb/apps/alert/plugins/alert_email.py
# file description: 邮件告警插件，默认插件，目前是支持用户分组及附件趋势图
__author__ = 'wu.ranbo'

from django.template import Context, Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from yottaweb.apps.utils.resources import MyUtils
import hashlib
import json
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import configparser
import smtplib
import logging
import os
import base64
from logging import handlers
import requests
import pymysql

global reply_content
reply_content = ""

# 发送方式的类型，对应三个样例。
# 样例一：connect；样例二：common；
send_type = "common"

# yottaweb_ip = "193.16.157.12"
# yottaweb_username = "chenfei"
# yottaweb_passwd = "Chenfei537527@"
yottaweb_ip = "192.168.40.104"
yottaweb_username = "admin"
yottaweb_passwd = "admin@rizhiyi.com"


META = {
        "name": "email_V4",
        "version": 8,
        "alias": "邮件告警_根据DTA选择接收人(V4)",
        "configs": [
            {
                "name": "subject",
                "alias": "标题",
                "placeholder": "支持模板语言",
                "presence": True,
                "value_type": "string",
                "default_value": "[告警邮件][{% if alert.is_alert_recovery %}告警恢复{% else %}{% if alert.strategy.trigger.level == \"info\" %}低级{% elif alert.strategy.trigger.level == \"low\" %}一般{% elif alert.strategy.trigger.level == \"mid\" %}中级{% elif alert.strategy.trigger.level == \"high\"%}重要{% elif alert.strategy.trigger.level == \"critical\"%}严重{% endif %}{% endif %}]{% autoescape off %}{{alert.name}}{% endautoescape %}",
                "style": {
                    "rows": 1,
                    "cols": 15
                }
            },
            {
                "name": "content_tmpl",
                "alias": "内容模板",
                "placeholder": "",
                "presence": True,
                "value_type": "template",
                "default_value": """
<table border="0" cellspacing="0" cellpadding="0" style="font-family:"微软雅黑",Helvetica,Arial,sans-serif;font-size:14px "
  width="100%">
  <tbody>
    <tr>
      <td style="">
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
          <tbody>
            <tr style="background-color: #2F323E;">
              <td>
                <p style="text-align:left;color: #FFFFFF; margin: 0 0 0 20px;font-size:18px;line-height: 48px;font-family:"微软雅黑",Helvetica,Arial,sans-serif;">日志易</p>
              </td>
            </tr>
          </tbody>
        </table>
      </td>
    </tr>
    <tr align="center">
      <td style="padding: 0 20px;">
        <p style="text-align:center;color:#2F323E;margin:24px 0;font-size:22px;font-family:"微软雅黑",Helvetica,Arial,sans-serif;">
        {% if alert.is_alert_recovery %} 告警{{ alert.name }}恢复 {% else %} 告警详情 {% endif %}</p>
      </td>
    </tr>
    {% if not alert.is_alert_recovery %}
      <tr>
        <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
          <table width="100%" border="0" cellpadding="5" cellspacing="0">
            <tbody>
              <tr>
                <td>
                  <p style="margin:0;font-size:14px;line-height:24px;color: #2F323E; font: bold 14px/20px Arial, sans-serif;margin-bottom: 10px">
                    <br>基本配置：<br></p>
                  <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px;">
                    告警产生时间：{{ alert.send_time|date:"Y年n月d日 H:i:s" }}  <a href={{web_conf.custom.web_address}}/search/?datasets={{ alert.search.datasets|urlencode }}&time_range={{alert.strategy.trigger.start_time|date:"Uu"|slice:":-3"}},{{alert.strategy.trigger.end_time|date:"Uu"|slice:":-3"}}&filters={{ alert.search.filter|urlencode}}&query={{alert.search.query|urlencode}}&title={{alert.name|urlencode}}&_t={{alert.send_time|date:"Uu"|slice:":-3"}}&page=1&size=20&order=desc&index=new&searchMode=index>查看详情</a></p>
                  <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px;">
                    数据集：{{ alert.search.dataset_query }} </p>
                  <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px;">
                    查询语句：{{ alert.search.query }} </p>
                </td>
              </tr>
            </tbody>
          </table>
        </td>
      </tr>
      <tr>
        <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
          <table width="100%" border="0" cellpadding="5" cellspacing="0">
            <tbody>
              <tr>
                <td>
                  <p style="margin:0;font-size:14px;line-height:24px;color: #2F323E; font: bold 14px/20px Arial, sans-serif;margin-bottom: 10px">
                    <br>告警结果：<br></p>
                  <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px;">
                    告警级别：{% if alert.strategy.trigger.level == "info" %}低级{%elif alert.strategy.trigger.level == "low"%}一般{% elif alert.strategy.trigger.level == "mid" %}中级{%elif alert.strategy.trigger.level == "high"%}重要{%elif alert.strategy.trigger.level == "critical"%}严重{% endif %}</p>
                  <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px;">
                    触发条件：{{ alert.strategy.trigger.compare_desc_text }}</p>
                  <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px">
                    触发事件总数：{{ alert.result.total }}</p>
                  <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px">
                    最近事件：</p>
                </td>
              </tr>
            </tbody>
          </table>
        </td>
      </tr>
      {% if alert.strategy.name == "count" and alert.result.hits %}
        <tr>
          <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
            <table width="100%" style="border: 1px solid #D7D7D7" cellpadding="10" cellspacing="0">
              <tbody>
                <tr>
                  <td style="width: 80px;border-right: 1px solid #D7D7D7; background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">序列
                    </p>
                  </td>
                  <td style="border-right: 1px solid #D7D7D7; background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">事件
                    </p>
                  </td>
                </tr>
                {% for item in alert.result.hits %}
                {% if not forloop.counter|divisibleby:"2" %}
                <tr>
                {% else %}
                <tr style="background-color:#F4F4F4;">
                {% endif %}
                  <td style="width: 80px;border-right: 1px solid #D7D7D7">
                    <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{forloop.counter}}
                    </p>
                  </td>
                  <td style="border-right: 1px solid #D7D7D7">
                    <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{item.raw_message}}</p>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </td>
        </tr>
      {% elif alert.strategy.name == "field_stat"%}
        <tr>
        {% if alert.strategy.trigger.method == "cardinality" %}
          <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
            <table width="100%" style="border: 1px solid #D7D7D7" cellpadding="10" cellspacing="0">
              <tbody>
                <tr>
                  <td style="width: 200px;border-right: 1px solid #D7D7D7; background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">键值
                    </p>
                  </td>
                  <td style="width: 100px;border-right: 1px solid #D7D7D7; background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">次数
                    </p>
                  </td>
                </tr>
                {% for item in alert.result.terms %}
                {% if not forloop.counter|divisibleby:"2" %}
                <tr>
                {% else %}
                <tr style="background-color:#F4F4F4;">
                {% endif %}
                  <td style="width: 200px;border-right: 1px solid #D7D7D7">
                    <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{item.key|ljust:"40"}}
                    </p>
                  </td>
                  <td style="width: 100px;border-right: 1px solid #D7D7D7">
                    <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{item.doc_count|ljust:"40"}}</p>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </td>
          {% else %}
            <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
              <p style="margin:0;font-size:12px;line-height:24px;color: #2F323E; font: normal Arial, sans-serif;margin-bottom: 8px;">
                {{ alert.strategy.trigger.field }}的值为{{ alert.result.value }}<br>
              </p>
            </td>
          {% endif %}
        </tr>
      {% elif alert.strategy.name == "spl_query" %}
        {% if alert.result.columns %}
        <tr>
          <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
            <table width="100%" style="border: 1px solid #D7D7D7" cellpadding="10" cellspacing="0">
              <tbody>
                <tr>
                {% for k in alert.result.columns %}
                  <td style="border-right: 1px solid #D7D7D7; background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">{{ k.name }}
                    </p>
                  </td>
                {% endfor %}
                </tr>
                {% for result_row in alert.result.hits %}
                {% if not forloop.counter|divisibleby:"2" %}
                <tr>
                {% else %}
                <tr style="background-color:#F4F4F4;">
                {% endif %}
                  {% for k in alert.result.columns %}
                      {% for rk, rv in result_row.items %}
                        {% if rk == k.name %}
                        <td style="border-right: 1px solid #D7D7D7">
                          <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{rv}}
                          </p>
                        </td>
                        {% endif %}
                      {% endfor %}
                  {% endfor %}
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </td>
        </tr>
        {% endif %}
      {% endif %}
    {% endif %}
    {% if alert.result.extend_total > 0 or alert.result.extend_result_total_hits > 0 or alert.result.extend_result_sheets_total %}
      {% if alert.result.is_extend_query_timechart and alert.graph_enabled %}
      <tr>
        <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
          <img src="cid:timechart_trend"/><br>
        </td>
      </tr>
      {% endif %}
    {% endif %}
    {% if alert.result.extend_total > 0 or alert.result.extend_result_total_hits > 0 or alert.result.extend_result_sheets_total %}
      <tr>
        <td style="font-family:Helvetica,Arial,sans-serif;font-size:14px;padding: 0 20px;">
          {% if alert.result.extend_hits %}
            {% if "raw_message" in alert.result.extend_hits.0.keys %}
            <table width="100%" style="border: 1px solid #D7D7D7;margin-top: 8px;" cellpadding="10" cellspacing="0">
              <tbody>
                <tr>
                  <td style="width: 80px;border-right: 1px solid #D7D7D7; background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">序号
                    </p>
                  </td>
                  <td style="background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">事件
                    </p>
                  </td>
                </tr>
                {% for ext in alert.result.extend_hits %}
                  {% if not forloop.counter|divisibleby:"2" %}
                  <tr>
                  {% else %}
                  <tr style="background-color:#F4F4F4;">
                  {% endif %}
                  <td style="width: 80px;border-right: 1px solid #D7D7D7">
                    <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{forloop.counter}}
                    </p>
                  </td>
                  <td style="">
                    <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{ext.raw_message}}</p>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% elif "_count" in alert.result.extend_hits.0.keys %}
            <table width="100%" style="border: 1px solid #D7D7D7;margin-top: 8px;" cellpadding="10" cellspacing="0">
              <tbody>
                <tr>
                  <td style="background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">事件
                    </p>
                  </td>
                </tr>
                {% for ext in alert.result.extend_hits %}
                  {% for sis in ext.source %}
                    {% if not forloop.counter|divisibleby:"2" %}
                      <tr>
                    {% else %}
                      <tr style="background-color:#F4F4F4;">
                    {% endif %}
                      <td style="">
                        <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{sis.raw_message}}</p>
                      </td>
                      </tr>
                  {% endfor %}
                  <tr><td>---------------------</td></tr>
                {% endfor %}
              </tbody>
            </table>
            {% else %}
            <table width="100%" style="border: 1px solid #D7D7D7;margin-top: 8px;" cellpadding="10" cellspacing="0">
              <tbody>
                <tr>
                {% for ks in alert.result.extend_hits.0.keys %}
                  <td style="width: 80px;border-right: 1px solid #D7D7D7; background-color:#EFF3F6;">
                    <p style="margin:0;font-size:12px;color: #2F323E; font-weight: bold; font-family:Arial, sans-serif;">{{ks}}
                    </p>
                  </td>
                {% endfor %}
                {% for ext in alert.result.extend_hits %}
                  {% if not forloop.counter|divisibleby:"2" %}
                    <tr>
                  {% else %}
                    <tr style="background-color:#F4F4F4;">
                  {% endif %}
                  {% for the_key in ext.keys %}
                    {% for key, value in ext.items %}
                      {% if key == the_key %}
                        <td style="width: 80px; border-right: 1px solid #D7D7D7;">
                          <p style="margin:0;font-size:12px;color: #2F323E; font: normal Arial, sans-serif;">{{value}}</p>
                        </td>
                      {% endif %}
                    {% endfor %}
                  {% endfor %}
                  </tr>
                {% endfor %}
              </tbody>
            </table>
            {% endif %}
          {% endif %}
        </td>
      </tr>
    {% endif %}
  </tbody>
</table>
<br>
                """,
                "style": {
                    "rows": 30,
                    "cols": 60
                }
            }
            ]
        }


class mysql(object):
    """
    数据库连接
    """

    def __init__(self, server_ip, dbuser, dbpasswd, database="rizhiyi_system"):
        self.server_ip = server_ip
        self.dbuser = dbuser
        self.dbpasswd = dbpasswd
        self.database = database
        self.cur = self.getConnect()

    def getConnect(self):
        self.con = pymysql.connect(host=self.server_ip, port=3306, user=self.dbuser, password=self.dbpasswd,
                                   database=self.database, autocommit=True, charset='utf8')
        cursor = self.con.cursor()
        if not cursor:
            logger.error("连接数据库失败")
        else:
            return cursor

    def select(self, sql):
        self.cur.execute(sql)
        result = self.cur.fetchall()
        return result

    def close(self):
        if self.con:
            self.con.close()


# db = mysql(server_ip="193.16.157.11", dbuser="root", dbpasswd="rizhiyi&2014")
db = mysql(server_ip="192.168.40.104", dbuser="root", dbpasswd="rizhiyi&2014")


# 发送GET请求，可以传入frontend的地址和接口，向Frontend发送请求
def http_get(url, params):
    logger.info("url is %s" % (url))
    logger.info("params is %s" % (params))

    url_params = urllib.parse.urlencode(params)
    logger.info("whole url is %s%s%s" % (url, '?', url_params))

    req = urllib.request.Request(url='%s%s%s' % (url, '?', url_params))
    res = urllib.request.urlopen(req)
    res = res.read()
    logger.info("response is %s" % (res))
    return res


def _web_conf_obj():
    confobj = {}
    try:
        cf = configparser.RawConfigParser(strict=False)
        real_path = os.getcwd() + '/config'
        cf.read(real_path + "/yottaweb.ini")
        for section in cf.sections():
            confobj[section] = {}
            for k, v in cf.items(section):
                confobj[section][k] = v
    except Exception:
        log_and_reply(logging.ERROR, ("_yottaweb_conf_obj get failed!"))
    return confobj


def _render(conf_obj, tmpl_str):
    t = Template(tmpl_str)
    c = Context(conf_obj)
    _content = t.render(c)
    return _content


def content(params, alert, isHandle=False):
    # logger.debug("content params is %s" % (params))
    conf_obj = {'alert': alert}
    str_temp = params.get('configs')[1].get('value')
    _content = _render(conf_obj, str_temp)
    logger.debug("isHandle is %s" % (isHandle))

    if not isHandle:
        _content = add_graph_to_text(params, _content)
    # logger.info("content result is %s" % (_content))
    return _content


def connect_method(use_protocol, mail_host, smtp_port):
    if use_protocol == "ssl":
        s = smtplib.SMTP_SSL()
    else:
        s = smtplib.SMTP()
    s.connect(mail_host, smtp_port)
    return s


# 样例2就是默认的发送方式
def common_method(use_protocol, mail_host, smtp_port):
    if use_protocol == "ssl":
        s = smtplib.SMTP_SSL(mail_host, smtp_port)
    elif use_protocol == 'tls':
        s = smtplib.SMTP(mail_host, smtp_port)
        s.starttls()
    else:
        s = smtplib.SMTP(mail_host, smtp_port)
    return s


send_email_method = {"connect": connect_method, "common": common_method}


# 预览插入趋势图
def add_graph_to_text(params, content):
    graph_path = ""
    if "timechart_trend_path" in params:
        graph_path = params.get('timechart_trend_path')
        logger.info("graph_path is %s" % (graph_path))

        fp = open(graph_path, 'rb')
        base64_data = base64.b64encode(fp.read())
        fp.close()
        imageHtml = "<img src=\"data:image/jpg;base64,%s\" style=\"width:700px\"/><br><br>" % (base64_data.decode())
        content = content.replace("<br><img src=\"cid:timechart_trend\"/><br><br>", imageHtml)
    else:
        # 如果没有图片，这里就去掉显示图片的地方，否则会有一个图裂，但是不知道需不需要保留这个图裂，以作提示
        content = content.replace("<br><img src=\"cid:timechart_trend\"/><br><br>", "")

    # logger.info("content replace is %s" % (content))
    return content


def getUserEmail(receivers):
    tmpReceivers = []
    for i in receivers.split(","):
        tmpReceivers.append("full_name=\"" + i + "\"")
    sql = '''select email from Account where {}'''.format(" OR ".join(tmpReceivers))
    result = db.select(sql)

    logger.debug("receivers:{}, result:{}".format(receivers, result))
    account_emails_list = []
    for data in iter(result):
        account_emails_list.append(data[0])

    # 虽然注册用户时，邮箱不能重复，但是这里还是去重一下
    account_emails = list(set(account_emails_list))
    # 转化字符串
    receiver_str = ','.join(account_emails)
    logger.info("receiver_str is %s" % (receiver_str))
    return receiver_str


def getReceivers():
    """
    通过接口的方式获取字典表中的短信接收用户信息
    """
    # url = "http://{}:8090/api/v2/dictionaries/62/".format(yottaweb_ip)
    url = "http://{}:8090/api/v2/dictionaries/31/".format(yottaweb_ip)

    querystring = {"type": "content", "page": "0", "size": "1000"}

    response = requests.request("GET", url, params=querystring, auth=(yottaweb_username, yottaweb_passwd), timeout=60)
    assert response.status_code == 200
    dictionary = response.json()["object"]["content"]
    del dictionary[0]

    reciverInfos = []
    for i in dictionary:
        reciverInfo = {}
        tmpI = i.replace("\"", "").split(",")

        reciverInfo["dta"] = tmpI[2]
        reciverInfo["appname"] = tmpI[1]
        reciverInfo["users"] = ",".join(tmpI[3:])
        reciverInfos.append(reciverInfo)
    return reciverInfos


def getEmailConfig():
    url = "http://{}:8090/api/v3/systemconfigs/".format(yottaweb_ip)

    md5 = hashlib.md5()
    md5.update(yottaweb_passwd.encode('utf-8'))
    password = md5.hexdigest()
    basic = base64.b64encode(b"%s:%s" % (yottaweb_username.encode(), password.encode()))
    basic = basic.decode('utf-8')

    headers = {
        'X-Encrypt-Method': 'MD5',
        'Content-Type': 'application/json',
        'Authorization': 'Basic %s' % basic
    }
    try:
        response = requests.request("GET", url, headers=headers).json()
        result = {}

        if response['result']:
            data = response.get('objects', [])
            configs = {}
            for item in data:
                key = item.get('key')
                value = item.get('value')
                configs[key] = value
            result['data'] = configs
            result['result'] = True
            logger.info("result:{}".format(json.dumps(result, ensure_ascii=False)))
        else:
            result['result'] = False
            result['data'] = {}
            result['error_info'] = response
            logger.warning("result:{}".format(json.dumps(result, ensure_ascii=False)))
        return result
    except Exception as e:
        logger.exception(str(e))
        return None


def handle(params, alert):
    subject_tmpl = params.get('configs')[0].get('value')
    subject_conf_obj = {'alert': alert}
    subject = _render(subject_conf_obj, subject_tmpl)
    token = alert.get('_alert_domain_token')

    # 获取趋势图路径
    graph_path = ""
    # 扩展搜索不是timechart的也不发送附件图片
    if ("result" in alert) and ("is_extend_query_timechart" in alert.get("result")):
        is_extend_query_timechart = alert.get("result").get("is_extend_query_timechart")
        if ("timechart_trend_path" in params) and is_extend_query_timechart:
            graph_path = params.get('timechart_trend_path')

    logger.debug("graph_path is %s" % (graph_path))

    subject = subject + "#token#" + token
    contents = content(params, alert)

    try:
        tmpData = {}
        for i in alert["result"]["hits"]:
            if tmpData.get(i["appname"]):
                tmpData[i["appname"]].append(i)
            else:
                tmpData[i["appname"]] = []
                tmpData[i["appname"]].append(i)

        tmpDtaData = {}
        for key, value in tmpData.items():
            tmpDtaData[key] = []
            dta = {}
            for i in value:
                if dta.get(i["dta"]):
                    dta[i["dta"]].append(i)
                else:
                    dta[i["dta"]] = []
                    dta[i["dta"]].append(i)
            tmpDtaData[key].append(dta)

        logger.info("待发送数据:{}".format(json.dumps(tmpDtaData, ensure_ascii=False)))

        revivers = getReceivers()
        logger.error("revivers:{}".format(json.dumps(revivers, ensure_ascii=False)))

        all_ori_conf = getEmailConfig().get("data")
        logger.info("all_ori_conf: %s， token: %s" % (all_ori_conf, token))

        sendSuccCounter = 0
        sendErrCounter = 0
        for key, value in tmpDtaData.items():
            for i in value:
                for k, v in i.items():
                    for j in revivers:
                        if j["appname"] == key and j["dta"] == k:
                            receiver_str = getUserEmail(j["users"])
                            rspData = {
                                "alertName": alert['name'],
                                "sendUsers": j["users"],
                                "alertLevel": "",
                                "sendType": "邮件告警",
                                "sendMsg": "由于推送内容为HTML模板渲染，不便于查看，因而不展示内容",
                                "sendRsp": {"Detail": {"TxnStat": ""}, "FaultString": ""}
                            }
                            if alert['strategy']['trigger'].get("level"):
                                rspData["alertLevel"] = alert['strategy']['trigger'].get("level")
                            alert["result"]["hits"] = v
                            contents = content(params, alert)
                            # logger.info("subject:{}, receiver_str:{}, contents:{}, graph_path:{}".format(subject, receiver_str, contents, graph_path))
                            FaultCode, FaultString = send_mail(subject, receiver_str, contents, all_ori_conf, graph_path)
                            if FaultCode == "SUCCESS":
                                sendSuccCounter += 1
                            else:
                                sendErrCounter += 1
                            rspData["sendRsp"]["Detail"]["TxnStat"] = FaultCode
                            rspData["sendRsp"]["FaultString"] = FaultString
                            logger.debug(json.dumps(rspData, ensure_ascii=False))
        log_and_reply(logging.INFO, "发送成功:{}条, 发送失败:{}条".format(sendSuccCounter, sendErrCounter))
    except Exception as e:
        logger.exception(e)
    finally:
        db.close()


def send_mail(subject, receiver, content, all_ori_conf, graph_path):
    subject_arr = subject.split("#token#")
    subject = subject_arr[0]
    token = ""
    try:
        token = subject_arr[1]
        cf = configparser.RawConfigParser(strict=False)
        real_path = os.getcwd() + '/config'
        cf.read(real_path + "/yottaweb.ini")
        use_protocol_ini = cf.get('email', 'use_protocol')
        need_login_ini = cf.get('email', 'need_login')
        send_address_ini = cf.get('email', 'send')
        smtp_pwd_ini = cf.get('email', 'passwd')
        smtp_port_ini = cf.get('email', 'smtp_port')
        email_user_ini = cf.get('email', 'user')
        smtp_server_ini = cf.get('email', 'smtp_server')
        use_protocol = ''
        need_login = ''
        send_address = ''
        smtp_pwd = ''
        smtp_port = ''
        email_user = ''
        smtp_server = ''

        if all_ori_conf:
            use_protocol = all_ori_conf.get('email_email_use_protocol')
            need_login = "yes" if all_ori_conf.get('email_email_need_login') == "true" else all_ori_conf.get('email_email_need_login')
            send_address = str(all_ori_conf.get('email_send'))
            smtp_pwd = all_ori_conf.get('email_passwd')
            smtp_port = str(all_ori_conf.get('email_smtp_port'))
            email_user = str(all_ori_conf.get('email_user')) if all_ori_conf.get('email_user') else all_ori_conf.get('email_user')
            smtp_server = str(all_ori_conf.get('email_smtp_server'))
            if not (send_address and smtp_pwd and smtp_port and smtp_server and email_user):
                use_protocol = use_protocol_ini
                need_login = need_login_ini
                send_address = send_address_ini
                smtp_pwd = smtp_pwd_ini
                smtp_port = smtp_port_ini
                email_user = email_user_ini
                smtp_server = smtp_server_ini
            if email_user == 'sender' or not email_user:
                email_user = send_address
    except Exception as e:
        log_and_reply(logging.ERROR, ("alert_plugins_config get failed!"))
        use_protocol = 'plain'
        need_login = 'yes'
        send_address = 'notice@yottabyte.cn'
        smtp_pwd = ''
        smtp_port = ''
        smtp_server = ''
    logger.info("alert_send_mail_conf: %s" % (send_address))
    sub = subject
    content = content
    main_msg = MIMEMultipart()

    mail_to_list = receiver.split(',')
    email_list = mail_to_list.copy()

    mail_host = smtp_server
    mail_address = send_address
    mail_pass = smtp_pwd
    mail_user = email_user
    #
    # to_list:发给谁
    # sub:主题
    # content:内容
    # send_mail("sub","content")

    me = mail_address
    msg = MIMEText(content, _subtype='html', _charset='gb18030')  # 创建一个实例，这里设置为html格式邮件
    main_msg.attach(msg)
    main_msg['Subject'] = sub
    main_msg['From'] = me
    main_msg['To'] = ";".join(mail_to_list)

    contype = 'application/octet-stream'
    maintype, subtype = contype.split('/', 1)

    # 如果趋势图路径是空，则跳过，不附带图片
    if graph_path != "":
        target_file = graph_path
        data = open(target_file, 'rb')
        file_msg = MIMEBase(maintype, subtype)
        file_msg.set_payload(data.read())
        data.close()
        encoders.encode_base64(file_msg)
        # 设置附件头
        basename = os.path.basename(target_file)
        file_msg.add_header('Content-Disposition', 'attachment', filename=basename)
        main_msg.attach(file_msg)

        # 正文也增加图片，但是一个流只能增加一种，所以不能与附件合并
        fp = open(target_file, 'rb')
        image_msg = MIMEImage(fp.read(), subtype)
        fp.close()
        image_msg.add_header('Content-ID', '<timechart_trend>')
        main_msg.attach(image_msg)

    try:
        # log_and_reply(logging.INFO, ("mail_user: %s, mail_pass: %s" % (mail_user, mail_pass)))
        # logger.info("use_protocol: %s, mail_user: %s, mail_pass: %s, need_login: %s, email_list: %s, me: %s" % (use_protocol, mail_user, mail_pass, need_login, email_list, me))
        smtp = send_email_method.get(send_type)(use_protocol, mail_host, smtp_port)
        # logger.warning("smtp:{}".format(smtp))
        if need_login == "yes":
            smtp.login(mail_user, mail_pass)

        # logger.error("登录成功")
        smtp.sendmail(me, email_list, main_msg.as_string())
        smtp.close()
        logger.info("Send email[ %s ] of report successful!" % (sub))
        return "SUCCESS", "发送成功"
    except Exception as e:
        # log_and_reply(logging.ERROR, ("Send mail [ %s ] Error: %s" % (sub, str(e))))
        logger.exception("Send mail [ %s ] Error: %s" % (sub, str(e)))
        return "FAIL", str(e)


def log_and_reply(log_level, comment):
    """
    既在日志中打印，又在执行结果中显示
    Args:
        log_level: 日志级别
        comment: 日志内容

    Returns:

    """
    global reply_content
    log_content = {
        logging.FATAL: logger.fatal,
        logging.ERROR: logger.error,
        logging.WARNING: logger.warning,
        logging.INFO: logger.info,
        logging.DEBUG: logger.debug
    }
    log_content.get(log_level)(comment)
    reply_content = '%s%s%s' % (reply_content, "\n", comment)


def execute_reply(params, alert):
    """
    获取执行结果的接口
    Args:
        params:
        alert:

    Returns:

    """
    logger.info("reply_content start")
    handle(params, alert)
    logger.info("reply_content: %s" % reply_content)
    return reply_content


def set_logger(reset_logger):
    """
    配置日志
    Args:
        reset_logger:

    Returns:

    """
    global logger
    logger = reset_logger
