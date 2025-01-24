"""Test the Builder class"""

from unittest import TestCase
import pytest
from es_client.builder import Builder
from es_client.exceptions import ConfigurationError, ESClientException, NotMaster
from . import CACRT, HOST, PASS, USER

config = {
    "elasticsearch": {
        "other_settings": {"username": USER, "password": PASS},
        "client": {"hosts": HOST, "ca_certs": CACRT},
    }
}

# pylint: disable=protected-access


class TestCheckMaster(TestCase):
    """Test 'check master' functionality"""

    def test_multiple_hosts_raises(self):
        """Raise exception if multiple hosts are specified and 'master_only' is True"""
        local_conf = {
            "elasticsearch": {
                "other_settings": {
                    "master_only": True,
                    "username": USER,
                    "password": PASS,
                },
                "client": {
                    "hosts": [HOST],
                    "ca_certs": CACRT,
                },
            }
        }
        obj = Builder(configdict=local_conf, autoconnect=False)
        obj._get_client()
        # Cheating in an extra HOST here
        obj.client_args.hosts.append(HOST)
        with pytest.raises(ConfigurationError):
            obj._check_multiple_hosts()

    def test_exit_if_not_master(self):
        """Raise NotMaster if node is not master"""
        obj = Builder(config, autoconnect=False)
        obj.master_only = True
        obj._get_client()
        obj._find_master()
        # Cheating in a False result for is_master
        obj.is_master = False
        with pytest.raises(NotMaster):
            obj._check_if_master()


class TestCheckVersion(TestCase):
    """Check ES version"""

    def test_skip_version_check(self):
        """Skip version check results in None being returned"""
        obj = Builder(configdict=config, autoconnect=False)
        obj.skip_version_test = True
        obj._get_client()
        assert obj._check_version() is None

    def test_bad_version_raises(self):
        """Raise ESClientException if version is out of bounds"""
        obj = Builder(configdict=config, autoconnect=False)
        obj.version_min = (98, 98, 98)
        obj.version_max = (99, 99, 99)
        obj._get_client()
        with pytest.raises(ESClientException):
            obj._check_version()


class TestConnection(TestCase):
    """Test client connection"""

    def test_incomplete_dict_passed(self):
        """Sending a proper dictionary but None value for hosts will raise ValueError"""
        cfg = {"elasticsearch": {"client": {"hosts": None}}}
        with pytest.raises(ValueError):
            Builder(configdict=cfg, autoconnect=True)

    def test_client_info(self):
        """Proper connection to client makes for a good response"""
        obj = Builder(configdict=config, autoconnect=True)
        client = obj.client
        expected = dict(client.info())
        assert expected['cluster_name'] == dict(obj.test_connection())['cluster_name']
