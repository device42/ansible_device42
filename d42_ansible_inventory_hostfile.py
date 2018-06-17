import imp
import sys
import json
import requests
from lib import *

conf = imp.load_source('conf', 'conf')

try: requests.packages.urllib3.disable_warnings()
except: pass

if __name__ == '__main__':

    ansible = Ansible(conf)
    groups = ansible.get_grouping(Device42(conf).doql())

    if ansible.write_inventory_file(groups) is True:
        print '\n[!] Done!'
    else:
        print '\n[!] Can\'t write to file'
    sys.exit()
