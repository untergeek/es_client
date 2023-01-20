"""Test helpers.utils"""
# pylint: disable=protected-access, broad-except, import-error
# add import-error here ^^^ to avoid false-positives for the local import
import os
import random
import string
from unittest import TestCase
import pytest
from mock import Mock
from es_client.exceptions import ConfigurationError
from es_client.helpers.utils import ensure_list, get_yaml, prune_nones, read_file, verify_ssl_paths, verify_url_schema, get_version
from . import FileTestObj

DEFAULT = {
    'elasticsearch': {
        'other_settings': {
            'master_only': False,
            'skip_version_test': False,
            'username': None,
            'password': None
        },
        'client': {
            'hosts': 'http://127.0.0.1:9200',
            'request_timeout': 30,
        }
    }
}

YAML = (
"""
elasticsearch:
  client:
    hosts: {0}
"""
)

def random_envvar(size):
    """Generate a random environment variable"""
    return ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.digits
        ) for _ in range(size)
    )

class TestEnsureList(TestCase):
    """Test the ensure_list function"""
    def test_ensure_list_returns_lists(self):
        """Test several examples of lists: existing lists, strings, mixed lists/numbers, etc."""
        verify = ["a", "b", "c", "d"]
        source = ["a", "b", "c", "d"]
        self.assertEqual(verify, ensure_list(source))
        verify = ["abcd"]
        source = "abcd"
        self.assertEqual(verify, ensure_list(source))
        verify = [["abcd","defg"], 1, 2, 3]
        source = [["abcd","defg"], 1, 2, 3]
        self.assertEqual(verify, ensure_list(source))
        verify = [{"a":"b", "c":"d"}]
        source = {"a":"b", "c":"d"}
        self.assertEqual(verify, ensure_list(source))

class TestPruneNones(TestCase):
    """Test the prune_nones function"""
    def test_prune_nones_with(self):
        """Ensure that a dict with a single None value comes back as an empty dict"""
        self.assertEqual({}, prune_nones({'a':None}))
    def test_prune_nones_without(self):
        """Ensure that a dict with no None values comes back unchanged"""
        testval = {'foo':'bar'}
        self.assertEqual(testval, prune_nones(testval))

class TestReadFile:
    """Test the read_file function"""
    def test_read_file_present(self):
        """Ensure that the written value is what was in the filename"""
        obj = FileTestObj()
        assert obj.written_value == read_file(obj.args['filename'])
        obj.teardown()
    def test_raise_when_no_file(self):
        """Raise an exception when there is no file"""
        obj = FileTestObj()
        with pytest.raises(ConfigurationError):
            read_file(obj.args['no_file_here'])
        obj.teardown()

class TestReadCerts:
    """Test the verify_ssl_paths function"""
    def test_all_as_one(self):
        """Test all 3 possible cert files at once from the same file"""
        obj = FileTestObj()
        config = {
            'ca_certs': obj.args['filename'],
            'client_cert': obj.args['filename'],
            'client_key': obj.args['filename'],
        }
        try:
            verify_ssl_paths(config)
        except Exception:
            pytest.fail("Unexpected Exception...")

class TestEnvVars:
    """Test the ability to read environment variables"""
    def test_present(self):
        """Test an existing (present) envvar"""
        obj = FileTestObj()
        evar = random_envvar(8)
        os.environ[evar] = "1234"
        dollar = '${' + evar + '}'
        obj.write_config(obj.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(obj.args['configfile'])
        assert cfg['elasticsearch']['client']['hosts'] ==  os.environ.get(evar)
        del os.environ[evar]
        obj.teardown()
    def test_not_present(self):
        """Test a non-existent (not-present) envvar. It should set None here"""
        obj = FileTestObj()
        evar = random_envvar(8)
        dollar = '${' + evar + '}'
        obj.write_config(obj.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(obj.args['configfile'])
        assert cfg['elasticsearch']['client']['hosts'] is None
        obj.teardown()
    def test_not_present_with_default(self):
        """Test a non-existent (not-present) envvar. It should set a default value here"""
        obj = FileTestObj()
        evar = random_envvar(8)
        default = random_envvar(8)
        dollar = '${' + evar + ':' + default + '}'
        obj.write_config(obj.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(obj.args['configfile'])
        assert cfg['elasticsearch']['client']['hosts'] == default
        obj.teardown()
    def test_raises_exception(self):
        """Ensure that improper formatting raises a ConfigurationError exception"""
        obj = FileTestObj()
        obj.write_config(obj.args['configfile'],
        """
        [weird brackets go here]
        I'm not a yaml file!!!=I have no keys
        I have lots of spaces
        """)
        with pytest.raises(ConfigurationError):
            get_yaml(obj.args['configfile'])
        obj.teardown()

class TestVerifyURLSchema:
    """Test the verify_url_schema function"""
    def test_full_schema(self):
        """Verify that a proper schema comes back unchanged"""
        url = 'https://127.0.0.1:9200'
        assert verify_url_schema(url) == url
    def test_http_schema_no_port(self):
        """Verify that port 80 is tacked on when no port is specified as a port is required"""
        http_port = '80'
        url = 'http://127.0.0.1'
        assert verify_url_schema(url) == 'http://127.0.0.1' + ':' + http_port
    def test_https_schema_no_port(self):
        """Verify that 443 is tacked on when no port is specified but https is the schema"""
        https_port = '443'
        url = 'https://127.0.0.1'
        assert verify_url_schema(url) == 'https://127.0.0.1' + ':' + https_port
    def test_bad_schema_no_port(self):
        """A URL starting with other than http or https raises an exception w/o port"""
        url = 'abcd://127.0.0.1'
        with pytest.raises(ConfigurationError):
            verify_url_schema(url)
    def test_bad_schema_with_port(self):
        """A URL starting with other than http or https raises an exception w/port"""
        url = 'abcd://127.0.0.1:1234'
        with pytest.raises(ConfigurationError):
            verify_url_schema(url)
    def test_bad_schema_too_many_colons(self):
        """An invalid URL with too many colons raises an exception"""
        url = 'http://127.0.0.1:1234:5678'
        with pytest.raises(ConfigurationError):
            verify_url_schema(url)

class TestGetVersion:
    """Test the get_version function"""
    def test_positive(self):
        """Ensure that what goes in comes back out unchanged"""
        client = Mock()
        client.info.return_value = {'version': {'number': '9.9.9'} }
        version = get_version(client)
        assert version == (9,9,9)
    def test_negative(self):
        """Ensure that mismatches are caught"""
        client = Mock()
        client.info.return_value = {'version': {'number': '9.9.9'} }
        version = get_version(client)
        assert version != (8,8,8)
    def test_dev_version_4_dots(self):
        """Test that anything after a third value and a period is truncated"""
        client = Mock()
        client.info.return_value = {'version': {'number': '9.9.9.dev'} }
        version = get_version(client)
        assert version == (9,9,9)
    def test_dev_version_with_dash(self):
        """Test that anything after a third value and a dash is truncated"""
        client = Mock()
        client.info.return_value = {'version': {'number': '9.9.9-dev'} }
        version = get_version(client)
        assert version == (9,9,9)