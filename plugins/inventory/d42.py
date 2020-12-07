from __future__ import (absolute_import, division, print_function)
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable, to_safe_group_name
import requests

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
        debug:
            description: Debug option.
            type: boolean
            default: false
            env:
                - name: D42_DEBUG
        clean_device_name:
            description: group name cleaning option.
            type: boolean
            default: true
            env:
                - name: D42_CLEAN_DEVICE_NAME
'''

EXAMPLES = r'''
plugin: device42.d42.d42
url: https://10.10.10.10
username: admin
password: password
ssl_check: False
debug: False
clean_device_name: True
keyed_groups:
    - key: d42_service_level
      prefix: ''
      separator: ''
'''


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

        strict = self.get_option('strict')

        try:
            try:
                clean_device_name = self.get_option('clean_device_name')
            except Exception:
                print("clean_device_name has not been defined in *.d42.yml. defaulting to False")
                clean_device_name = True

            objects = []

            json_response = self.get_d42_inventory()

            if 'Devices' in json_response:
                objects = json_response['Devices']

            for object_ in objects:
                if clean_device_name:
                    host_name = self.inventory.add_host(to_safe_group_name(object_['name']))
                else:
                    host_name = self.inventory.add_host(object_['name'])

                for k in object_.keys():
                    self.inventory.set_variable(host_name, 'd42_' + k, object_[k])

                if object_['ip_addresses']:
                    self.inventory.set_variable(host_name, 'ansible_host', object_['ip_addresses'][0]['ip'])

                self._set_composite_vars(
                    self.get_option('compose'),
                    self.inventory.get_host(host_name).get_vars(), host_name,
                    strict)

                self._add_host_to_composed_groups(self.get_option('groups'), dict(), host_name, strict)
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), dict(), host_name, strict)
        except Exception as e:
            print(e)

    def get_doql_json(self, query):
        base_url = self.get_option('url')
        username = self.get_option('username')
        password = self.get_option('password')
        ssl_check = self.get_option('ssl_check')
        debug = self.get_option('debug')

        data = {'output_type': 'json', 'query': query}

        try:
            # while there should be no timeout, ansible seems to get stuck sending requests without timeouts
            response = requests.post(base_url + "/services/data/v1.0/query/", data=data,
                                    auth=(username, password), verify=ssl_check, timeout=30)

            status_code = response.status_code

            if status_code == 500:
                print('an error was encountered on query API call to Device42')
                print('Response Status: ' + str(status_code))
                unformatted_d42_inventory = {}
            else:
                # csv response to json object
                if debug:
                    print('Response Status: ' + str(status_code))
                unformatted_d42_inventory = response.json()

        except Exception as e:
            if debug:
                print(e)
            return {}

        return unformatted_d42_inventory

    def get_d42_inventory(self):

        debug = self.get_option('debug')

        # the final inventory that will be returned
        inventory = {
            'total_count': None,
            'Devices': [],
        }

        # the dictionary below is used to build the json object
        d42_inventory = {}

        # get all the items from device42 that will be used to build the json object
        if debug:
            print('Getting Devices')
        d42_devices = self.get_devices()
        if debug:
            print('Getting IPs')
        d42_device_ips = self.get_ip_addresses()
        if debug:
            print('Getting MAC Addresses')
        d42_device_mac_addresses = self.get_mac_addresses()
        if debug:
            print('Getting HDD Details')
        d42_device_hdd_details = self.get_hdd_details()
        if debug:
            print('Getting Device External Links')
        d42_device_external_links = self.get_external_links()
        if debug:
            print('Getting Device Entitlements')
        d42_device_entitlements = self.get_device_entitlements()
        if debug:
            print('Getting Custom Fields')
        d42_device_custom_fields = self.get_custom_fields()

        for device in d42_devices:

            device_record = {}

            device_record['datastores'] = device.get('datastores')
            device_record['last_updated'] = device.get('last_edited')
            device_record['ip_addresses'] = []
            device_record['serial_no'] = device.get('serial_no')
            device_record['hw_depth'] = device.get('hw_depth')
            device_record['nonauthoritativealiases'] = str(device.get('nonauthoritativealiases')).split(',') if device.get('nonauthoritativealiases') is not None else []

            device_record['service_level'] = device.get('service_level')
            device_record['is_it_blade_host'] = 'no' if device.get('blade_chassis') == 'false' else 'yes'
            device_record['is_it_switch'] = 'no' if device.get('is_it_switch') == 'false' else 'yes'
            device_record['virtual_subtype_id'] = device.get('virtual_subtype_id')
            device_record['hw_size'] = device.get('hw_size')
            device_record['id'] = device.get('device_pk')

            # custom field
            device_record['custom_fields'] = []

            device_record['aliases'] = str(device.get('aliases')).split(',') if device.get('aliases') is not None else []
            device_record['category'] = device.get('category')

            # hdd details
            device_record['hdd_details'] = []

            device_record['uuid'] = device.get('uuid')
            device_record['virtual_subtype'] = device.get('virtual_subtype')
            device_record['cpuspeed'] = device.get('cpuspeed')
            device_record['hw_model'] = device.get('hw_model')
            device_record['osverno'] = device.get('os_version_no')
            device_record['type'] = device.get('type')
            device_record['hddcount'] = device.get('hard_disk_count')

            # external links
            device_record['device_external_links'] = []

            device_record['tags'] = device.get('tags')
            device_record['hw_model_id'] = device.get('hw_model_id')
            device_record['in_service'] = device.get('in_service')
            device_record['hddsize'] = device.get('disk_size')
            device_record['hddsize_type'] = 'GB'

            # mac addresses
            device_record['mac_addresses'] = []

            device_record['hddraid'] = device.get('hw_sw_raid')
            device_record['corethread'] = device.get('corethread')
            device_record['cpucount'] = device.get('cpucount')
            device_record["virtual_host_name"] = device.get('virtual_host_name')
            device_record["is_it_virtual_host"] = 'no' if device.get('virtual_host') == 'false' else 'yes'
            device_record["manufacturer"] = device.get('manufacturer')
            device_record["customer"] = device.get('customer')
            device_record["customer_id"] = device.get('customer_id')
            device_record["ucs_manager"] = device.get('ucsmanager')
            device_record["hddraid_type"] = device.get('raid_type')
            device_record["name"] = device.get('name')
            device_record["notes"] = device.get('notes')
            device_record["ram"] = device.get('ram')
            device_record["asset_no"] = device.get('asset_no')
            device_record["osarch"] = device.get('os_arch')
            device_record["osver"] = device.get('os_version_no')

            # line items
            device_record["device_purchase_line_items"] = []

            device_record["cpucore"] = device.get('cpucore')
            device_record["os"] = device.get('os_name')
            device_record["device_id"] = device.get('device_pk')

            # store the device in a dict for updates
            d42_inventory[device['device_pk']] = device_record

        for custom_field_record in d42_device_custom_fields:
            device_id = custom_field_record.get('device_pk')

            if device_id in d42_inventory:
                d42_inventory[device_id]['custom_fields'].append(
                    {
                        'key': custom_field_record.get('custom_field_key'),
                        'value': custom_field_record.get('custom_field_value')
                    }
                )

        for hdd_detail_record in d42_device_hdd_details:
            device_id = hdd_detail_record.get('device_pk')

            if device_id in d42_inventory:
                d42_inventory[device_id]['hdd_details'].append({
                    "raid_group": hdd_detail_record.get('raid_group'),
                    "serial_no": hdd_detail_record.get('hdd_serial_no'),
                    "raid_type": hdd_detail_record.get('hdd_raid_type'),
                    "hdd": {
                        "description": hdd_detail_record.get('hdd_description'),
                        "partno": hdd_detail_record.get('partno'),
                        "rpm": {
                            "id": hdd_detail_record.get('hdd_rpm_id'),
                            "name": hdd_detail_record.get('hdd_rpm')
                        },
                        "notes": hdd_detail_record.get('hdd_notes'),
                        "bytes": hdd_detail_record.get('hdd_bytes'),
                        "location": hdd_detail_record.get('hdd_location'),
                        "hd_id": hdd_detail_record.get('hdd_id'),
                        "manufacturer_id": hdd_detail_record.get('manufactuerer_id'),
                        "type": {
                            "id": hdd_detail_record.get('hdd_type_id'),
                            "name": hdd_detail_record.get('hdd_type_name')
                        },
                        "size": hdd_detail_record.get('size')
                    },
                    "part_id": hdd_detail_record.get('part_id'),
                    "hddcount": hdd_detail_record.get('hddcount'),
                    "description": hdd_detail_record.get('description')
                })

        for device_external_link_record in d42_device_external_links:
            device_id = device_external_link_record.get('device_pk')

            if device_id in d42_inventory:
                d42_inventory[device_id]['device_external_links'].append(
                    {
                        'notes': device_external_link_record.get('device_url_notes'),
                        'link': device_external_link_record.get('device_url')
                    }
                )

        for device_mac_address_record in d42_device_mac_addresses:

            device_id = device_mac_address_record.get('device_pk')

            if device_id in d42_inventory:
                d42_inventory[device_id]['mac_addresses'].append(
                    {
                        "mac": device_mac_address_record.get('mac'),
                        "vlan": device_mac_address_record.get('vlan'),
                        "port_name": device_mac_address_record.get('port_name'),
                        "port": device_mac_address_record.get('port')
                    }
                )

        for device_entitlement_record in d42_device_entitlements:

            device_id = device_entitlement_record.get('device_pk')

            if device_id in d42_inventory:
                d42_inventory[device_id]['device_purchase_line_items'].append(
                    {
                        "purchase_id": device_entitlement_record.get('purchase_id'),
                        "line_start_date": device_entitlement_record.get('line_start_date'),
                        "line_no": device_entitlement_record.get('line_no'),
                        "line_renew_date": device_entitlement_record.get('line_renew_date'),
                        "line_notes": device_entitlement_record.get('line_notes'),
                        "line_quantity": device_entitlement_record.get('line_quantity'),
                        "line_frequency": device_entitlement_record.get('line_frequency'),
                        "line_cost": device_entitlement_record.get('line_cost'),
                        "line_cancel_policy": device_entitlement_record.get('line_cancel_policy'),
                        "line_item_type": device_entitlement_record.get('line_item_type'),
                        "purchase_order_no": device_entitlement_record.get('purchase_order_no'),
                        "line_type": device_entitlement_record.get('line_type'),
                        "line_service_type": device_entitlement_record.get('line_service_type'),
                        "line_end_date": device_entitlement_record.get('line_end_date'),
                        "line_contract_type": device_entitlement_record.get('line_contract_type')
                    }
                )

        for device_ip_record in d42_device_ips:
            device_id = device_ip_record.get('device_pk')

            if device_id in d42_inventory:
                d42_inventory[device_id]['ip_addresses'].append(
                    {
                        "subnet_id": device_ip_record.get('subnet_id'),
                        "ip": device_ip_record.get('ip'),
                        "label": device_ip_record.get('label'),
                        "type": device_ip_record.get('type'),
                        "subnet": device_ip_record.get('subnet')
                    }
                )

        # now that the dictionary has been constructed, remove device id keys and keep value
        # add additional imformation like total_count

        total_count = 0
        for key, value in d42_inventory.items():
            inventory['Devices'].append(value)
            total_count += 1

        # update with the final device count
        inventory['total_count'] = total_count

        return inventory


    def get_devices(self):

        device_query = """
            select
            view_device_v1.*,
            view_device_v1.customer_fk as customer_id,
            customer.name as customer,
            t_cost.cost,
            view_vendor_v1.name as manufacturer,
            view_device_v1.type as hw_model,
            view_hardware_v1.hardware_pk as hw_model_id,
            vendor.name as manufacturer,
            view_hardware_v1.is_it_switch,
            view_hardware_v1.is_it_blade_host,
            view_hardware_v1.depth as hw_depth,
            view_hardware_v1.size as hw_size,
            vhost.name as virtual_host_name,
            nonauthoritativealias.alias_names as nonauthoritativealiases,
            alias.alias_names as aliases,
            obj_category.name as category,
            case
                WHEN view_device_v1.hz = 'MHz' and view_device_v1.cpupower is not null
                    THEN view_device_v1.cpupower / 1000
                ELSE
                    view_device_v1.cpupower
                END as cpuspeed,
            case
                WHEN view_device_v1.ram_size_type = 'MB' and view_device_v1.ram is not null
                    THEN view_device_v1.ram / 1024
                WHEN view_device_v1.ram_size_type = 'TB' and view_device_v1.ram is not null
                    THEN view_device_v1.ram * 1024
                ELSE
                    view_device_v1.ram
                END as ramsize,
            network_ip.ip_address, network_hw.hwaddress,
            CEIL(COALESCE(p.total_part_disk_size,
                            CASE
                                WHEN view_device_v1.hard_disk_count IS NOT NULL AND
                                     view_device_v1.hard_disk_size IS NOT NULL AND
                                     view_device_v1.hard_disk_size_type IS NOT NULL THEN
                                        view_device_v1.hard_disk_count *
                                        CASE
                                            WHEN view_device_v1.hard_disk_size_type = 'GB'
                                                THEN view_device_v1.hard_disk_size
                                            WHEN view_device_v1.hard_disk_size_type = 'TB'
                                                THEN view_device_v1.hard_disk_size * 1024
                                            WHEN view_device_v1.hard_disk_size_type = 'PB'
                                                THEN view_device_v1.hard_disk_size * 1024 * 1024
                                            ELSE
                                                NULL
                                        END
                                ELSE NULL
                            END)) AS disk_size
            from view_device_v1
            left join view_hardware_v1
                on view_device_v1.hardware_fk = view_hardware_v1.hardware_pk
            left join  (select view_ipaddress_v1.device_fk,  string_agg(host(view_ipaddress_v1.ip_address)::character varying, ', ' order by view_ipaddress_v1.ip_address) as ip_address from view_ipaddress_v1 group by view_ipaddress_v1.device_fk) network_ip
                on view_device_v1.device_pk=network_ip.device_fk
            left join (select device_fk, string_agg(view_netport_v1.hwaddress :: macaddr::character varying, ', ' order by view_netport_v1.hwaddress) as hwaddress from view_netport_v1 where view_netport_v1.hwaddress is null or (view_netport_v1.hwaddress is not null and LENGTH(view_netport_v1.hwaddress)=12)  group by view_netport_v1.device_fk) network_hw
                on view_device_v1.device_pk=network_hw.device_fk
            left join (select device_fk, sum(cost) as cost from view_purchaselineitem_v1 left join view_purchaselineitems_to_devices_v1 on purchaselineitem_fk = purchaselineitem_pk group by device_fk) t_cost
                on t_cost.device_fk=device_pk
            left join view_vendor_v1
                on vendor_pk=vendor_fk
            left join (select device_fk, string_agg(view_devicenonauthoritativealias_v1.alias_name, ', ' order by view_devicenonauthoritativealias_v1.alias_name) as alias_names from view_devicenonauthoritativealias_v1 group by view_devicenonauthoritativealias_v1.device_fk) nonauthoritativealias
                on view_device_v1.device_pk=nonauthoritativealias.device_fk
            left join (select device_fk, string_agg(view_devicealias_v1.alias_name, ', ' order by view_devicealias_v1.alias_name) as alias_names from view_devicealias_v1 group by view_devicealias_v1.device_fk) alias
                on view_device_v1.device_pk=alias.device_fk
            left join (select device_pk, name from view_device_v1) vhost
                on view_device_v1.virtual_host_device_fk=vhost.device_pk
            left join (select objectcategory_pk, name from view_objectcategory_v1) obj_category
                on view_device_v1.objectcategory_fk = obj_category.objectcategory_pk
            left join (select vendor_pk, name from view_vendor_v1) vendor
                on view_hardware_v1.vendor_fk = vendor.vendor_pk
            left join (select customer_pk, name from view_customer_v1) customer
                on view_device_v1.customer_fk = customer.customer_pk
            LEFT OUTER JOIN (
               SELECT p.device_fk,
                 SUM(p.pcount *
                     CASE
                       WHEN pm.hdsize_unit = 'GB'
                           THEN pm.hdsize
                       WHEN pm.hdsize_unit = 'TB'
                           THEN pm.hdsize * 1024
                       WHEN pm.hdsize_unit = 'PB'
                           THEN pm.hdsize * 1024 * 1024
                       WHEN pm.hdsize_unit = 'EB'
                           THEN pm.hdsize * 1024 * 1024 * 1024
                       WHEN pm.hdsize_unit = 'ZB'
                           THEN pm.hdsize * 1024 * 1024 * 1024 * 1024
                       WHEN pm.hdsize_unit = 'YB'
                           THEN pm.hdsize * 1024 * 1024 * 1024 * 1024 * 1024
                       ELSE
                           NULL
                     END) AS total_part_disk_size
                 FROM view_part_v1 p
                 INNER JOIN view_partmodel_v1 pm ON p.partmodel_fk = pm.partmodel_pk
                 WHERE pm.type_id = 3 AND pm.hdsize IS NOT NULL AND p.pcount > 0 AND p.device_fk IS NOT NULL
                 GROUP BY p.device_fk
             ) AS p ON view_device_v1.device_pk = p.device_fk
        """

        return self.get_doql_json(device_query)


    def get_custom_fields(self):

        custom_field_query = """
                select
                view_device_v1.device_pk,
                view_device_v1.name,
                custom_field.key as custom_field_key,
                custom_field.value as custom_field_value
                from view_device_v1
                inner join (select device_fk, type, key,
                                  (CASE
                                    WHEN view_device_custom_fields_v1.type = 'Related Field'
                                        THEN (CASE
                                                WHEN view_device_custom_fields_v1.related_model_name = 'endusers'
                                                THEN (SELECT name FROM view_enduser_v1 WHERE view_enduser_v1.enduser_pk = view_device_custom_fields_v1.value :: int)
                                                ELSE 'not available'
                                                END)
                                    ELSE view_device_custom_fields_v1.value
                                    END) as value
                from view_device_custom_fields_v1) custom_field
                on view_device_v1.device_pk = custom_field.device_fk
            """

        return self.get_doql_json(custom_field_query)


    def get_external_links(self):
        external_links_query = """
                select
                view_device_v1.device_pk,
                view_device_v1.name as device_name,
                external_links.device_url,
                external_links.device_url_notes
                from view_device_v1
                inner join (select device_fk, device_url, notes as device_url_notes from view_deviceurl_v1) external_links
                on view_device_v1.device_pk=external_links.device_fk
            """
        return self.get_doql_json(external_links_query)


    def get_hdd_details(self):
        hdd_details_query = """
        select
        view_device_v1.device_pk,
        view_device_v1.name as device_name,
        hdd_details.raid_group,
        hdd_details.hdd_serial_no,
        hdd_details.hdd_raid_type,
        hdd.hdd_description,
        hdd.partno,
        hdd.rpm as hdd_rpm,
        hdd.rpm_id as hdd_rpm_id,
        hdd.notes as hdd_notes,
        hdd.hdd_bytes,
        hdd.location as hdd_location,
        hdd.hdd_id,
        hdd.manufactuerer_id,
        hdd.hdd_type_id,
        hdd.hdd_type_name,
        hdd.size,
        hdd_details.part_id,
        hdd_details.hddcount,
        hdd_details.description
        from view_device_v1
        inner join (select device_fk, raid_group, serial_no as hdd_serial_no, raid_type_name as hdd_raid_type, part_pk as part_id, partmodel_fk as partmodel_id, pcount as hddcount, description from view_part_v1) hdd_details
        on view_device_v1.device_pk = hdd_details.device_fk
        inner join (select description as hdd_description, partno, hdrpm_name as rpm, hdrpm_id as rpm_id, notes, hdsize_unit as hdd_bytes, location, partmodel_pk as hdd_id, vendor_fk as manufactuerer_id, hddtype_id as hdd_type_id, hddtype_name as hdd_type_name, hdsize as size from view_partmodel_v1) hdd
        on hdd_details.partmodel_id = hdd.hdd_id
        """

        return self.get_doql_json(hdd_details_query)


    def get_ip_addresses(self):
        ip_address_query = """
            select
            view_device_v1.device_pk,
            view_device_v1.name,
            ip_address.subnet_fk as subnet_id,
            ip_address.ip_address as ip,
            ip_address.label,
            ip_address.type,
            subnet.name as subnet
            from view_device_v1
            left join (select device_fk, subnet_fk, ip_address, label, type from view_ipaddress_v1) ip_address
            on ip_address.device_fk = view_device_v1.device_pk
            inner join (select subnet_pk, name from view_subnet_v1) subnet
            on ip_address.subnet_fk = subnet.subnet_pk
        """
        return self.get_doql_json(ip_address_query)

    def get_mac_addresses(self):
        mac_addresses_query = """
            select
            view_device_v1.device_pk,
            view_device_v1.name as device_name,
            mac_address.hw_address as mac,
            mac_address.port_name,
            mac_address.port,
            vlan.name as vlan
            from view_device_v1
            inner join (select device_fk, (
                CASE
                    WHEN length(TRIM(hwaddress)) = 12
                        THEN CONCAT_WS(':',left(TRIM(view_netport_v1.hwaddress),2), substring(TRIM(view_netport_v1.hwaddress),3,2), substring(TRIM(view_netport_v1.hwaddress),5,2), substring(TRIM(view_netport_v1.hwaddress),7,2), substring(TRIM(view_netport_v1.hwaddress),9,2), right(TRIM(view_netport_v1.hwaddress),2))
                        ELSE
                            hwaddress
                        END
                )
                as hw_address, name as port_name, port, primary_vlan_fk from view_netport_v1) mac_address
            ON view_device_v1.device_pk = mac_address.device_fk
            full join (select vlan_pk, name from view_vlan_v1) vlan
            ON vlan.vlan_pk = mac_address.primary_vlan_fk
        """

        return self.get_doql_json(mac_addresses_query)


    def get_device_entitlements(self):
        # todo change parse method so it doesnt fail on non valid mac addresses, did this for FS mapping query
        device_entitlements_query = """
            Select
            view_device_v1.device_pk,
            view_device_v1.name as device_name,
            line_items.purchase_fk as purhase_id,
            line_items.start_date as line_start_date,
            line_items.line_no,
            line_items.renew_date as line_renew_date,
            line_items.notes as line_notes,
            line_items.quantity as line_quantity,
            line_items.frequency as line_frequency,
            line_items.cost as line_cost,
            line_items.cancel_policy as line_cancel_policy,
            line_items.item_type as line_item_type,
            purchase.order_no as purchase_order_no,
            line_items.line_type as line_type,
            line_items.service_type_name as line_service_type,
            line_items.end_date as line_end_date,
            line_items.contract_type_name as line_contract_type
            from view_device_v1
            inner join (select device_fk, purchaselineitem_fk from view_purchaselineitems_to_devices_v1) purchase_lineitem
                on view_device_v1.device_pk=purchase_lineitem.device_fk
            inner join (select purchaselineitem_pk,
                               purchase_fk,
                               start_date,
                               line_no,
                               renew_date,
                               notes,
                               quantity,
                               frequency,
                               cost,
                               cancel_policy,
                               item_type,
                               line_type,
                               service_type_name,
                               end_date,
                               contract_type_name
                        from view_purchaselineitem_v1) line_items
            on line_items.purchaselineitem_pk = purchase_lineitem.purchaselineitem_fk
            inner join (select purchase_pk, order_no from view_purchase_v1) purchase
            on purchase.purchase_pk = line_items.purchase_fk
        """

        return self.get_doql_json(device_entitlements_query)

