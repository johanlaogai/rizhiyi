# -*- coding:utf-8

'''
Author:garmin
Time:2022/02/28

Editor:2u0y0u
Time:2022/07/15
'''

'''
参数解析：可见[POST]http://10.236.20.98:29520/sccp-api/system/dict/data/types
'''
# import random
import winsound
import requests
import time
import os
# import easygui
import json
# from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime

# 运行前请更新cookie
Cookie = 'username=zhanghx1056; Sccp-Admin-Token=01b34bf5-1a36-4c96-9cbd-7325d1b79139; Sccp-Admin-Expires-In=28800; loginStatus=1; sidebarStatus=0'
Authorization = "Bearer 01b34bf5-1a36-4c96-9cbd-7325d1b79139"


day_time = time.strftime("%Y-%m-%d", time.localtime())
logFileName = day_time + "_"+ str(time.time())[:10] + '.log'  #加上时间戳的前10位
with open('log/'+logFileName,'w',encoding="utf-8") as fw:
    fw.write("["+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"] - "+ "开始运行\n\n")

sendDept="lt"
# sendDeptName="总部"

receiveDept="lt46"
# receiveDeptName="国际公司"
# 反馈内容
feedbackDesc="国际公司收到，内部按要求处理。"
# 显示工单数量
pageSize = 10
# 统计已处理工单数
count = 0
# 轮询间隔时间（秒级，10代表每个10秒查询一次工单列表，并对未签收未反馈工单进行判定是否自动处理）
round_time = 10
# 进行签收动作的工单最短已下发时间（秒级，45代表只有下发了超过45秒才签收，不超过不签收，防止自动化签收明显）
qs_time = 40
# 进行反馈动作的工单最短已下发时间（秒级，60代表只有下发了超过60秒才反馈，不超过不反馈，防止自动化反馈明显）
fk_time = 60*1

instructionTypeDict = {"INS00":"封堵处置",
                        "INS01":"监测预警",
                        "INS02":"通知管理",
                        "INS03":"排查指令",
                        "INS04":"信息收集",
                        "INS05":"解封通告",
                        "INS06":"封禁指令",
                        "INS07":"信息统计",
                        "INS10":"涉密指令" }

def printRed(mess):
    import ctypes, sys
    STD_OUTPUT_HANDLE = -11
    FOREGROUND_RED = 0x0c  # red.
    FOREGROUND_BLUE = 0x09  # blue.
    FOREGROUND_GREEN = 0x0a  # green.
    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, FOREGROUND_RED)
    sys.stdout.write(mess + '\n')
    ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)

def printGreen(mess):
    import ctypes, sys
    STD_OUTPUT_HANDLE = -11
    FOREGROUND_RED = 0x0c  # red.
    FOREGROUND_BLUE = 0x09  # blue.
    FOREGROUND_GREEN = 0x0a  # green.
    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, FOREGROUND_GREEN)
    sys.stdout.write(mess + '\n')
    ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)

def getTimesSeconds(operatingTime):
    """
    用于计算工单下发和当前时间的时间差（秒）
    """
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  #当前时间yyyy-MM-dd HH:mm:ss
    now_time_struct = datetime.strptime(now_time, "%Y-%m-%d %H:%M:%S") #转datetime类型
    operatingTime_struct = datetime.strptime(operatingTime, "%Y-%m-%d %H:%M:%S")
    seconds = (now_time_struct - operatingTime_struct).total_seconds()
    return seconds  #相差秒数

def log(instruction,action,rp_text):
    """  记录日志，格式如下：
    [2011-05-05 16:37:06] - [签收指令/反馈指令]
    指令类型: 
    指令单号: 
    指令标题: 
    """
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open('log/'+logFileName,'a+',encoding="utf-8") as fw:
        fw.write("[%s] - [%s]\n指令类型: %s\n指令单号: %s\n指令标题: %s\n反馈响应信息: %s\n\n"%(now_time,action, instructionTypeDict[instruction['instructionType']], 
        instruction['taskNo'], instruction['instructionName'], rp_text))


