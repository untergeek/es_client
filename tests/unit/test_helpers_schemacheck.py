from unittest import TestCase
from es_client.exceptions import ConfigurationError
from es_client.helpers.schemacheck import SchemaCheck
from es_client.defaults import config_schema

class TestSchemaCheck(TestCase):
    def test_bad_port_value(self):
        config = {
            'elasticsearch': {
                'client': {
                    'port': 70000
                }
            }
        }
        schema = SchemaCheck(
            config,
            config_schema(),
            'elasticsearch',
            'client'
        )
        self.assertRaises(ConfigurationError, schema.result)
    def test_entirely_wrong_keys(self):
        config = {
            'elasticsearch': {
                'client_not': {},
                'not_aws': {},
            },
            'something_else': 'foo'
        }
        schema = SchemaCheck(
            config,
            config_schema(),
            'elasticsearch',
            'client'
        )
        self.assertRaises(ConfigurationError, schema.result)