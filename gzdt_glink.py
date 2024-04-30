#!/opt/rizhiyi/python/bin/python
# -*- coding: utf-8 -*-

"""
告警模板
"""
__author__ = 'hu.qingpo,wu.guoquan'

from django.template import Context, Template
import requests
import logging
import os
import time
import json
import hashlib
import base64

# 打印日志存储文件,一般不需要修改
log_file = "/data/rizhiyi/logs/yottaweb/alert.log"
# 日志的回写变量
global reply_content
reply_content = ""
# 告警的名称
global alert_name
alert_name = ""
# 告警的uuid
global alert_id
alert_id = ""


#日志相关配置
# logging部分设置,滚动生成5个文件，每个文件的最大为100M,不需要修改
if not os.path.exists( os.path.dirname( log_file ) ):
    os.makedirs( os.path.dirname( log_file ) )
# 获取META里面的name作为loging名字：
script_name = "gzdt_glink"
req_logger = logging.getLogger( script_name )
# 打印的日志级别,一般不需要修改，调试的时候修改
req_logger.setLevel( level=logging.INFO )
handler = logging.handlers.RotatingFileHandler( log_file, maxBytes=1024 * 1024 * 100, backupCount=5 )
formatter = logging.Formatter( "%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s" )
handler.setFormatter( formatter )
log_content = {logging.FATAL: req_logger.fatal, logging.ERROR: req_logger.error, logging.WARNING: req_logger.warning,
               logging.INFO: req_logger.info, logging.DEBUG: req_logger.debug}



# 既在日志中打印，又在执行结果中显示
def log_and_reply(log_level, comment):
    global reply_content
    reply_content = '%s%s%s' % (reply_content, "\n", comment)
    req_logger.addHandler( handler )
    comment = alert_name + " - " + alert_id + " - " + comment
    log_content.get( log_level )( comment )
    req_logger.removeHandler( handler )



#告警配置的meta信息
rizhiyi_name = "chenjunhao"
rizhiyi_key = "bmEhwadOhlCoTEfkDWbKAYJMOWdcEHUL"

#uuap应用编码（请求头参数）
appCode = "epidemicFill"
#uuap应用秘钥（请求头参数）
appKey = "asdfd7834lkwepoxcmsdSwe"
#填入glink管理员生成的订阅号编码
serviceCode="508400fe-7de9-46c7-b36a-7e4f4d51ca30"


#获取日志易集群的用户列表信息
user_name_set = {"test01"}
user_name_set.clear()


try:
    rizhiyi_url = "http://10.32.189.5/api/v2/accounts/?page=0&size=2000&sort=-id&type=readable"
    rizhiyi_header = {'Authorization':'apikey ' +  rizhiyi_name + ":" + rizhiyi_key  }
    rizhiyi_account_list_res = requests.get(rizhiyi_url,headers=rizhiyi_header,timeout=10)
    log_and_reply( logging.DEBUG, "获取用户列表开始。" )
    if rizhiyi_account_list_res.status_code == 200:
        if json.loads( rizhiyi_account_list_res.text ).get("result"):
            user_list = json.loads( rizhiyi_account_list_res.text ).get("objects")
    if len(user_list) != 0 :
        for user in user_list:
            user_name = ""
            name = str(user.get("name"))
            full_name = str(user.get("full_name"))
            user_name = name + "_" + full_name
            user_name_set.add(user_name)
            log_and_reply( logging.DEBUG, "获取用户列表结束，用户列表数：%s。" % len(user_name_set))
except Exception as e:
    log_and_reply( logging.ERROR, "获取用户列表失败:%s" % e )

user_name_list = []
for  user_name in user_name_set:
    user_name_list.append(user_name)

# 告警模板
ONLINE_CONTENT = """
{% if alert.is_alert_recovery %}
    {{ alert.name }}已经恢复
{% else %}  
    在{{ alert.send_time|date:"Y年n月d日 H:i:s" }}时名称是{{ alert.name }}的告警触发,告警内容是：{{ alert.strategy.trigger.compare_desc_text }}
{% endif %}
"""

