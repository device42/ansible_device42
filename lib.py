from StringIO import StringIO
import requests
import codecs
import base64
import imp
import csv
import sys
import os
try:
    import json
except ImportError:
    import simplejson as json

def get_conf():
    try:
        conf = imp.load_source('conf', 'conf').__dict__
        if conf['D42_SKIP_SSL_CHECK'] == True:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    except:
        if 'D42_SKIP_SSL_CHECK' in os.environ and os.environ['D42_SKIP_SSL_CHECK'] == 'True':
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        if 'D42_URL' not in os.environ:
            print 'Please set D42_URL environ.'
            sys.exit()

        if 'D42_USER' not in os.environ:
            print 'Please set D42_USER environ.'
            sys.exit()

        if 'D42_PWD' not in os.environ:
            print 'Please set D42_PWD environ.'
            sys.exit()

        if 'GROUP_BY_QUERY' not in os.environ:
            print 'Please set GROUP_BY_QUERY environ.'
            sys.exit()

        if 'GROUP_BY_FIELD' not in os.environ:
            print 'Please set GROUP_BY_FIELD environ.'
            sys.exit()

        if 'GROUP_BY_REFERENCE_FIELD' not in os.environ:
            print 'Please set GROUP_BY_REFERENCE_FIELD environ.'
            sys.exit()

        conf = {
            'D42_URL': os.environ['D42_URL'],
            'D42_USER': os.environ['D42_USER'],
            'D42_PWD': os.environ['D42_PWD'],
            'GROUP_BY_QUERY': os.environ['GROUP_BY_QUERY'],
            'GROUP_BY_FIELD': os.environ['GROUP_BY_FIELD'],
            'GROUP_BY_REFERENCE_FIELD': os.environ['GROUP_BY_REFERENCE_FIELD']
        }
    return conf

class Device42:

    def __init__(self, conf):
        self.conf = conf
        self.password = self.conf['D42_PWD']
        self.username = self.conf['D42_USER']
        self.base_url = self.conf['D42_URL']
        self.query = self.conf['GROUP_BY_QUERY']

    def fetcher(self, url, query):
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(self.username + ':' + self.password),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        r = requests.post(url, data={
            'query': query,
            'header': 'yes'
        }, headers=headers, verify=False)
        return r.text

    def doql(self):
        url = self.base_url + '/services/data/v1.0/query/'
        return self.get_list_from_csv(self.fetcher(url, self.query))

    @staticmethod
    def get_list_from_csv(text):
        f = StringIO(text.decode("utf-8"))
        list_ = []
        dict_reader = csv.DictReader(f, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True, dialect='excel')
        for item in dict_reader:
            list_.append(item)

        return list_


class Ansible:

    def __init__(self, conf):
        self.conf = conf

    def get_grouping(self, objects):
        groups = {}
        for object_ in objects:
            try:
                if object_[self.conf['GROUP_BY_FIELD']] not in groups:
                    groups[object_[self.conf['GROUP_BY_FIELD']]] = []
                groups[object_[self.conf['GROUP_BY_FIELD']]].append(object_[self.conf['GROUP_BY_REFERENCE_FIELD']])
            except Exception as e:
                print object_
                sys.exit()
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
