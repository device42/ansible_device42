
import imp
import sys
import json
import requests
from lib import *

conf = imp.load_source('conf', 'conf')

try: requests.packages.urllib3.disable_warnings()
except: pass

if __name__ == '__main__':
    logger = Logger(conf)
    rest = REST(conf, logger)
    rest_res = json.loads(rest.get_devices())

    if conf.GROUP_BY not in available_groups:
        print '\n[!] ERROR: wrong grouping name'
        sys.exit()

    ansible = Ansible(conf, logger)
    groups = ansible.get_grouping(rest_res)
    if ansible.write_inventory_file(groups) is True:
        print '\n[!] Done!'
    else:
        print '\n[!] Can\'t write to file'
    sys.exit()
