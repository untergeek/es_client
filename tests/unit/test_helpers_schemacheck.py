"""Test helpers.schemacheck"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
from unittest import TestCase
from es_client.exceptions import ConfigurationError
from es_client.helpers.schemacheck import SchemaCheck
from es_client.defaults import config_schema, VERSION_MIN, version_min, VERSION_MAX, version_max

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

class TestVersionMinMax(TestCase):
    """Test version min and max functions"""
    def test_version_max(self):
        """Ensure version_max returns what it's set with"""
        assert VERSION_MAX == version_max()
    def test_version_min(self):
        """Ensure version_min returns what it's set with"""
        assert VERSION_MIN == version_min()