# 元数据
META = {
    "name": "gzdt_glink",
    "version": 5,
    "alias": "广州地铁glink消息推送",
    "configs": [
         {
             "name": "touser",
             "alias": "成员ID列表",
             "presence": True,
             "value_type": "string",
             "input_type": "drop_down_multiple",
             "input_candidate": user_name_list,
             "default_value": "",
             "style": {
                 "rows": 1,
                 "cols": 20
             }
         },
         {
             "name": "content",
             "alias": "告警内容",
             "presence": True,
             "value_type": "template",
             "default_value": ONLINE_CONTENT
         }
    ]
}






def _render(conf_obj, tmpl_str):
    """
    渲染模板
    :param conf_obj:
    :param tmpl_str:
    :return:
    """
    t = Template( tmpl_str )
    c = Context( conf_obj )
    _content = t.render( c )
    return _content

# 读取告警高级配置里面生成的图片
def add_graph_to_text(params, content):
    graph_path = ""
    if "timechart_trend_path" in params:
        graph_path = params.get( 'timechart_trend_path' )
        log_and_reply( logging.INFO, ("图片的路径是：%s" % graph_path) )
        fp = open( graph_path, 'rb' )
        base64_data = base64.b64encode( fp.read() )
        fp.close()
        imageHtml = "<img src=\"data:image/jpg;base64,%s\" style=\"width:700px\"/><br><br>" % (base64_data)
        content = content.replace( "<br><img src=\"cid:timechart_trend\"/><br><br>", imageHtml)
    else:
        # 如果没有图片，这里就去掉显示图片的地方，否则会有一个图裂，但是不知道需不需要保留这个图裂，以作提示
        content = content.replace( "<br><img src=\"cid:timechart_trend\"/><br><br>", "" )
    return content


def content(params, alert, isHandle=False):
    """
    预览展现
    :param params:
    :param alert:
    :return:
    """
    alert_class = AlertAction( params, alert )
    global alert_id
    alert_id = alert_class.alert_md5( script_name )

    #打印content输入的参数
    for key in list(params.keys()):
        log_and_reply( logging.DEBUG, ("content的params：%s ===>%s" % (key, params.get( key ))) )
    for key in list(alert.keys()):
        log_and_reply( logging.DEBUG, ("content的alert：%s ===>%s" % (key, alert.get( key ))) )

    template_str = params.get( 'configs' )[len( params.get( 'configs' ) ) - 1].get( 'value' )
    conf_obj = {'alert': alert}
    _content = _render( conf_obj, template_str ) + "\n alert_id:" + alert_id
    if not isHandle:
        _content = add_graph_to_text( params, _content )
    return _content


def handle(params, alert):
    """
    发送消息
    :param params:
    :param alert:
    """
    try:
        alert_start_time = round( time.time() * 1000 )
        alert_class = AlertAction( params, alert )
        global alert_id
        alert_id = alert_class.alert_md5( script_name )
        global alert_name
        alert_name = _render( {'alert': alert}, "{{ alert.name }}" )
        log_and_reply( logging.INFO, ("插件开始执行") )

        # 打印content输入的参数
        for key in list(params.keys()):
            log_and_reply( logging.DEBUG, ("handle的params：%s ===>%s" % (key, params.get( key ))) )
        for key in list(alert.keys()):
            log_and_reply( logging.DEBUG, ("handle的alert：%s ===>%s" % (key, alert.get( key ))) )

        # 插件执行
        alert_class.action()

        log_and_reply( logging.INFO, "插件运行完成，运行耗时：%dms" % int( round( time.time() * 1000 ) - alert_start_time ) )
    except Exception as e:
        log_and_reply( logging.ERROR, ("插件运行报错，错误信息：%s" % (e)) )
        raise e





# 在前台调试的时候打印日志
def execute_reply(params, alert):
    log_and_reply( logging.INFO, "reply_content start" )
    handle( params, alert )
    log_and_reply( logging.INFO, ("reply_content: %s" % (reply_content)) )
    return reply_content


