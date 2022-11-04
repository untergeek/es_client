import certifi
from unittest import TestCase
from es_client.builder import Builder
from es_client.exceptions import ConfigurationError, MissingArgument
from mock import Mock, patch
from . import FileTestObj

DEFAULT = {
    'elasticsearch': {
        'client': {
            'hosts': ['http://127.0.0.1:9200']
        }
    }
}

YAMLCONFIG = ('---\n'
'elasticsearch:\n'
'  client:\n'
'    hosts:\n'
'      - {0}\n')

class TestInit(TestCase):
    def test_non_dict_passed(self):
        self.assertRaises(ConfigurationError, Builder, configdict='string')
    def test_read_config_file_old(self):
        es_url = 'http://127.0.0.1:9200'
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args['configfile'], YAMLCONFIG.format(es_url))
        # Test
        build_obj = Builder(configfile=file_obj.args['configfile'])
        assert build_obj.client_args.hosts[0] == es_url
        # Teardown
        file_obj.teardown()
    def test_assign_defaults(self):
        obj = Builder(configdict={})
        self.assertEqual(obj.client_args.hosts, None)
    def test_raises_for_both_hosts_and_cloud_id(self):
        test = {
            'elasticsearch': {
                'client': {
                    'hosts': ['http://10.1.2.3:4567'],
                    'cloud_id': 'foo:bar'
                }
            }
        }
        self.assertRaises(ConfigurationError, Builder, configdict=test)
    def test_remove_default_hosts_when_cloud_id(self):
        test = {
            'elasticsearch': {
                'client': {
                    'hosts': ['http://127.0.0.1:9200'],
                    'cloud_id': 'foo:bar'
                }
            }
        }
        obj = Builder(configdict=test)
        self.assertEqual(None, obj.client_args.hosts)
class TestAuth(TestCase):
    def test_user_but_no_pass(self):
        obj = Builder(configdict=DEFAULT)
        obj.other_args.username = 'test'
        self.assertRaises(ConfigurationError, obj._check_basic_auth)
    def test_pass_but_no_user(self):
        obj = Builder(configdict=DEFAULT)
        obj.client_args.hosts = ['http://127.0.0.1:9200']
        obj.other_args.password = 'test'
        self.assertRaises(ConfigurationError, obj._check_basic_auth)
    def test_id_but_no_api_key(self):
        test = {
            'elasticsearch': {
                'other_settings': {
                    'api_key': {
                        'id': 'test'
                    }
                },
                'client': {'hosts': ['http://127.0.0.1:9200']}}
        }
        self.assertRaises(ConfigurationError, Builder, configdict=test)
    def test_api_key_but_no_id(self):
        test = {
            'elasticsearch': {
                'other_settings': {
                    'api_key': {
                        'api_key': 'test'
                    }
                },
                'client': {'hosts': ['http://127.0.0.1:9200']}}
        }
        self.assertRaises(ConfigurationError, Builder, configdict=test)
    def test_proper_api_key(self):
        id = 'foo'
        api_key = 'bar'
        test = {
            'elasticsearch': {
                'other_settings': {
                    'api_key': {
                        'id': id,
                        'api_key': api_key
                    }
                },
                'client': {'hosts': ['http://127.0.0.1:9200']}}
        }
        obj = Builder(configdict=test)
        self.assertEqual(obj.client_args.api_key, (id, api_key))
    def test_basic_auth_tuple(self):
        u = 'username'
        p = 'password'
        obj = Builder(configdict=DEFAULT)
        obj.other_args.username = u
        obj.other_args.password = p
        obj._check_basic_auth()
        self.assertFalse(u in obj.client_args.asdict())
        self.assertFalse(p in obj.client_args.asdict())
        self.assertEqual((u, p), obj.client_args.basic_auth)

class TestCheckSSL(TestCase):
    def test_certifi(self):
        https = DEFAULT
        https['elasticsearch']['client']['hosts'] = 'https://127.0.0.1:9200'
        obj = Builder(configdict=https)
        obj._check_ssl()
        self.assertEqual(certifi.where(), obj.client_args.ca_certs)
