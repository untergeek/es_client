"""Test functions in es_client.defaults"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
from unittest import TestCase
from es_client.defaults import CLIENT_SETTINGS, OTHER_SETTINGS, client_settings, other_settings


class TestSettings(TestCase):
    """Ensure test coverage of simple functions that might be deprecated in the future"""
    def test_client_settings(self):
        """Ensure matching output"""
        self.assertEqual(CLIENT_SETTINGS, client_settings())
    def test_other_settings(self):
        """Ensure matching output"""
        self.assertEqual(OTHER_SETTINGS, other_settings())
