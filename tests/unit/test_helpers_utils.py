import os, random, string
import pytest
from unittest import TestCase
from . import FileTestObj
from es_client.exceptions import ConfigurationError
from es_client.helpers.utils import ensure_list, get_yaml, prune_nones, read_file, verify_ssl_paths

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
    return ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.digits
        ) for _ in range(size)
    )

class TestEnsureList(TestCase):
    def test_ensure_list_returns_lists(self):
        l = ["a", "b", "c", "d"]
        e = ["a", "b", "c", "d"]
        self.assertEqual(e, ensure_list(l))
        l = "abcd"
        e = ["abcd"]
        self.assertEqual(e, ensure_list(l))
        l = [["abcd","defg"], 1, 2, 3]
        e = [["abcd","defg"], 1, 2, 3]
        self.assertEqual(e, ensure_list(l))
        l = {"a":"b", "c":"d"}
        e = [{"a":"b", "c":"d"}]
        self.assertEqual(e, ensure_list(l))

class TestPruneNones(TestCase):
    def test_prune_nones_with(self):
        self.assertEqual({}, prune_nones({'a':None}))
    def test_prune_nones_without(self):
        a = {'foo':'bar'}
        self.assertEqual(a, prune_nones(a))

class TestReadFile:
    def test_read_file_present(self):
        obj = FileTestObj()
        assert obj.written_value == read_file(obj.args['filename'])
        obj.teardown()
    def test_raise_when_no_file(self):
        obj = FileTestObj()
        with pytest.raises(ConfigurationError):
            read_file(obj.args['no_file_here'])
        obj.teardown()

class TestReadCerts:
    def test_all_as_one(self):
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
    def test_present(self):
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
        obj = FileTestObj()
        evar = random_envvar(8)
        dollar = '${' + evar + '}'
        obj.write_config(obj.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(obj.args['configfile'])
        assert cfg['elasticsearch']['client']['hosts'] is None
        obj.teardown()
    def test_not_present_with_default(self):
        obj = FileTestObj()
        evar = random_envvar(8)
        default = random_envvar(8)
        dollar = '${' + evar + ':' + default + '}'
        obj.write_config(obj.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(obj.args['configfile'])
        assert cfg['elasticsearch']['client']['hosts'] == default
        obj.teardown()
    def test_raises_exception(self):
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
