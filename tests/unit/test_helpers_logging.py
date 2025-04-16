"""Test helpers.logging"""

from unittest import TestCase
import pytest
import click
from es_client.logging import check_logging_config, get_numeric_loglevel
from es_client.utils import get_yaml
from . import FileTestObj


def process_cmd(key):
    """Return the key from the click context's object"""
    return click.get_current_context().obj[key]


class TestCheckLoggingConfig(TestCase):
    """Test check_logging_config functionality"""

    default = {
        "loglevel": "INFO",
        "blacklist": ["elastic_transport", "urllib3"],
        "logfile": None,
        "logformat": "default",
    }

    def test_non_dict(self):
        """Ensure it yields default values"""
        assert self.default == check_logging_config("not-a-dict")

    def test_empty_key(self):
        """Ensure it yields default values too"""
        assert self.default == check_logging_config({"logging": {}})

    def test_logging_context_for_empty_logfile(self):
        """Test to see contents of ctx"""
        yamlconfig = "\n".join(
            [
                "---",
                "logging:",
                "  loglevel: INFO",
                "  logfile: ",
                "  logformat: default",
                "  blacklist: ['elastic_transport', 'urllib3']",
            ]
        )
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args["configfile"], yamlconfig)
        # Test
        val = get_yaml(file_obj.args["configfile"])
        key = 'draftcfg'
        ctx = click.Context(click.Command('cmd'), obj={key: val})
        with ctx:
            resp = process_cmd(key)
        assert resp['logging']['logfile'] is None
        # Teardown
        file_obj.teardown()


class TestGetNumericLogLevel(TestCase):
    """Test get_numeric_loglevel function"""

    def test_invalid_loglevel(self):
        """Ensure it raises an exception when an invalid loglevel is provided"""
        with pytest.raises(ValueError):
            get_numeric_loglevel("NONSENSE")
