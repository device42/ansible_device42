from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
    name: device42.d42.d42
    plugin_type: inventory
    author:
      - Will Tome (@willtome)
    short_description: Device42 Inventory Plugin
    version_added: "2.10"
    description:
        - Device42 Inventory plugin
    extends_documentation_fragment:
        - constructed
    options:
        plugin:
            description: The name of the Device42 Inventory Plugin, this should always be 'device42.d42.d42'.
            required: True
            choices: ['device42.d42.d42']
        url:
            description: URI of Device42. The URI should be the fully-qualified domain name, e.g. 'your-instance.device42.net'.
            type: string
            required: True
            env:
                - name: D42_URL
        username:
            description: The Device42 user acount.
            type: string
            required: True
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
instance: https://10.10.10.10
username: admin
password: adm!nd42
keyed_groups:
    - key: d42_service_level
      prefix: ''
      separator: ''
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable, to_safe_group_name
import requests


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = 'device42.d42.d42'

    def parse(self, inventory, loader, path, cache=False): 
        super(InventoryModule, self).parse(inventory, loader, path)

        self._read_config_data(path)

        base_url = self.get_option('url')
        username = self.get_option('username')
        password = self.get_option('password')
        ssl_check = self.get_option('ssl_check')
        strict = self.get_option('strict')

        response = requests.get(f"{base_url}/api/1.0/devices/all", auth=(username, password), verify=ssl_check)
        objects = response.json()['Devices']
        for object_ in objects:
            host_name = self.inventory.add_host(to_safe_group_name(object_['name']))
            for k in object_.keys():
                self.inventory.set_variable(host_name, f'd42_{k}', object_[k])

            if object_['ip_addresses'] != []:
                self.inventory.set_variable(host_name, 'ansible_host', object_['ip_addresses'][0]['ip'])

            self._set_composite_vars(
                self.get_option('compose'),
                self.inventory.get_host(host_name).get_vars(), host_name,
                strict)

            self._add_host_to_composed_groups(self.get_option('groups'), dict(), host_name, strict)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), dict(), host_name, strict)



