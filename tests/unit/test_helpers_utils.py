from unittest import TestCase
from . import FileTestCase
from es_client.exceptions import ConfigurationError
from es_client.helpers.utils import check_config, ensure_list, process_config, prune_nones, read_file, verify_ssl_paths

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

class TestCheckConfig(TestCase):
    def test_empty_defaults(self):
        self.assertEqual(DEFAULT, check_config({}))
    def test_somewhat_populated(self):
        config = {
            'elasticsearch': {
                'client': {
                    'hosts': '127.0.0.1'
                },
                'aws': {
                    'sign_requests': False
                }
            }
        }
        self.assertEqual(DEFAULT, check_config(config))


class TestProcessConfig(TestCase):
    def test_empty_defaults(self):
        self.assertEqual(DEFAULT['elasticsearch'], process_config({}))
