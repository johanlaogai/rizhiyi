import json
import csv
import re
from translate import Translator


# with open('test/rules.json','r',encoding="utf8") as ft:
#     contents = json.load(ft)
#     for con in contents:
#         for item in con:
#             print("{}:{}".format(item,con[item]))
#         print()
with open('test/rules.json','r') as ft,open("test/rule_to_en2.json", "w") as fp:
    res = []
    contents = json.load(ft)
    for con in contents:
        pattern_desc = r'eval desc = ([\s\S]+) \|'
        pattern_name = r'eval rule_name = ([\s\S]+)'
        desc = re.search(pattern=pattern_desc, string=con['extend_rule'], flags=0).group(1)
        extend_name = re.search(pattern=pattern_name,string=con['extend_rule'],flags=0).group(1)
        rule_name = con['rule_name']


        # 中文翻译成英文
        translator = Translator(from_lang="ZH|EN",to_lang="EN-US")
        tran_name = translator.translate(rule_name)
        tran_desc = translator.translate(desc)
        tran_extend_name = translator.translate(extend_name)

        print(rule_name)
        print(desc)
        print(extend_name)
        print(tran_name)
        print(tran_desc)
        print(tran_extend_name)

        con['rule_name'] = tran_name
        con['extend_rule'] = str(con['extend_rule']).replace(desc,tran_desc)
        con['extend_rule'] = str(con['extend_rule']).replace(extend_name,tran_extend_name)
        res.append(con)
        print()
    json.dump(res,fp)

print("写入完成")
