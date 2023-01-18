"""Test helpers.schemacheck"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
from unittest import TestCase
from es_client.exceptions import ConfigurationError
from es_client.helpers.schemacheck import SchemaCheck
from es_client.defaults import config_schema

class TestSchemaCheck(TestCase):
    """Test SchemaCheck class and member functions"""
    def test_bad_port_value(self):
        """Ensure that a bad port value Raises a ConfigurationError"""
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
        """Ensure that unacceptable keys Raises a ConfigurationError"""
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