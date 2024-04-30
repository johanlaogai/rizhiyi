import json
import csv

# 打开并读取文件  
with open('./test/rules_20240412100716.json', 'r') as f:  
    data = json.load(f)  

content = [['rule_name']]

# 打印数据  
for item in data:
    # if item['is_enable'] == 1:
    content.append([item['rule_name']])




# with open('./test/ctgslb.csv','r') as f:
#     f_csv = csv.reader(f)  #生成csv迭代器
#     headers = next(f_csv)  #获取headers
#     for row in f_csv:  #获取每一行内容
#         for item in row[4].split('\n'):
#             content.append([row[2],item])


with open('rule.csv','w',newline='') as file:
    writer = csv.writer(file)
    writer.writerows(content)



