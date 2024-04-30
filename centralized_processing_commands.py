from datetime import datetime, timedelta
from time import sleep
import pymysql
import logging
import traceback
import json

#数据库配置
connection = pymysql.connect(  
    host='192.168.40.106',
    user="root",
    password="rizhiyi&2014",  
    db="rizhiyi_system",
    autocommit=True
)  
cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
#数据库搜素语句模版
check_modle = 'status="Running" && cur_version != expected_version && expected_version!="" && last_update_timestamp >="{}"'
updating_model = 'status="Running" && cur_version != expected_version && expected_version!=""'
update_model = 'id={} && platform="{}" && ip="{}"'
update_set_model = 'expected_version="{}"'
rollback_set_model = 'expected_version=""'
#存储升级成功和失败的IP
updated = {}
fail = {}

def generate_logger(name):
    FORMAT = '[%(asctime)s %(levelname)s] %(message)s'
    path = "/data/rizhiyi/logs/heka/{}.log".format(name)
    Logger = logging.getLogger(name)
    Logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename=path)
    handler.setFormatter(logging.Formatter(FORMAT))
    Logger.addHandler(handler)
    return Logger

apiLog = generate_logger("updates")
script = generate_logger("script")

#数据库select语句执行
def select_operation(filter):
    command = 'SELECT ip,last_update_timestamp,platform,cur_version,expected_version,id \
                from AgentStatus  \
                where {} '
    script.info(command.format(filter))
    # 检查连接是否断开，如果断开就进行重连
    connection.ping(reconnect=True)
    # 使用 execute() 执行sql
    cursor.execute(command.format(filter))
    data = cursor.fetchall()
    connection.commit()
    return data

#数据库update语句执行
def update_operation(se,wh):
    command = 'UPDATE AgentStatus \
            SET {} \
            where {}'
    script.info(command.format(se,wh))
    try:
        # 检查连接是否断开，如果断开就进行重连
        connection.ping(reconnect=True)
        # 使用 execute() 执行sql
        cursor.execute(command.format(se,wh))
        # 提交事务
        connection.commit()
    except Exception as e:
        script.exception("操作出现错误：{}".format(e))
        # 回滚所有更改
        connection.rollback()


def wait_sec(second):
    script.info("等待{}秒".format(str(second)))
    sleep(second)

#判断agent是否过期
def is_expired(minutes=0):
    # 获取当前时间  
    current_time = datetime.now()   
    time_difference = current_time - timedelta(minutes=30)
    return time_difference.strftime("%Y-%m-%d %H:%M:%S")

#升级是否超时
def update_timeout(ip): 
    start_time = updated.get(ip,None)
    if start_time is None:
        return True
    else:
        current_time = datetime.now()
        time_difference = current_time - start_time
        return time_difference > timedelta(minutes=15)
    

def roll_back(data,platform):
    #升级回滚
    for updating in data:
        if update_timeout(updating['ip']):
            update = update_model.format(updating['id'],platform,updating['ip'])
            script.error("Upgrade time is too long，{} has been rolled back".format(updating['ip']))
            update_operation(rollback_set_model,update)
            fail[updating['ip']] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#批量滚动升级
def filter_agent(iterator,expected_version,platform):
    i = 0
    print(fail)
    script.info("当前数量：{}".format(len(iterator)))
    for item in iterator:
        script.info(item)
    for item in iterator:
        script.info("当前已更新了：{}".format(i))
        while True:  
            try: 
                modle = check_modle.format(is_expired())
                data = select_operation(modle)
                num = len(data)  
            except pymysql.err as e:
                traceback.print_exc()  
                script.error("查询时发生一个错误")  
                script.exception("发生了一个错误: %s", str(e))
            except Exception as e:   
                script.exception("发生了一个错误: %s", str(e))
                traceback.print_exc()  

            script.info("当前升级数量：{}".format(num))
            if item['ip'] in fail:
                break
            if num <10: #同时升级的数量不能大于10,
                updated[item['ip']] = datetime.now()
                update_set = update_set_model.format(expected_version)
                update = update_model.format(item['id'],platform,item['ip'])
                update_operation(update_set,update) #逐个升级
                check_version()
                i+=1
                break
            roll_back(data,platform)
            wait_sec(60)
        wait_sec(5)  #升级间隔
    wait_sec(1000)
    modle = check_modle.format(is_expired())
    data = select_operation(modle)
    roll_back(data,platform)


def check_version():  
    sleep(10)    
    # 检查cur_version和expected_version是否相等  
    for item in select_operation(updating_model):
        apiLog.info("{}：当前版本{}==> 升级版本{},升级中....... ".format(item['ip'],item['cur_version'],item['expected_version']))
    apiLog.info("Waiting for Cur version and Expected version to be equal....") 


if __name__ == "__main__":
    try:
        with open('/data/rizhiyi/logs/heka/failed_update.json','r+') as fp:
            fail = json.load(fp)
    except:
        fail = {}
    modle = 'status="Running" && platform="{}" && cur_version="{}" && last_update_timestamp >="{}" && ip!="" limit 1000'
    check_version()
    #升级Linux-x64，当前版本3.8.0.9
    linux64 = select_operation(filter=modle.format("linux-x64","3.8.0.9",is_expired()))
    filter_agent(linux64,"4.8.0.7","linux-x64")  #期望版本4.8.0.7
    with open('/data/rizhiyi/logs/heka/failed_update.json','w') as fp:
        fail = json.dump(fail,fp)
    check_version()
    cursor.close()
    connection.close()
    script.info("进程结束")