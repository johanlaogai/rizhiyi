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

import json
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import configparser
import smtplib
import logging
import os
import base64

re_logger = logging.getLogger("django.request")
global reply_content
reply_content = ""
log_content = {
    logging.FATAL: re_logger.fatal,
    logging.ERROR: re_logger.error,
    logging.WARNING: re_logger.warning,
    logging.INFO: re_logger.info,
    logging.DEBUG: re_logger.debug
}
# 发送方式的类型，对应三个样例。
# 样例一：connect；样例二：common；样例三：starttls。
# 默认的是样例2，所以是common。如果跑不通，能跑通哪个样例，替换哪个样例对应的代号。
send_type = "common"

META = {
        "name": "email_V2",
        "version": 2,
        "alias": "邮件告警(V2)",
        "configs": [
            {
                "name": "subject",
                "alias": "标题",
                "placeholder": "支持模板语言",
                "presence": True,
                "value_type": "string",
                "default_value": "[告警邮件][{% if alert.is_alert_recovery %}告警恢复{% else %}{% if alert.strategy.trigger.level == \"low\" %}低{% elif alert.strategy.trigger.level == \"mid\" %}中{% elif alert.strategy.trigger.level == \"high\"%}高{% endif %}{% endif %}]{% autoescape off %}{{alert.name}}{% endautoescape %}",
                "style": {
                    "rows": 1,
                    "cols": 15
                }
            },
            {
                "name": "receiver",
                "alias": "接收者",
                "placeholder": "可以是个人邮箱，也可以是用户分组",
                "presence": True,
                "value_type": "string",
                "input_type": "email_account_group",
                "default_value": "",
                "style": {
                    "rows": 1,
                    "cols": 20
                }
            },
            {
                "name": "cc",
                "alias": "抄送",
                "placeholder": "可以是个人邮箱，也可以是用户分组",
                "presence": False,
                "value_type": "string",
                "input_type": "email_account_group",
                "default_value": "",
                "style": {
                    "rows": 1,
                    "cols": 20
                }
            },
            {
                "name": "bcc",
                "alias": "密送",
                "placeholder": "可以是个人邮箱，也可以是用户分组",
                "presence": False,
                "value_type": "string",
                "input_type": "email_account_group",
                "default_value": "",
                "style": {
                    "rows": 1,
                    "cols": 20
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
                    数据集：{{ alert.search.datasets }} </p>
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
                    告警级别：{% if alert.strategy.trigger.level == "low" %}低{% elif alert.strategy.trigger.level == "mid" %}中{%elif alert.strategy.trigger.level == "high"%}高{% endif %}</p>
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


# 发送GET请求，可以传入frontend的地址和接口，向Frontend发送请求
def http_get(url, params):
    re_logger.info("url is %s" % (url))
    re_logger.info("params is %s" % (params))

    url_params = urllib.parse.urlencode(params)
    re_logger.info("whole url is %s%s%s" % (url, '?', url_params))

    req = urllib.request.Request(url='%s%s%s' % (url, '?', url_params))
    res = urllib.request.urlopen(req)
    res = res.read()
    re_logger.info("response is %s" % (res))
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
    re_logger.info("content params is %s" % (params))
    template_str = params.get('configs')[4].get('value')
    conf_obj = {'alert': alert, 'web_conf': _web_conf_obj()}
    _content = _render(conf_obj, template_str)
    re_logger.info("isHandle is %s" % (isHandle))

    if not isHandle:
        _content = add_graph_to_text(params, _content)
    re_logger.info("content result is %s" % (_content))
    return _content


def connect_method(use_ssl, mail_host, smtp_port):
    if use_ssl == "yes":
        s = smtplib.SMTP_SSL()
    else:
        s = smtplib.SMTP()
    s.connect(mail_host, smtp_port)
    return s


# 样例2就是默认的发送方式
def common_method(use_ssl, mail_host, smtp_port):
    if use_ssl == "yes":
        s = smtplib.SMTP_SSL(mail_host, smtp_port)
    else:
        s = smtplib.SMTP(mail_host, smtp_port)
    return s


def starttls_method(use_ssl, mail_host, smtp_port):
    if use_ssl == "yes":
        s = smtplib.SMTP_SSL(mail_host, smtp_port)
    else:
        s = smtplib.SMTP(mail_host, smtp_port)
    s.starttls()
    return s


send_email_method = {"connect": connect_method, "common": common_method, "starttls": starttls_method}


# 预览插入趋势图
def add_graph_to_text(params, content):
    graph_path = ""
    if "timechart_trend_path" in params:
        graph_path = params.get('timechart_trend_path')
        re_logger.info("graph_path is %s" % (graph_path))

        fp = open(graph_path, 'rb')
        base64_data = base64.b64encode(fp.read())
        fp.close()
        imageHtml = "<img src=\"data:image/jpg;base64,%s\" style=\"width:700px\"/><br><br>" % (base64_data.decode())
        content = content.replace("<br><img src=\"cid:timechart_trend\"/><br><br>", imageHtml)
    else:
        # 如果没有图片，这里就去掉显示图片的地方，否则会有一个图裂，但是不知道需不需要保留这个图裂，以作提示
        content = content.replace("<br><img src=\"cid:timechart_trend\"/><br><br>", "")

    re_logger.info("content replace is %s" % (content))
    return content


def handle(params, alert):
    # print "###########################mail params: ",params
    # print "###########################mail alert: ", alert
    log_and_reply(logging.WARNING, ("###########################mail params: %s" % (params)))
    log_and_reply(logging.WARNING, ("###########################mail alert:  %s" % (alert)))


    # render subject
    subject_tmpl = params.get('configs')[0].get('value')
    subject_conf_obj = {'alert': alert}
    subject = _render(subject_conf_obj, subject_tmpl)

    re_logger.info("configs[1] is %s" % (params.get('configs')[1]))
    receivers = params.get('configs')[1].get('value').strip(',').split(',')
    re_logger.info("receivers are %s" % (receivers))

    re_logger.info("configs[2] is %s" % (params.get('configs')[2]))
    ccs = params.get('configs')[2].get('value', '').strip(',').split(',')
    re_logger.info("ccs are %s" % (ccs))

    re_logger.info("configs[3] is %s" % (params.get('configs')[3]))
    bccs = params.get('configs')[3].get('value', '').strip(',').split(',')
    re_logger.info("bccs are %s" % (bccs))

    web_conf = _web_conf_obj()
    url = web_conf['frontend']['frontend_url'].strip(',').split(',')[0]
    token = alert.get('_alert_domain_token')
    operator = alert.get('_alert_owner_name')
    re_logger.info("token is %s" % (token))
    re_logger.info("operator is %s" % (operator))
    re_logger.info("frontend url is %s" % (url))

    # Frontend只有通过某个用户分组id获取某个分组的用户，目前没有批量接口。
    account_emails_list = []
    for receiver in receivers:     # 循环获取
        re_logger.info("receiver is %s" % (receiver))
        if '@' in receiver:
            account_emails_list = account_emails_list + [receiver]
            re_logger.info("account_emails_list is %s" % (account_emails_list))
        else:
            get_account_params = {'act': 'get_account_by_user_group_id', 'operator': operator, 'token': token, 'user_group_id': receiver}
            response = json.loads(http_get(url, get_account_params))
            re_logger.info("response is %s" % (response))
            if "accounts" in response:
                accounts = response['accounts']
                re_logger.info("accounts is %s" % (accounts))
                # 判断email有无
                for account in accounts:
                    if "email" in account:
                        account_emails_list = account_emails_list + [account.get('email')]
                re_logger.info("account_emails_list is %s" % (account_emails_list))
            else:
                log_and_reply(logging.WARNING, ("no user group for %s" % (receiver)))

    account_ccs_list = []
    for cc in ccs:     # 循环获取
        re_logger.info("cc is %s" % (cc))
        if '@' in cc:
            account_ccs_list = account_ccs_list + [cc]
            re_logger.info("account_ccs_list is %s" % (account_ccs_list))

    account_bccs_list = []
    for bcc in bccs:     # 循环获取
        re_logger.info("bcc is %s" % (bcc))
        if '@' in bcc:
            account_bccs_list = account_bccs_list + [bcc]
            re_logger.info("account_bccs_list is %s" % (account_bccs_list))

    # 虽然注册用户时，邮箱不能重复，但是这里还是去重一下
    account_emails = list(set(account_emails_list))
    account_ccs = list(set(account_ccs_list))
    account_bccs = list(set(account_bccs_list))
    # 转化字符串
    receiver_str = ','.join(account_emails)
    re_logger.info("receiver_str is %s" % (receiver_str))

    cc_str = ','.join(account_ccs)
    re_logger.info("cc_str is %s" % (cc_str))

    bcc_str = ','.join(account_bccs)
    re_logger.info("bcc_str is %s" % (bcc_str))

    # 获取趋势图路径
    graph_path = ""
    # 扩展搜索不是timechart的也不发送附件图片
    if ("result" in alert) and ("is_extend_query_timechart" in alert.get("result")):
        is_extend_query_timechart = alert.get("result").get("is_extend_query_timechart")
        if ("timechart_trend_path" in params) and is_extend_query_timechart:
            graph_path = params.get('timechart_trend_path')

    re_logger.info("graph_path is %s" % (graph_path))

    _content = content(params, alert, True)
    subject = subject + "#token#" + token
    send_mail(subject, receiver_str, cc_str, bcc_str, _content, graph_path)


def send_mail(subject, receiver, cc, bcc, content, graph_path):
    subject_arr = subject.split("#token#")
    subject = subject_arr[0]
    token = ""
    try:
        token = subject_arr[1]
        cf = configparser.RawConfigParser(strict=False)
        real_path = os.getcwd() + '/config'
        cf.read(real_path + "/yottaweb.ini")
        use_ssl_ini = cf.get('email', 'use_ssl')
        need_login_ini = cf.get('email', 'need_login')
        send_address_ini = cf.get('email', 'send')
        smtp_pwd_ini = cf.get('email', 'passwd')
        smtp_port_ini = cf.get('email', 'smtp_port')
        email_user_ini = cf.get('email', 'user')
        smtp_server_ini = cf.get('email', 'smtp_server')
        use_ssl = ''
        need_login = ''
        send_address = ''
        smtp_pwd = ''
        smtp_port = ''
        email_user = ''
        smtp_server = ''

        all_ori_conf = MyUtils().get_key_config(token, 'all').get("data")

        if all_ori_conf:
            use_ssl = all_ori_conf.get('email_email_use_ssl')
            need_login = all_ori_conf.get('email_email_need_login')
            send_address = str(all_ori_conf.get('email_send'))
            smtp_pwd = all_ori_conf.get('email_passwd')
            smtp_port = str(all_ori_conf.get('email_smtp_port'))
            email_user = str(all_ori_conf.get('email_user')) if all_ori_conf.get('email_user') else all_ori_conf.get('email_user')
            smtp_server = str(all_ori_conf.get('email_smtp_server'))
            if not (send_address and smtp_pwd and smtp_port and smtp_server and email_user):
                use_ssl = use_ssl_ini
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
        use_ssl = 'no'
        need_login = 'yes'
        send_address = 'notice@yottabyte.cn'
        smtp_pwd = ''
        smtp_port = ''
        smtp_server = ''
    re_logger.info("alert_send_mail_conf: %s" % (send_address))
    sub = subject
    content = content
    main_msg = MIMEMultipart()

    mail_to_list = receiver.split(',')
    email_list = mail_to_list.copy()

    if cc:
        cc_to_list = cc.split(',')
        main_msg['Cc'] = ";".join(cc_to_list)
        email_list += cc_to_list

    if bcc:
        bcc_to_list = bcc.split(',')
        main_msg['Bcc'] = ";".join(bcc_to_list)
        email_list += bcc_to_list

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
        smtp = send_email_method.get(send_type)(use_ssl, mail_host, smtp_port)
        if need_login == "yes":
            smtp.login(mail_user, mail_pass)

        # re_logger.error(main_msg.as_string())
        smtp.sendmail(me, email_list, main_msg.as_string())
        smtp.close()
        log_and_reply(logging.INFO, ("Send email[ %s ] of report successful!" % (sub)))
        return True
    except Exception as e:
        log_and_reply(logging.ERROR, ("Send mail [ %s ] Error: %s" % (sub, str(e))))
        return False


# 既在日志中打印，又在执行结果中显示
def log_and_reply(log_level, comment):
    global reply_content
    log_content.get(log_level)(comment)
    reply_content = '%s%s%s' % (reply_content, "\n", comment)


# 获取执行结果的接口
def execute_reply(params, alert):
    re_logger.info("reply_content start")
    handle(params, alert)
    re_logger.info("reply_content: %s" % (reply_content))
    return reply_content
