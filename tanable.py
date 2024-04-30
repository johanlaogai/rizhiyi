# _*_ coding:utf-8 _*_
import requests
import json
import sys
import time
import urllib3

tenableurl = "https://10.120.26.208"
siem_api = "http://10.120.54.231:8380/loopholes/create"
headers = {'x-apikey': 'accessKey=6809db04e1244a909f106a44ad00a673;secretKey=1a620e52f1e64cdfb79cabf4ad09b273','content-type': 'application/json'}
def getScanId():
    scanId = []
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    req = requests.get('%s/rest/scanResult' %(tenableurl),headers=headers,verify=False)
    resp = json.loads(req.text)
    print(resp)
    datas = resp['response']['usable']
    for data in datas:
        if data['status'] == "Completed":
            scanId.append(data['id'])
        else:
            continue
    return scanId

def getAnalysis():
    analysis = []
    scanIds = getScanId()
    #scan = ['1349']
    for scanId in scanIds:
        queryData = {}
        query = {}
        filters = {}
        filter_ = []
        filters['filterName'] = "severity"
        filters['operator'] = "="
        filters['value'] = "4,3,2,1"
        filter_.append(filters)
        query['type'] = "vuln"
        query['tool'] = "vulndetails"
        query['vulnTool'] = "vulndetails"
        query['filters'] = filter_
        query['scanID'] = scanId
        query['view'] = "all"
        query["startOffset"] = 0
        query['endOffset'] = 9999999
        queryData['query'] = query
        queryData['sourceType'] = "individual"
        queryData['type'] = "vuln"
        queryData['scanID'] = scanId
        req = requests.post("%s/rest/analysis" %(tenableurl),data=json.dumps(queryData),headers=headers,verify=False)

        resp = json.loads(req.text)
        results = resp['response']['results']
        for result in results:
            vulnInfo = {}
            vulnInfo['loophole_id'] = result['pluginID']
            #vulnInfo['loophole_name'] = result['name']
            vulnInfo['description'] = result['description']
            vulnInfo['solution'] = result['solution']
            if int(result['severity']['id']) == 4:
                risk = 2
            elif int(result['severity']['id']) == 3:
                risk = 2
            elif int(result['severity']['id']) == 2:
                risk = 1
            else:
                risk = 0
            vulnInfo['risk_level'] = risk
            vulnInfo['siem_risk_level'] = risk
            vulnInfo['app_classif'] = result['family']["name"]
            vulnInfo['system_classif'] = result['netbiosName']
            vulnInfo['cve_id'] = result['cve']
            vulnInfo['host'] = result['ip']
            vulnInfo['scan_id'] = scanId
            vulnInfo['source'] = "Tenable"
            starttime = result['firstSeen']
            endtime = result['lastSeen']
            start_ = time.localtime(float(starttime))
            end_ = time.localtime(float(endtime))
            start = time.strftime("%Y-%m-%d %H:%M:%S",start_)
            end = time.strftime("%Y-%m-%d %H:%M:%S",end_)
            vulnInfo['scanner_start_time'] = start
            vulnInfo['scanner_end_time'] = end
            analysis.append(vulnInfo)
    return analysis

def getname():
    vulns = getAnalysis()
    
    for vuln in vulns:
        id_ = vuln['loophole_id']
        req = requests.get('%s/rest/plugin/%s' %(tenableurl,id_),headers=headers,verify=False)
        resp = json.loads(req.text)
        name = resp['response']['name']
        vuln['loophole_name'] = name
    return  vulns

def toSIEM(taskInfo):
    datas = taskInfo
    resp = requests.post(siem_api,data=json.dumps(datas),headers={'Content-Type':'application/json'})

def main():
    datas = getname()
    for data in datas:
        toSIEM(data)

if __name__ == '__main__':
    main()