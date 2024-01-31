"""Test helpers.logging"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
from unittest import TestCase
from es_client.helpers.logging import LogInfo, check_logging_config

class TestCheckLoggingConfig(TestCase):
    """Test check_logging_config functionality"""
    default = {
        'loglevel': 'INFO',
        'blacklist': ['elastic_transport', 'urllib3'],
        'logfile': None,
        'logformat': 'default'
    }
    def test_non_dict(self):
        """Ensure it yields default values"""
        self.assertEqual(self.default, check_logging_config('not-a-dict'))
    def test_empty_key(self):
        """Ensure it yields default values too"""
        self.assertEqual(self.default, check_logging_config({'logging':{}}))

class TestLogInfo(TestCase):
    """Test LogInfo Class"""
    def test_invalid_loglevel(self):
        """Ensure it raises an exception when an invalid loglevel is provided"""
        self.assertRaises(ValueError, LogInfo, {'loglevel': 'NONSENSE'})
