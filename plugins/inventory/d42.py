#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
    module: d42
    plugin_type: inventory
    author:
        - Will Tome (@willtome)
        - Omar Sanchez (@osanchez42)
    short_description: Device42 Inventory Plugin
    version_added: "2.10"
    description:
        - Device42 Inventory plugin
    extends_documentation_fragment:
        - constructed
    options:
        plugin:
            description: The name of the Device42 Inventory Plugin, this should always be 'device42.d42.d42'.
            required: true
            choices: ['device42.d42.d42']
        url:
            description: URI of Device42. The URI should be the fully-qualified domain name, e.g. 'your-instance.device42.net'.
            type: string
            required: true
            env:
                - name: D42_URL
        username:
            description: The Device42 user account.
            type: string
            required: true
            env:
                - name: D42_USER
        password:
            description: The Device42 instance user password.
            type: string
            secret: true
            required: true
            env:
                - name: D42_PWD
        ssl_check:
            description: SSL verification.
            type: boolean
            default: true
            env:
                - name: D42_SSL_CHECK
'''

EXAMPLES = r'''
plugin: device42.d42.d42
url: https://10.10.10.10
username: admin
password: password
ssl_check: False
keyed_groups:
    - key: d42_service_level
      prefix: ''
      separator: ''
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable, to_safe_group_name
import requests


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = 'device42.d42.d42'

    def verify_file(self, path):
         valid = False
         if super(InventoryModule, self).verify_file(path):
             if path.endswith(('d42.yaml', 'd42.yml')):
                 valid = True
             else:
                 self.display.vvv('Skipping due to inventory source not ending in "d42.yaml" nor "d42.yml"')
         return valid


    def parse(self, inventory, loader, path, cache=False): 
        super(InventoryModule, self).parse(inventory, loader, path)

        self._read_config_data(path)

        base_url = self.get_option('url')
        username = self.get_option('username')
        password = self.get_option('password')
        ssl_check = self.get_option('ssl_check')
        strict = self.get_option('strict')

        try:
            objects = []

            response = requests.get(base_url + "/api/1.0/devices/all", auth=(username, password), verify=ssl_check, timeout=10)

            print('response code: ' + str(response.status_code))
            json_response = response.json()

            if 'Devices' in json_response:
                objects = json_response['Devices']

            for object_ in objects:
                host_name = self.inventory.add_host(to_safe_group_name(object_['name']))
                for k in object_.keys():
                    self.inventory.set_variable(host_name, 'd42_' + k, object_[k])

                if object_['ip_addresses'] != []:
                    self.inventory.set_variable(host_name, 'ansible_host', object_['ip_addresses'][0]['ip'])

                self._set_composite_vars(
                    self.get_option('compose'),
                    self.inventory.get_host(host_name).get_vars(), host_name,
                    strict)

                self._add_host_to_composed_groups(self.get_option('groups'), dict(), host_name, strict)
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), dict(), host_name, strict)
        except Exception as e:
            print(e)



