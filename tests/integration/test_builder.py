"""Test the Builder class"""
# pylint: disable=protected-access
import os
from unittest import TestCase
from es_client.builder import Builder
from es_client.exceptions import ConfigurationError, ESClientException, NotMaster

host = os.environ.get('TEST_ES_SERVER', 'http://127.0.0.1:9200')

config = {
    'elasticsearch': {
        'other_settings': {},
        'client': {
            'hosts': host
        }
    }
}


class TestCheckMaster(TestCase):
    """Test 'check master' functionality"""

    def test_multiple_hosts_raises(self):
        """Raise exception if multiple hosts are specified and 'master_only' is True"""
        local_conf = {
            'elasticsearch': {
                'other_settings': {
                    'master_only': True
                },
                'client': {
                    'hosts': ['http://127.0.0.1:9200', 'http://localhost:9200']
                }
            }
        }
        obj = Builder(configdict=local_conf, autoconnect=False)
        obj._get_client()
        self.assertRaises(ConfigurationError, obj._check_master)

    def test_exit_if_not_master(self):
        """Raise NotMaster if node is not master"""
        obj = Builder(config, autoconnect=False)
        obj.master_only = True
        obj.is_master = False
        obj._get_client()
        self.assertRaises(NotMaster, obj._check_master)


class TestCheckVersion(TestCase):
    """Check ES version"""

    def test_skip_version_check(self):
        """Skip version check results in None being returned"""
        obj = Builder(configdict=config, autoconnect=False)
        obj.skip_version_test = True
        obj._get_client()
        self.assertIsNone(obj._check_version())

    def test_bad_version_raises(self):
        """Raise ESClientException if version is out of bounds"""
        obj = Builder(configdict=config, autoconnect=False)
        obj.version_min = (98, 98, 98)
        obj.version_max = (99, 99, 99)
        obj._get_client()
        self.assertRaises(ESClientException, obj._check_version)


class TestConnection(TestCase):
    """Test client connection"""

    def test_non_dict_passed(self):
        """Ensure that a 'bad' configdict connects using defaults"""
        obj = Builder(configdict='string', autoconnect=True)
        client = obj.client
        expected = client.info()
        self.assertEqual(expected, obj.test_connection())

    def test_incomplete_dict_passed(self):
        """Sending a proper dictionary but None value for hosts will raise ValueError"""
        cfg = {'elasticsearch': {'client': {'hosts': None}}}
        self.assertRaises(ValueError, Builder, configdict=cfg, autoconnect=True)

    def test_client_info(self):
        """Proper connection to client makes for a good response"""
        obj = Builder(configdict=config, autoconnect=True)
        client = obj.client
        expected = client.info()
        self.assertEqual(expected, obj.test_connection())
