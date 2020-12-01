[Device42](http://www.device42.com/) is a Continuous Discovery software for your IT Infrastructure. It helps you automatically maintain an up-to-date inventory of your physical, virtual, and cloud servers and containers, network components, software/services/applications, and their inter-relationships and inter-dependencies.

This Ansible Collection contains the inventory and lookup plugins for Device42. 
1. Inventory (device42.d42.d42) - can be used to dynamically generate Ansible inventory from Device42 devices.
2. Lookup (device42.d42.d42)- This lookup plugin allows a playbook to fetch passwords or ip addresses for hosts from Device42.
3. Lookup (device42.d42.d42_prompt) - This lookup plugin allows a playbook to fetch passwords or ip addresses for hosts from Device42 with prompt. 

In the `contrib` directory you will find the legacy inventory scripts. Please favor the plugin over the legacy scripts:
1. `contrib\inventory\d42_ansible_inventory_hostfile.py` can be used to create a static inventory file for ansible. You can group hosts by tags, customers, building or service level from Device42 data.
2. `contrib\inventory\d42_ansible_dynamic_inventory.py` can be used to dynamically by ansible to get hosts from Device42 based on certain filters.

-----------------------------
### Requirements
- ansible 2.9+
- python 3.6.x+
- Device42 16.12.00+
- requests (you can install it with pip install requests or apt-get install python-requests)
- Ansible must have an available connection to your Device42 instance in order to collect devices for inventory

### Installation Methods

#### Galaxy 
```bash
ansible-galaxy collection install device42.d42
```

#### Automation Hub
To consume content from hub as part of your automation workflows the content can also be accessed via CLI. 
For this an offline token is required which can be obtained via the web UI at [automation hub](https://cloud.redhat.com/ansible/automation-hub/token), 
and needs to be added to the configuration file as follows:

```bash
[galaxy]
server_list = automation_hub, galaxy

[galaxy_server.automation_hub]
url=https://cloud.redhat.com/api/automation-hub/
auth_url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
token=AABBccddeeff112233gghh...

[galaxy_server.galaxy]
url=https://galaxy.ansible.com/
```

Once configured the collection can be installed by running the following command
```bash
$ ansible-galaxy collection install device42.d42
```

#### Ansible Tower:
* Create a collections requirement file in the SCM 
```bash
touch requirements.yml
```

* add the following to your file and save it
```bash
collections:
- name: device42.d42
version: 1.1.2
source: https://galaxy.ansible.com/

* Install the Ansible collection by running command
```bash
ansible-galaxy collection install -r requirements.yml -p <job tmp location>
```
Starting with Ansible Tower 3.6, the project folder will be copied for each job run. This allows playbooks to make 
local changes to the source tree for convenience, such as creating temporary files, 
without the possibility of interference with other jobs.

* Set the following environmental variables (optional)
```
D42_USER = 'device42 user'
D42_PWD = 'device42 password'
D42_URL = 'https:// device42 server IP address'
D42_SKIP_SSL_CHECK = False
D42_CLEAN_DEVICE_NAME = False
```

For more information on installing collections please follow documentation here https://docs.ansible.com/ansible/latest/user_guide/collections_using.html

-----------------------------
## Inventory Plugin

### Configuration
Define an inventory file (`*.d42.yml`) 

View documentation using `ansible-doc -t inventory device42.d42.d42`

Environmental variables not defined:
```
plugin: device42.d42.d42
url: https://10.10.10.10
username: admin
password: password
ssl_check: False
debug: False
clean_device_name: False
keyed_groups:
    - key: d42_service_level
      prefix: ''
      separator: ''
```

Environmental variables defined:
```
plugin: device42.d42.d42
keyed_groups:
    - key: d42_service_level
      prefix: ''
      separator: ''
```
See [Ansible documentation](https://docs.ansible.com/ansible/latest/plugins/inventory/constructed.html) for more constructed examples.

### How to run
from the directory of your newly created file run the following command.

```bash
ansible-inventory -i *.d42.yml --graph
```

-----------------------------
## Lookup Plugin

### Configuration

If using environmental variables skip this step, if not create a d42.py or d42_prompt.py in ansible/lib/ansible/plugins/lookup/
with the following information
```
D42_USER = 'device42 user'
D42_PWD = 'device42 password'
D42_URL = 'https:// device42 server IP address'
D42_SKIP_SSL_CHECK = False
D42_DEBUG = False
D42_CLEAN
```

### How to run
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

The following was tested in a playbook using the included example template `example_playbook.yaml`
playbooks can be run by using the following command

```bash
ansible-playbook *.yaml -f 10
```
## Legacy Inventory Usage
-----------------------------

### Requirements
- ansible 2.9+
- python 3.6.x+ or python 2.7.x
- Device42 16.12.00+
- requests (you can install it with pip install requests or apt-get install python-requests)
- Ansible must have an available connection to your Device42 instance in order to collect devices for inventory

    * rename conf.sample.ini to conf.ini
    * in conf add D42 URL/credentials ( also instead of conf file, possible to use environment variables )
```
# ====== Device42 upload settings =========
[DEFAULT]
D42_USER = admin
D42_PWD = adm!nd42
D42_URL = https://10.10.10.10
D42_SKIP_SSL_CHECK = True
D42_DEBUG = FALSE

# ====== Ansible settings =========
[DOQL]
GROUP_BY_QUERY = select name, service_level from view_device_v1
GROUP_BY_FIELD = service_level
GROUP_BY_REFERENCE_FIELD = name
SPLIT_GROUP_BY_COMMA = False
```

Navigate to the root folder of the script `.../ansible_device42`

Run the `python -m contrib.inventory.d42_ansible_inventory_hostfile` and enjoy!

Also you may use automatic version with Ansible commands ex.

ping :

`ansible all -i d42_ansible_dynamic_inventory.py -m ping`

copy ssh file :

`ansible all -i d42_ansible_dynamic_inventory.py -m authorized_key -a "user=root key='ssh-rsa AAAA...XXX == root@hostname'"`

modify file :

`ansible all -i d42_ansible_dynamic_inventory.py -m lineinfile -a "dest=/etc/group regexp='^(users:x:100:)(.*)' line='\1ldapusername,\2' state=present backrefs=yes"`



and much more! [Please read Ansible docs.](https://ansible-tips-and-tricks.readthedocs.io/en/latest/ansible/commands/)

If you have any questions - feel free to reach out to us at support at device42.com


