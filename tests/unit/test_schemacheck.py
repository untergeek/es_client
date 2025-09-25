"""Test schemacheck module"""

from unittest import TestCase
import pytest
from voluptuous import Schema
from es_client.exceptions import FailedValidation
from es_client.schemacheck import SchemaCheck
from es_client.defaults import (
    config_schema,
    VERSION_MIN,
    version_min,
    VERSION_MAX,
    version_max,
)


class TestSchemaCheck(TestCase):
    """Test SchemaCheck class and member functions"""

    def test_bad_port_value(self):
        """Ensure that a bad port value Raises a FailedValidation"""
        config = {"elasticsearch": {"client": {"port": 70000}}}
        schema = SchemaCheck(config, config_schema(), "elasticsearch", "client")
        with pytest.raises(FailedValidation):
            schema.result()

    def test_entirely_wrong_keys(self):
        """Ensure that unacceptable keys Raises a FailedValidation"""
        config = {
            "elasticsearch": {
                "client_not": {},
                "not_aws": {},
            },
            "something_else": "foo",
        }
        schema = SchemaCheck(config, config_schema(), "elasticsearch", "client")
        with pytest.raises(FailedValidation):
            schema.result()

    def test_does_not_password_filter_non_dict(self):
        """Ensure that if config is not a dictionary that it doesn't choke"""
        config = None
        schema = SchemaCheck(config, Schema(config), "arbitrary", "anylocation")
        assert schema.result() is None


class TestVersionMinMax(TestCase):
    """Test version min and max functions"""

    def test_version_max(self):
        """Ensure version_max returns what it's set with"""
        assert VERSION_MAX == version_max()

    def test_version_min(self):
        """Ensure version_min returns what it's set with"""
        assert VERSION_MIN == version_min()