class AlertAction():

    def __init__(self, params, alert):
        self.params = params
        self.alert = alert

    def alert_md5(self, script_name):
        # 使用发送时间+插件名称+执行时间+脚本名称做MD5值
        md5_str = str(self.alert["send_time"]) + str(self.alert["name"]) + str(
            self.alert["exec_time"] ) + script_name
        md5 = hashlib.md5()
        md5.update( md5_str.encode( 'utf-8', 'strict' ) )
        sign = md5.hexdigest()
        return sign

    def init_meta(self):
        """
        初始化meta配置的数据
        :param :
        :alert :
        :return:返回一个包含所有meta值的dict，key是 meta的name，value是其值
        """
        log_and_reply( logging.DEBUG, "调用init_meta方法，params:%s,alert:%s" % (self.params, self.alert) )
        meta_dict = {}
        meta_config = META.get( 'configs' )
        log_and_reply( logging.DEBUG, "init_meta开始执行,%s" % meta_config )
        for i in range( 0, len( meta_config ) ):
            name = meta_config[i].get( 'name' )
            name_type = meta_config[i].get( 'value_type' ).lower()
            # 获取meta的输入框的值
            name_value = self.params.get( 'configs' )[i].get( 'value' )
            if name_type == "template":
                conf_obj = {'alert': self.alert}
                name_value = _render( conf_obj, name_value )
            meta_dict[name] = str( name_value )
        for key, values in list(meta_dict.items()):
            log_and_reply( logging.DEBUG, "meta_dict的字典:%s===>%s" % (key, values) )
        return meta_dict

    # 告警触发的实际操作：
    def action(self):
        """
        告警具体触发的操作：
        """
        try:
            init_meta = self.init_meta()
            # 打印初始化的参数列表和值列表
            for key, value in list(init_meta.items()):
                log_and_reply( logging.DEBUG, ("init_meta的参数名：%s，参数值：%s" % (key, value)) )

            # action具体的操作：
            receiverIds = []
            for usename in init_meta.get( "touser" ).replace("[","").replace("]","").replace("'","").replace(" ","").split(","):
                receiverIds.append(str(usename.split("_")[0]))
                log_and_reply( logging.DEBUG, "usename:%s," % (str(usename.split("_")[0])) )


            glink_url = "http://zt.gzmetro.com/glinkms-api/uniserMessage/sendMessage"
            glink_headers = {
                 "Accept" : "*/*",
                 "Accept-Encoding" : "gzip,deflate,br",
                 "Connection" : "keep-alive",
                 "Content-Type" : "application/json",
                 "appCode" : appCode ,
                 "appKey" : appKey
            }
            glink_data = {
                "serviceCode" : serviceCode,                                      #填入glink管理员生成的订阅号编码
                "msgContent" : str(init_meta.get( "content" )),                   #告警内容
                "receiverIds" : receiverIds,                                      #接受人列表
                "msgType" : "simple",                                             #发送消息类型，simple是简单文本消息，complex是富文本消息
                "userDataType" : "accountName",                                   #用户接受帐号类型，accountName是用户帐号
                "msgTitle" : "",
                "msgAppCode" : "",
                "msgAppUrl" : "",
                "msgParam" : "",
                "msgTargetUrl" : "",
                "senderId" : "日志易告警",
                "toDeviceType" : ""
             }
            # header里面指明了为json格式，utf-8编码
            json_data = json.dumps( glink_data, ensure_ascii=False ).encode("utf-8")
            self.post(glink_url,glink_headers,json_data)
        except Exception as e:
            raise e

    # 告警触发的post请求
    def post(self, url, glink_headers,data):
        log_and_reply( logging.INFO, "请求数据体: url:%s,glink_headers:%s,json_data:%s," % ( url, json.dumps( glink_headers, ensure_ascii=False ) , data) )
        try:
            res = requests.post( url,headers=glink_headers, data=data)
            log_and_reply( logging.INFO, "返回code:%s,响应时间:%sms" % (res.status_code, res.elapsed.total_seconds() * 1000) )
            if res.status_code == 200:
                log_and_reply( logging.INFO, "数据已经发送,返回内容：%s" % res.text )
            else:
                raise Exception( "数据发送失败,返回的错误信息是：%s" % res.text )
        except Exception as e:
            raise Exception( "数据发送失败,返回的错误信息是：%s" % e )
