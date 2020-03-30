[Device42](http://www.device42.com/) is a Continuous Discovery software for your IT Infrastructure. It helps you automatically maintain an up-to-date inventory of your physical, virtual, and cloud servers and containers, network components, software/services/applications, and their inter-relationships and inter-dependencies.

This Ansible Collection contains the inventory and lookup plugins for Device42. 
1. Inventory (device42.d42.d42) - can be used to dynamically generate Ansible inventory from Device42 devices.
2. Lookup (device42.d42.d42)- This lookup plugin allows a playbook to fetch passwords or ip addresses for hosts from Device42.
3. Lookup (device42.d42.d42_prompt) - This lookup plugin allows a playbook to fetch passwords or ip addresses for hosts from Device42 with prompt. 

In the `contrib` directory you will find the legacy inventory scripts. Please favor the plugin over the legacy scripts:
1. `contrib\inventory\d42_ansible_inventory_hostfile.py` can be used to create a static inventory file for ansible. You can group hosts by tags, customers, building or service level from Device42 data.
2. `contrib\inventory\d42_ansible_dynamic_inventory.py` can be used to dynamically by ansible to get hosts from Device42 based on certain filters.

-----------------------------
## Assumptions
- This script works with Device42 12.0.0 and above
### Requirements
- ansible 2.9+
- python 3.6.x+
- requests (you can install it with pip install requests or apt-get install python-requests)

### Installation
#### Ansible Tower:
* Clone the repo on the host of your anisble server
```bash
git clone git@github.com:device42/ansible_device42.git
```
* Navigate to the cloned directory
```bash
cd path/to/directory
```
* Build the Ansible collection
```bash
ansible-galaxy collection build
```
* Install the ansible collection 
```bash
ansible-galaxy collection install device42-d42-2.0.0.tar.gz -p ../.ansible/collections
```

___Change ../.ansible/collections to the directory of your Ansible collections folder___

#### Other: 
For more information on installing collections please follow documentation here https://docs.ansible.com/ansible/latest/user_guide/collections_using.html

-----------------------------
## Inventory Plugin

### Configuration
Define an inventory file (`*.d42.yml`). View documentation using `ansible-doc -t inventory device42.d42.d42`

Example:
```
plugin: device42.d42.d42
instance: https://10.10.10.10
username: admin
password: adm!nd42
keyed_groups:
    - key: d42_service_level
      prefix: ''
      separator: ''
```
See https://docs.ansible.com/ansible/latest/plugins/inventory/constructed.html for more constructed examples.

-----------------------------
## Lookup Plugin

### Configuration

Please set system environment variables if you use ENV version ( d42.py ):
```
D42_USER = 'device42 user'
D42_PWD = 'device42 password'
D42_URL = 'https:// device42 server IP address'
D42_SKIP_SSL_CHECK = False
```

```
* Place d42.py or d42_prompt.py in ansible/lib/ansible/plugins/lookup/
```

### Usage

```
To get password call: lookup('d42', 'device_name', 'password', 'username')
```
device_name and username need to be filled in
```
To run any doql request: lookup('d42', 'SELECT ... FROM ...', 'doql', 'list')
```
doql query need to be filled in + we need to set data type of returned result ( 'string', 'list', 'list_dicts' )
* string - return single string without column headers
* list - return list of string ( we split DOQL result line by line without column headers )
* list_dicts - return list of dicts with column headers

All above works the same for the `prompt` version, we just add 3 more arguments in the yaml file, please check reference in promt example.

## Legacy Inventory Usage
-----------------------------

    * rename conf.sample to conf
    * in conf add D42 URL/credentials ( also instead of conf file, possible to use environment variables )
```
# ====== Device42 upload settings ========= #
D42_USER = 'device42 user'
D42_PWD = 'device42 password'
D42_URL = 'https:// device42 server IP address'
D42_SKIP_SSL_CHECK = True
```

    * in conf add DOQL group settings
```
# ====== Ansible settings ========= #
GROUP_BY_QUERY = 'select name, service_level from view_device_v1' # DOQL QUERY, POSSIBLE TO GROUP BY ANY FIELD
GROUP_BY_FIELD = 'service_level' # GROUP BY FIELD
GROUP_BY_REFERENCE_FIELD = 'name' # FIELD THAT COMES AS REFERENCE NAME
SPLIT_GROUP_BY_COMMA = False
```

Run the `python d42_ansible_inventory_hostfile.py`  and enjoy!

Also you may use automatic version with Ansible commands ex.

ping :

`ansible all -i d42_ansible_dynamic_inventory.py -m ping`

copy ssh file :

`ansible all -i d42_ansible_dynamic_inventory.py -m authorized_key -a "user=root key='ssh-rsa AAAA...XXX == root@hostname'"`

modify file :

`ansible all -i d42_ansible_dynamic_inventory.py -m lineinfile -a "dest=/etc/group regexp='^(users:x:100:)(.*)' line='\1ldapusername,\2' state=present backrefs=yes"`



and much more! [Please read Ansible docs.](https://ansible-tips-and-tricks.readthedocs.io/en/latest/ansible/commands/)

If you have any questions - feel free to reach out to us at support at device42.com


