# coding:utf-8

from OTXv2 import OTXv2
from OTXv2 import IndicatorTypes
import json, sys

otx = OTXv2("e801c191596ce48f9d2a0dd489c41dee5b51e03aa3838102e146e5a28ef3cb9b")


def getValue(results, keys):
    if type(keys) is list and len(keys) > 0:

        if type(results) is dict:
            key = keys.pop(0)
            if key in results:
                return getValue(results[key], keys)
            else:
                return None
        else:
            if type(results) is list and len(results) > 0:
                return getValue(results[0], keys)
            else:
                return results
    else:
        return results


def ip(otx, ip):
    ti = {}
    content = []

    result = otx.get_indicator_details_by_section(indicator_type=IndicatorTypes.IPv4, indicator=ip, section='general')

    # Return nothing if it's in the whitelist
    validation = getValue(result, ['validation'])
    if not validation:
        pulses = getValue(result, ['pulse_info', 'pulses'])

        ip_info = {"ip_addr": ip}
        pulses.append(ip_info)

        content.append(pulses)

        ti['content'] = content
        print(json.dumps(ti))

    return None


def main():
    data = sys.argv[1]
    ip(otx, data)


if __name__ == '__main__':
    main()
