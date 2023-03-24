"""Test helpers.schemacheck"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
from unittest import TestCase
import certifi
import pytest
from es_client.builder import Builder
from es_client.exceptions import ConfigurationError
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
    """Test initializing a Builder object"""
    def test_read_config_file_old(self):
        """Ensure that the value of es_url is passed to hosts"""
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
        """Ensure that the default URL is passed to hosts when an empty config dict is passed"""
        obj = Builder(configdict={})
        self.assertEqual(obj.client_args.hosts, ['http://127.0.0.1:9200'])
    def test_raises_for_both_hosts_and_cloud_id(self):
        """Ensure that ConfigurationError is Raised when both hosts and cloud_id are passed"""
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
        """Ensure that only a default hosts url is removed when cloud_id is also passed"""
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
    def test_url_schema_validation_fix(self):
        """Ensure that :443 is appended to a host with https and no port"""
        test = {
            'elasticsearch': {
                'client': {
                    'hosts': ['https://127.0.0.1']
                }
            }
        }
        obj = Builder(configdict=test)
        assert 'https://127.0.0.1:443' == obj.client_args.hosts[0]
    def test_url_schema_validation_raises(self):
        """Ensure that ConfigurationError is raised with an invalid host URL schema"""
        test = {
            'elasticsearch': {
                'client': {
                    'hosts': ['127.0.0.1:9200']
                }
            }
        }
        with pytest.raises(ConfigurationError):
            _ = Builder(configdict=test)


class TestAuth(TestCase):
    """Test authentication methods"""
    def test_user_but_no_pass(self):
        """Ensure ConfigurationError is Raised when username is provided but no password"""
        obj = Builder(configdict=DEFAULT)
        obj.other_args.username = 'test'
        self.assertRaises(ConfigurationError, obj._check_basic_auth)
    def test_pass_but_no_user(self):
        """Ensure ConfigurationError is Raised when password is provided but no username"""
        obj = Builder(configdict=DEFAULT)
        obj.client_args.hosts = ['http://127.0.0.1:9200']
        obj.other_args.password = 'test'
        self.assertRaises(ConfigurationError, obj._check_basic_auth)
    def test_id_but_no_api_key(self):
        """Ensure ConfigurationError is Raised when id is passed but no api_key"""
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
        """Ensure ConfigurationError is Raised when api_key is passed but no id"""
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
        """Ensure that API key value is assigned to client_args when a properly passed"""
        api_id = 'foo'
        api_key = 'bar'
        test = {
            'elasticsearch': {
                'other_settings': {
                    'api_key': {
                        'id': api_id,
                        'api_key': api_key
                    }
                },
                'client': {'hosts': ['http://127.0.0.1:9200']}}
        }
        obj = Builder(configdict=test)
        self.assertEqual(obj.client_args.api_key, (api_id, api_key))
    def test_basic_auth_tuple(self):
        """Test basic_auth is set properly"""
        usr = 'username'
        pwd = 'password'
        obj = Builder(configdict=DEFAULT)
        obj.other_args.username = usr
        obj.other_args.password = pwd
        obj._check_basic_auth()
        self.assertFalse(usr in obj.client_args.asdict())
        self.assertFalse(pwd in obj.client_args.asdict())
        self.assertEqual((usr, pwd), obj.client_args.basic_auth)

class TestCheckSSL(TestCase):
    """Ensure that certifi certificates are picked up"""
    def test_certifi(self):
        """Ensure that the certifi.where() output matches what was inserted into client_args"""
        https = DEFAULT
        https['elasticsearch']['client']['hosts'] = 'https://127.0.0.1:9200'
        obj = Builder(configdict=https)
        obj._check_ssl()
        self.assertEqual(certifi.where(), obj.client_args.ca_certs)
    def test_ca_certs_named_but_no_file(self):
        """Ensure that a ConfigurationError is raised if ca_certs is named but no file found"""
        tmp = FileTestObj()
        tmp.write_config(tmp.args['configfile'],
        """
        This file will be deleted
        """)
        tmp.teardown()
        https = {
            'elasticsearch': {
                'client': {
                    'hosts': ['http://127.0.0.1:9200'],
                    'ca_certs': tmp.args['configfile']
                }
            }
        }
        https['elasticsearch']['client']['hosts'] = 'https://127.0.0.1:9200'
        with pytest.raises(ConfigurationError):
            Builder(configdict=https)
