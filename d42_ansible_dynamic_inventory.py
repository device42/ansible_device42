#!/usr/bin/env python

import argparse
import imp
import sys
from lib import *

conf = imp.load_source('conf', 'conf')

try:
    import json
except ImportError:
    import simplejson as json


class Inventory(object):

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        self.args = parser.parse_args()

        # Called with `--list`.
        if self.args.list:
            self.inventory = self.inventory()
        # Called with `--host [hostname]`.
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()

        print json.dumps(self.inventory)

    # Example inventory for testing.
    def inventory(self):
        rest = REST(conf)
        returned_devices = rest.get_devices()

        if conf.GROUP_BY not in available_groups:
            print '\n[!] ERROR: wrong grouping name'
            sys.exit()

        ansible = Ansible(conf)
        return ansible.get_grouping(returned_devices)

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

# Get the inventory.
Inventory()
