import requests
import json
import sys


ti = []
domain_z = {}

def vt(domain):
    url = "https://www.virustotal.com/api/v3/domains/{domain}".format(domain=domain)
    headers = {"accept": "application/json",'x-apikey': '1fa6f1bd1e1082823383181501a5018f97b1352f8051537fa0150a57adeafcd9'}
    response = requests.get(url, headers=headers)
    res = json.loads(response.text)
    res['domain'] = domain
    ti.append(res)
    domain_z["content"] = ti
    print(json.dumps(domain_z))

if __name__ == '__main__':
    query_data = sys.argv[1]
    result = vt(query_data)
