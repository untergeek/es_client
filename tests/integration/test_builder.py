import os
from unittest import TestCase
from ..unit import FileTestCase
from es_client.builder import Builder
from es_client.exceptions import ConfigurationError, ESClientException, NotMaster

host, port = os.environ.get('TEST_ES_SERVER', 'localhost:9200').split(':')
port = int(port) if port else 9200

config = {
    'elasticsearch': {
        'client': {
            'hosts': host,
            'port': port,
        }
    }
}

class TestCheckMaster(TestCase):
    def test_multiple_hosts_raises(self):
        local_conf = {'elasticsearch':{'client':{'hosts':['127.0.0.1','localhost']}}}
        local_conf['elasticsearch']['master_only'] = True
        obj = Builder(local_conf, autoconnect=False)
        obj._get_client()
        self.assertRaises(ConfigurationError, obj._check_master)
    def test_exit_if_not_master(self):
        obj = Builder(config, autoconnect=False)
        obj.master_only = True
        obj.is_master = False
        obj._get_client()
        self.assertRaises(NotMaster, obj._check_master)

class TestCheckVersion(TestCase):
    def test_skip_version_check(self):
        obj = Builder(config, autoconnect=False, version_min=(98,98,98), version_max=(99,99,99))
        obj.skip_version_test = True
        obj._get_client()
        self.assertIsNone(obj._check_version())
    def test_bad_version_raises(self):
        obj = Builder(config, autoconnect=False, version_min=(98,98,98), version_max=(99,99,99))
        obj._get_client()
        self.assertRaises(ESClientException, obj._check_version)

class TestConnection(TestCase):
    def test_client_info(self):
        obj = Builder(config)
        client = obj.client
        expected = client.info()
        self.assertEqual(expected, obj.test_connection())        

