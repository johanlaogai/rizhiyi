import csv
import sys

headers = {
    'Rizhiyi-User-ID': '1',
    'Content-Type': 'application/json'
}

def main():
    infile = sys.stdin
    outfile = sys.stdout
    r = csv.reader(infile)
    w = csv.writer(outfile)
    for result in r:
        if result:
            #相加
            sum = int(result[0]) + int(result[1])
            result.append(sum)
            # 处理返回的结果
            w.writerow(result)                   