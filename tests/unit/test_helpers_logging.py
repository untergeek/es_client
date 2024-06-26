"""Test helpers.logging"""

from unittest import TestCase
from es_client.helpers.logging import check_logging_config, get_numeric_loglevel


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
        self.assertEqual(self.default, check_logging_config("not-a-dict"))

    def test_empty_key(self):
        """Ensure it yields default values too"""
        self.assertEqual(self.default, check_logging_config({"logging": {}}))


class TestGetNumericLogLevel(TestCase):
    """Test get_numeric_loglevel function"""

    def test_invalid_loglevel(self):
        """Ensure it raises an exception when an invalid loglevel is provided"""
        self.assertRaises(ValueError, get_numeric_loglevel, "NONSENSE")
