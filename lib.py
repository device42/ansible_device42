import requests
import codecs
import base64   
import os
try:
    import json
except ImportError:
    import simplejson as json

available_groups = ['tag', 'buildings', 'customer', 'service_level']


class Logger:

    def __init__(self, conf):
        self.conf = conf
        self.logfile = self.conf.LOGFILE
        self.stdout = self.conf.STDOUT
        self.check_log_file()

    def check_log_file(self):
        while 1:
            if os.path.exists(self.logfile):
                reply = raw_input("[!] Log file already exists. Overwrite or append [O|A]? ")
                if reply.lower().strip() == 'o':
                    with open(self.logfile, 'w'):
                        pass
                    break
                elif reply.lower().strip() == 'a':
                    break
            else:
                break
        if self.conf.DEBUG and os.path.exists(self.conf.DEBUG_LOG):
            with open(self.conf.DEBUG_LOG, 'w'):
                pass

    def writer(self, msg):
        if self.conf.LOGFILE and self.conf.LOGFILE != '':
            with codecs.open(self.logfile, 'a', encoding='utf-8') as f:
                msg = msg.decode('UTF-8', 'ignore')
                f.write(msg + '\r\n')  # \r\n for notepad
        if self.stdout:
            try:
                print msg
            except:
                print msg.encode('ascii', 'ignore') + ' # < non-ASCII chars detected! >'

    def debugger(self, msg):
        if self.conf.DEBUG_LOG and self.conf.DEBUG_LOG != '':
            with codecs.open(self.conf.DEBUG_LOG, 'a', encoding='utf-8') as f:
                title, message = msg
                row = '\n-----------------------------------------------------\n%s\n%s' % (title, message)
                f.write(row + '\r\n\r\n')  # \r\n for notepad


class REST:

    def __init__(self, conf, logger=None):
        self.conf = conf
        self.logger = logger
        self.password = self.conf.D42_PWD
        self.username = self.conf.D42_USER
        self.base_url = self.conf.D42_URL

    def fetcher(self, url):
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(self.username + ':' + self.password),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        offset = 0
        more_pages = True
        devices = []
        while more_pages:
            r = requests.get(url + "&offset={0}".format(offset), headers=headers, verify=False)
            response = r.json()
            devices = devices + response['Devices']
            if offset + response['limit'] < response['total_count']:
                offset += response['limit']
            else:
                more_pages = False
        return devices

    def get_devices(self):
        url = self.base_url + '/api/1.0/devices/all/?include_cols=name,tags,buildings,customer,service_level&limit=1000'
        msg = '\r\nGetting data from %s ' % url
        if self.logger:
            self.logger.writer(msg)
        return self.fetcher(url)


class Ansible:

    def __init__(self, conf, logger=None):
        self.conf = conf

    def check_group(self, group):
        if group == '' and self.conf.EMPTY_TO_NONE is True:
            return 'none'
        elif group == '' and self.conf.EMPTY_TO_NONE is False:
            return False
        else:
            return group.lower().replace(' ', '_')

    def get_grouping(self, devices):

        groups = {}

        for device in devices:

            if self.conf.GROUP_BY == 'tag':
                for tag in device['tags']:
                    group_name = tag
                    groups.setdefault(group_name, {}).setdefault('hosts', []).append(device['name'])
                if len(device['tags']) == 0 and self.conf.EMPTY_TO_NONE is True:
                    groups.setdefault('None', []).append(device['name'])
            else:
                group_name = str(device[self.conf.GROUP_BY])
                group_name = self.check_group(group_name)
                if group_name is False:
                    continue
                groups.setdefault(group_name, []).append(device['name'])
                if device['name'] not in groups[group_name]:
                    groups[group_name].append(device['name'])

        return groups

    @staticmethod
    def write_inventory_file(groups):

        f = open("hosts", "w")

        for group in groups:
            f.write('[' + group + ']\n')
            for device in groups[group]:
                f.write(device.encode('ascii', 'replace') + '\n')
            f.write('\n')

        f.close()

        return True
