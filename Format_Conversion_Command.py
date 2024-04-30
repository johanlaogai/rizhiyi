import re
name = '【集中日志审计系统提醒】-东莞分公司 -月报'
res = re.search(r'-\s*(\S+)\s*-',name)
print(res.group(1))