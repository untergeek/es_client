"""Test helpers.config"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
from unittest import TestCase
from elasticsearch8 import Elasticsearch
from es_client.builder import ClientArgs, OtherArgs
from es_client.defaults import ES_DEFAULT
from es_client.exceptions import ESClientException
from es_client.helpers import config

class TestGetClient(TestCase):
    """Test get_client functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        self.assertTrue(isinstance(config.get_client(configdict=ES_DEFAULT), Elasticsearch))
    def test_raises_when_no_connection(self):
        """Ensures that an exception is raised when it cannot connect to Elasticsearch"""
        client_args = ClientArgs()
        other_args = OtherArgs()
        client_args.update_settings(ES_DEFAULT)
        client_args.hosts = ['http://127.0.0.123:12345']
        client_args.request_timeout = 0.1
        cnf = {
            'elasticsearch': {
                'client': client_args.asdict(),
                'other_settings': other_args.asdict()
            }
        }
        self.assertRaises(ESClientException, config.get_client, configdict=cnf)
