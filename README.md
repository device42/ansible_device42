[Device42](http://www.device42.com/) is a Continuous Discovery software for your IT Infrastructure. It helps you automatically maintain an up-to-date inventory of your physical, virtual, and cloud servers and containers, network components, software/services/applications, and their inter-relationships and inter-dependencies.

This repository has 2 different scripts that you can use with ansible.
1. `d42_ansible_inventory_hostfile.py` can be used to create a static inventory file for ansible. You can group hosts by tags, customers, building or service level from Device42 data.
2. `d42_ansible_dynamic_inventory.py` can be used to dynamically by ansible to get hosts from Device42 based on certain filters.

## Assumptions
-----------------------------
    * This script works with Device42 12.0.0 and above

### Requirements
-----------------------------
    * python 2.7.x
    * requests (you can install it with pip install requests or apt-get install python-requests)

### Usage
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



### Compatibility
-----------------------------
    * Script runs on Linux and Windows
