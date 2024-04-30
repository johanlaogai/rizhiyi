from datetime import datetime, timedelta
from time import sleep
import pymysql
import logging

connection = pymysql.connect(  
    host='192.168.40.106',
    user="root",
    password="rizhiyi&2014",  
    db="rizhiyi_system",
)  

log_path = '/data/rizhiyi/logs/heka/updates.log'
FORMAT = '[%(asctime)s %(levelname)s] %(message)s'
apiLog = logging.getLogger("cmdb")
apiLog.setLevel(logging.INFO)
handler = logging.FileHandler(filename=log_path)
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
apiLog.addHandler(handler)

script_path = '/data/rizhiyi/logs/heka/script.out'
script = logging.getLogger("script")
script.setLevel(logging.INFO)
script_handler = logging.FileHandler(filename=script_path)
script_handler.setFormatter(formatter)
script.addHandler(script_handler)


def select_operation(cursor,filter):
    command = 'SELECT ip,last_update_timestamp,platform,cur_version,expected_version,id \
                from AgentStatus  \
                where {} '
    script.info(command.format(filter))
    cursor.execute(command.format(filter))
    return cursor.fetchall()


def update_operation(cursor,filter={}):
    command = 'UPDATE AgentStatus \
            SET expected_version="{expected_version}" \
            where id={start_id} && platform="{platform}" && ip="{ip}"'
    script.info(command.format(**filter))
    cursor.execute(command.format(**filter))
    connection.commit()


def is_expired():
    # 获取当前时间  
    current_time = datetime.now()  
    time_difference = current_time - timedelta(minutes=30)
    return time_difference.strftime("%Y-%m-%d %H:%M:%S")
    

def filter_agent(cursor,iterator,expected_version,platform):
    i = 0
    modle = 'status="Running" && cur_version != expected_version && platform="{}" && expected_version!=""'
    script.info("当前数量：{}".format(len(iterator)))
    for item in iterator:
        script.info(item)
    for item in iterator:
        script.info("当前已更新了：{}".format(i))
        while True:  
            try: 
                num = len(select_operation(cursor,filter=modle.format(platform)))  #如果数据查询过快会导致数据库反应不过来，而报AttributeError
            except AttributeError:  
                script.error("Error: 'NoneType' object has no attribute 'read'") 
            except pymysql.Error as e:  
                script.error(e)  
            script.info("当前升级数量：{}".format(num))
            if num <10: #同时升级的数量不能大于10,
                update_operation(cursor,{"expected_version":expected_version,"start_id":item[5],"platform":platform,"ip":item[0]}) #逐个升级
                check_version(cursor)
                i+=1
                break
            script.info("等待30秒")
            sleep(30) #否则等待30秒，直到升级数量小于10
        script.info("等待100秒")
        sleep(100)  #更新后等待100秒


def check_version(cursor):  
    sleep(10)    
    # 检查cur_version和expected_version是否相等  
    cursor.execute('SELECT ip,cur_version,expected_version FROM AgentStatus where status="Running" && cur_version != expected_version && expected_version!=""')  
    for item in cursor.fetchall():
        apiLog.info("{}：当前版本{}==> 升级版本{},升级中....... ".format(item[0],item[1],item[2]))
    apiLog.info("Waiting for Cur version and Expected version to be equal....") 
    connection.commit()


if __name__ == "__main__":
    modle = 'status="Running" && platform="{}" && cur_version="{}" && last_update_timestamp >="{}" && ip!="" limit 20'
    cursor = connection.cursor()
    check_version(cursor)
    #更新expected_version字段  
    #升级linux386，当前版本3.8.0.9
    #linux386 = select_operation(cursor,filter=modle.format("linux-386","3.8.0.9"))
    #filter_agent(cursor,linux386,"4.8.0.7","linux-386") #期望版本4.8.0.7
    # #升级Linux-x64，当前版本3.8.0.9
    linux64 = select_operation(cursor,filter=modle.format("linux-x64","3.8.0.9",is_expired()))
    filter_agent(cursor,linux64,"4.8.0.7","linux-x64")  #期望版本4.8.0.7
    ##升级win-386，版本3.6.0.7
    #win386 = select_operation(cursor,filter=modle.format("win-386","3.6.0.7",is_expired()))
    #filter_agent(cursor,win386,"3.9.2.0","win-386") #期望版本3.9.2.0
    #升级win-386，版本3.8.0.9
    #win386 = select_operation(cursor,filter=modle.format("win-386","3.8.0.9",is_expired()))
    #filter_agent(cursor,win386,"3.9.2.0","win-386") #期望版本3.9.2.0
    script.info("执行完成，等待60秒...")
    sleep(60)
    cursor.close()
    connection.close()
    check_version(cursor)
    script.info("进程结束")