def getInstructionDetail(instruction):
    instructionName = instruction['instructionName']
    taskNo = instruction['taskNo']
    instructionDesc = instruction['instructionDesc']
    instructionType = instructionTypeDict[instruction['instructionType']]    #指令类型
    # print(instructionType)
    fileName = taskNo + " " + instructionName + " " + instructionType
    root = "instructions/" + fileName
    workchat = "2023年重大活动保障"
    tag = "@黄传城 @张皓翔"
    # print(instruction)
    if instructionType in ("封堵处置", "解封通告"):
        workchat = "IP封堵-解封处置"
        tag = "@丁玮阳 @易珍珍  @龚育  @杨宜"
    if not os.path.exists(root):
        os.mkdir(root)  #创建目录  "instructions/" + fileName
        with open(root + "/readme.txt","w",encoding="utf-8") as fw:
            fw.write("发企微群[%s]转达以下通知并%s：\n\n【指挥调度平台工单处置】新增【%s】工单1例，请跟进处理！相关如下：\n指令类型: %s\n指令单号: %s\n指令标题: %s\n指令描述: %s" % (workchat, tag, instructionType, instructionType, taskNo, instructionName, instructionDesc))
        if instruction['taskFiles'] == None and instructionType in ("封堵处置","监测预警","解封通告"):
            url = "http://10.236.20.98:29520/sccp-api/business/disposal/export"
            data = "taskNo="+taskNo+"&"
            headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0','Cookie':Cookie,'Authorization':Authorization,'Content-Type': "application/x-www-form-urlencoded","Referer":"http://10.236.20.98:29520/nspp-soc/task/feedback","Pragma":"no-cache"}
            connect = 0
            while connect==0:
                try:
                    rq = requests.post(url, data=data, headers=headers)
                    connect = 1
                except:
                    printRed("下载附件出错，网络连接异常。访问接口：/sccp-api/business/disposal/export")
            if "Content-disposition" in rq.headers:
                name = urllib.parse.unquote(rq.headers["Content-disposition"].lstrip("attachment;filename="))
                with open(root + "/" + name,'wb') as fw:
                    fw.write(rq.content)
        else:
            if instruction['taskFiles'] != None:
                for f in instruction['taskFiles']:
                    url = f['url']
                    fileName = f['name']
                    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0','Cookie':Cookie,'Authorization':Authorization,'Content-Type': "application/x-www-form-urlencoded","Referer":"http://10.236.20.98:29520/nspp-soc/task/feedback","Pragma":"no-cache"}
                    connect = 0
                    while connect==0:
                        try:
                            rq = requests.get(url, headers=headers, verify=False)
                            connect = 1
                        except:
                            printRed("下载附件出错，网络连接异常。访问接口：/nspp-soc/task/feedback")
                    with open(root + "/" + fileName,'wb') as fw:
                        fw.write(rq.content)


def send_feedback_info(instruction):
    """发送反馈信息"""
    # 获取的工单log
    instruction = instruction
    p_log = {"instructionName":instruction["instructionName"],"taskNo":instruction["taskNo"],"instructionType":instruction["instructionType"],"needReport":0,"id":instruction["feedbackId"],"receiveDept":receiveDept,"feedbackDesc":feedbackDesc,"feedbackStatus":2}
    # 设置反馈消息 —> PUT形式 发送反馈内容
    url_put = "http://10.236.20.98:29520/sccp-api/business/instruction/feedback"
    # 反馈内容 -> feedbackDesc 
    payload = json.dumps(p_log)
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0','Cookie':Cookie,
             'Authorization':Authorization,'Content-Type': "application/json;charset=utf-8","Referer":"http://10.236.20.98:29520/nspp-soc/task/feedback","Pragma":"no-cache"}
    # print(payload)
    connect = 0
    while connect==0:  #发送一次直到成功
        try:
            r = requests.put(url_put,data=payload,headers=headers)
            connect = 1
        except:
            printRed("反馈内容出错，网络连接异常")
    # 反馈成功 -> {"msg":"操作成功","code":200}
    print("[+]","反馈成功",r.text)
    return r.text

def put_sign(instruction):
    """签收工单"""
    # 获取未签到的工单
    instruction = instruction
    # 需要进行put的log 用于对比
    p_log = {"taskNoIds":[instruction["taskNo"]+","+instruction["feedbackId"]]}
    # 设置反馈消息 —> PUT形式 发送反馈内容
    url_put = "http://10.236.20.98:29520/sccp-api/business/instruction/feedback/bulkSign"
    # 反馈内容 -> feedbackDesc 
    payload = json.dumps(p_log)
    # print(payload)
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0','Cookie':Cookie,'Authorization':Authorization,'Content-Type': "application/json;charset=utf-8","Referer":"http://10.236.20.98:29520/nspp-soc/task/feedback","Pragma":"no-cache","Origin": "http://10.236.20.98:29520"}
    connect = 0
    while connect==0:
        try:
            r = requests.put(url_put,data=payload,headers=headers)
            connect = 1
        except:
            printRed("签收工单出错，网络连接异常")
    # 反馈成功 -> {"msg":"操作成功","code":200}
    print("[+]","签收成功",r.text)
    return r.text
    
