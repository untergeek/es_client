"""Test helpers.config"""
from unittest import TestCase
from dotmap import DotMap  # type: ignore
from elasticsearch8 import Elasticsearch
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
        client_args = DotMap()
        other_args = DotMap()
        client_args.update(DotMap(ES_DEFAULT))
        client_args.hosts = ['http://127.0.0.123:12345']
        client_args.request_timeout = 0.1
        cnf = {
            'elasticsearch': {
                'client': client_args.toDict(),
                'other_settings': other_args.toDict()
            }
        }
        self.assertRaises(ESClientException, config.get_client, configdict=cnf)
