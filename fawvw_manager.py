# coding: utf-8
# @Time: 2023/8/15 10:57 AM 
# @Author: chen_zhangpeng 
# @File: fawvw_manager.py
# -*- coding: utf-8 -*-

import logging
import datetime
import json
import requests
import traceback
from common.plugin_util import convert_config

re_logger = logging.getLogger(__name__)

META = {
    "name": "fawvw_manager",
    "version": 1,
    "alias": "企业微信告警",
    "configs": [],
    "param_configs": [
        {
            "name": "webhook_url",
            "alias": "webhook地址",
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 15
            }
        }
    ]
}


def content(alert):
    """
    生成告警内容
    :param alert:
    :return:
    """
    try:
        module = alert.get("Module", "")
        alert_type = alert.get("Type", "")
        ip = alert.get("Ip", "")
        alarm_time = alert.get("Time", "")
        if alarm_time == "":
            alarm_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            alarm_dt = datetime.datetime.strptime(alarm_time[:19], "%Y-%m-%dT%H:%M:%S")
            alarm_time = alarm_dt.strftime("%Y-%m-%d %H:%M:%S")
        detail = alert.get("Detail", "")
        recovery = alert.get("Recover", "")
        if recovery or recovery == "True":
            recovery = "【招商基金-日志平台】<font color=\"info\">manager告警已恢复</font> \n".format(alert_type)
        else:
            recovery = "【招商基金-日志平台】<font color=\"warning\">manager触发告警</font> \n".format(alert_type)
        if module != "" and ip != "":
            _content = """%s
            > 告警类型: %s
            > 告警模块: %s
            > 告警IP: %s
            > 告警时间: %s
            > 告警详情: %s""" % (recovery, alert_type, module, ip, alarm_time, detail)
        elif ip != "":
            _content = """%s
            > 告警类型: %s
            > 告警IP: %s
            > 告警时间: %s
            > 告警详情: %s""" % (recovery, alert_type, ip, alarm_time, detail)
        else:
            _content = """%s
            > 告警类型: %s
            > 告警时间: %s
            > 告警详情: %s""" % (recovery, alert_type, alarm_time, detail)
        return _content
    except Exception as e:
        re_logger.exception("Fail to generate content :%s" % str(e))
        return None


def check_config_item(configs, name):
    """
    检查配置项是否配置
    :param configs:
    :param name:
    :return:
    """
    value = configs.get(name)
    if value is None:
        re_logger.error("{} not config, skip".format(name))
        raise
    return value


def send_alert(webhook_url, alert_content):
    """
    推送告警
    :param webhook_url:
    :param alert_content:
    :return:
    """
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": alert_content
        }
    }
    data_json = json.dumps(data)
    re_logger.info("ready send alert: {}".format(data_json))
    try:
        resp = requests.post(webhook_url, data=data_json, headers=headers, timeout=5, verify=False)
        if resp.status_code == 200:
            re_logger.info("send alert success")
            return True
        re_logger.error("send alert failed, response: {}".format(resp.text))
        return False
    except Exception as e:
        re_logger.error("send alert failed, exception: {}".format(e))
        re_logger.error(traceback.format_exc())
        return False


def handle(meta, alert):
    re_logger.info("start handle message")
    param_configs = meta.get("param_configs")
    if param_configs is None:
        re_logger.error("No param_configs in meta param")
        return False
    param_configs = convert_config(param_configs)
    webhook_url = check_config_item(param_configs, "webhook_url")  #没必要
    # 获取短信内容
    alert_content = content(alert)
    if alert_content:
        return send_alert(webhook_url, alert_content)