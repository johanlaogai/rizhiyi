# -*- coding: utf-8 -*-
# Author: Yottabyte
# Email: wu.guoquan@yottabyte.cn
# Date: 2023.06.08

import csv
import sys
import pymysql

host = "10.120.54.230"
port = 3306
user = "root"
pwd = "Cug#hk#13579"
db_name = "rizhiyi_system"

def main(host, port, user, pwd, db_name):
    infile = sys.stdin
    outfile = sys.stdout
    r = csv.reader(infile)
    w = csv.writer(outfile)
    conn = pymysql.connect(host=host, port=port, user=user, password=pwd, db=db_name, charset="utf8")
    cur=conn.cursor()
    for result in r:
        loophole_name = result[0]
        host = result[1]
        try:
            sql = "update siem_loophole_log set status=1 where name=\"%s\" and host=\"%s\";" % (loophole_name,host)
            cur.execute(sql)
            conn.commit()
            status = "提交成功"
        except Exception as e:
            conn.rollback()
            status = "提交失败"
        finally:
            result.append(status)
    conn.close()
    w.writerow(result)

main(host, port, user, pwd, db_name)