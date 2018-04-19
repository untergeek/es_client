import os, random, string
from unittest import TestCase
from . import FileTestCase
from es_client.exceptions import ConfigurationError
from es_client.helpers.utils import ensure_list, get_yaml, prune_nones, read_file, verify_ssl_paths

DEFAULT = {
    'elasticsearch': {
        'aws': {
            'sign_requests': False
        },
        'client': {
            'hosts': '127.0.0.1',
            'password': None,
            'port': 9200,
            'timeout': 30,
            'use_ssl': False,
            'username': None,
            'verify_certs': False
        },
        'master_only': False,
        'skip_version_test': False
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

class TestReadFile(FileTestCase):
    def test_read_file_present(self):
        self.assertEqual(self.written_value, read_file(self.args['filename']))
    def test_raise_when_no_file(self):
        self.assertRaises(ConfigurationError, read_file, self.args['no_file_here'])

class TestReadCerts(FileTestCase):
    def test_all_as_one(self):
        config = {
            'ca_certs': self.args['filename'],
            'client_cert': self.args['filename'],
            'client_key': self.args['filename'],
        }
        self.assertIsNone(verify_ssl_paths(config))

class TestEnvVars(FileTestCase):
    def test_present(self):
        evar = random_envvar(8)
        os.environ[evar] = "1234"
        dollar = '${' + evar + '}'
        self.write_config(self.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(self.args['configfile'])
        self.assertEqual(cfg['elasticsearch']['client']['hosts'], os.environ.get(evar))
        del os.environ[evar]
    def test_not_present(self):
        evar = random_envvar(8)
        dollar = '${' + evar + '}'
        self.write_config(self.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(self.args['configfile'])
        self.assertIsNone(cfg['elasticsearch']['client']['hosts'])
    def test_not_present_with_default(self):
        evar = random_envvar(8)
        default = random_envvar(8)
        dollar = '${' + evar + ':' + default + '}'
        self.write_config(self.args['configfile'], YAML.format(dollar))
        cfg = get_yaml(self.args['configfile'])
        self.assertEqual(cfg['elasticsearch']['client']['hosts'], default)
    def test_raises_exception(self):
        self.write_config(self.args['configfile'], 
        """
        [weird brackets go here]
        I'm not a yaml file!!!=I have no keys
        I have lots of spaces
        """)
        self.assertRaises(ConfigurationError, get_yaml, self.args['configfile'])