while True:
    try:
        # os.system("clear")
        print("= " * 100)
        print("当前时间：",time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        # 获取工单列表 pageNum:页码、pageSize:显示工单数量
        url='http://10.236.20.98:29520/sccp-api/business/instruction/feedbackList?pageNum=1&pageSize=%s&feedbackStatus=1' % pageSize
        # url='http://10.236.20.98:29520/sccp-api/business/instruction/feedbackList?pageNum=1&pageSize=%s' % pageSize
        # url='http://10.236.20.98:29520/sccp-api/business/instruction/feedbackList?pageNum=1&pageSize=%s&taskNo=INS20220718091218339&' % pageSize
        # headers头
        headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
                 'Cookie':Cookie,
                 'Authorization':Authorization}
        connect = 0
        while connect==0:
            try:
                response = requests.get(url, headers=headers)  #获取工单列表
                connect = 1
            except:
                printRed("获取工单列表出错，网络连接异常...")
        # req = BeautifulSoup(response.text, 'html.parser')
        log_list = json.loads(response.text)["rows"]
        print(log_list)

        # 遍历当前工单情况
        find = 0
        for i in log_list:
            instruction = i
            feedbackStatus = i["feedbackStatus"]  #状态
            signer = i['signer']  #签收者
            taskNo = i['taskNo'] #工单号
            instructionType = instructionTypeDict[i['instructionType']]    #指令类型
            operatingTime = i['operatingTime']  #下发时间 2022-07-26 10:12:24
            timePlus = getTimesSeconds(operatingTime) # 下发时间和当前时间的时间差
            # print(taskNo)
            instructionDesc = instruction["instructionDesc"].replace("\n","").replace(" ","").replace("\r","")  #工单详情
            if len(instructionDesc) > 100:
                instructionDesc = instructionDesc[0:80] + "..."
            feedback_info = ""
            # if (timePlus > 60 ) and (timePlus < 60*2 ):  # 测试代码
            if feedbackStatus == 1 and signer == None and (timePlus > qs_time ): #超过45秒才签收
                feedback_info = "【待签到反馈】"
                # print("[+]",feedback_info,feedbackStatus,log["createTime"],log["taskNo"],instructionDesc)
                printRed("[+]" + " " + feedback_info + " " + str(feedbackStatus) + " " + instruction["createTime"] + " " + instruction["taskNo"] + " " + instructionDesc)
                _t = int(str(time.time())[:10])
                if 30 <= _t%60 <= 59:
                    put_text = put_sign(instruction)  # 签收工单
                    log(instruction,"签收指令",put_text) # 日志记录签收
                    # log(instruction,"签收指令",test)
                if instructionType in ("封堵处置", "解封通告"):  #在getInstructionDetail处置
                    pass
                else:
                    feedback_info = "【待手工反馈】"
                    # print("[+]",feedback_info,feedbackStatus,log["createTime"],log["taskNo"],instructionDesc)
                    printRed("[+]" + " " + feedback_info + " " + str(feedbackStatus) + " " + instruction["createTime"] + " " + instruction["taskNo"] + " "+instructionDesc)
                    getInstructionDetail(instruction)
                    count += 1
                winsound.Beep(3000,1000)
            elif feedbackStatus == 1 and signer != None and (timePlus > fk_time ): #超过2分钟才反馈
                if instructionType in ("封堵处置", "解封通告"):
                    _t = int(str(time.time())[:10])
                    if 30 <= _t%60 <= 59:
                        send_text = send_feedback_info(instruction)
                         # 日志记录反馈
                        log(instruction,"反馈指令",send_text)
                        # log(instruction,"反馈指令",test)
                        # 获取工单细节，用于反馈
                        getInstructionDetail(instruction)
                        count += 1
                else:
                    find = 1
                    winsound.Beep(3000,1000)
        if find:
            printRed("="*10+"本轮查询：当前存在待手工反馈工单"+" "+"="*10+"\n\n")
        printGreen("="*10+"本次运行：总计已签收反馈工单数为 "+str(count)+" "+"="*10)
        response.close()
        time.sleep(round_time)  #每轮查询未反馈工单列表的时间间隔，当前为10s
        # time.sleep(30)
    except:
        printRed("脚本出现错误，可能是网络连接异常...")
        time.sleep(60)
        
