import certifi
from unittest import TestCase
from . import FileTestCase
from es_client.builder import Builder
from es_client.exceptions import ConfigurationError, MissingArgument
from mock import Mock, patch

DEFAULT = {
    'elasticsearch': {
        'client': {
            'hosts': ['http://127.0.0.1:9200']
        }
    }
}

class TestInit(TestCase):
    def test_non_dict_passed(self):
        self.assertRaises(ConfigurationError, Builder, 'string', autoconnect=False)
    def test_assign_defaults(self):
        obj = Builder({}, autoconnect=False)
        self.assertEqual(obj.client_args['hosts'], ['http://127.0.0.1:9200'])
    def test_raises_for_both_hosts_and_cloud_id(self):
        test = {
            'elasticsearch': {
                'client': {
                    'hosts': ['http://127.0.0.2:9200'],
                    'cloud_id': 'foo:bar'
                }
            }
        }
        self.assertRaises(ConfigurationError, Builder, test, autoconnect=False)
    def test_remove_default_hosts_when_cloud_id(self):
        test = {
            'elasticsearch': {
                'client': {
                    'hosts': ['http://127.0.0.1:9200'],
                    'cloud_id': 'foo:bar'
                }
            }
        }
        obj = Builder(test, autoconnect=False)
        self.assertRaises(KeyError, lambda: obj.client_args['hosts'])
class TestAuth(TestCase):
    def test_user_but_no_pass(self):
        obj = Builder(DEFAULT, autoconnect=False)
        obj.other_args['username'] = 'test'
        self.assertRaises(ConfigurationError, obj._check_basic_auth)
    def test_pass_but_no_user(self):
        obj = Builder(DEFAULT, autoconnect=False)
        obj.client_args['hosts'] = ['http://127.0.0.1:9200']
        obj.other_args['password'] = 'test'
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
        self.assertRaises(ConfigurationError, Builder, test, autoconnect=False)
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
        self.assertRaises(ConfigurationError, Builder, test, autoconnect=False)
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
        obj = Builder(test, autoconnect=False)
        self.assertEqual(obj.client_args['api_key'], (id, api_key))
    def test_basic_auth_tuple(self):
        u = 'username'
        p = 'password'
        obj = Builder(DEFAULT, autoconnect=False)
        obj.other_args[u] = u
        obj.other_args[p] = p
        obj._check_basic_auth()
        self.assertFalse(u in obj.client_args)
        self.assertFalse(p in obj.client_args)
        self.assertEqual((u, p), obj.client_args['basic_auth'])

class TestCheckSSL(TestCase):
    def test_certifi(self):
        https = DEFAULT
        https['elasticsearch']['client']['hosts'] = 'https://127.0.0.1:9200'
        obj = Builder(https, autoconnect=False)
        obj._check_ssl()
        self.assertEqual(certifi.where(), obj.client_args['ca_certs'])
