#!/usr/bin/env python

import argparse
import sys
from lib import *

try:
    import json
except ImportError:
    import simplejson as json

class Inventory(object):

    def __init__(self):
        parser = argparse.ArgumentParser()
        self.args = parser.parse_args()

        self.inventory = self.inventory()
        print json.dumps(self.inventory)

    def inventory(self):
        conf = get_conf()
        ansible = Ansible(conf)
        groups = ansible.get_grouping(Device42(conf).doql())
        groups['_meta'] = {'hostvars': {}}
        return groups

    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

Inventory()
