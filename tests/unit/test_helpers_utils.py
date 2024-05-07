"""Test helpers.utils"""

import os
import random
import string
import binascii
from unittest import TestCase
from unittest.mock import Mock
import pytest
from es_client.exceptions import ConfigurationError
from es_client.helpers import utils as u
from . import FileTestObj

# pylint: disable=R0903,W0718

DEFAULT = {
    "elasticsearch": {
        "other_settings": {
            "master_only": False,
            "skip_version_test": False,
            "username": None,
            "password": None,
        },
        "client": {
            "hosts": "http://127.0.0.1:9200",
            "request_timeout": 30,
        },
    }
}


# The leading spaces are important here to create a proper yaml file.
YAML = "\n".join(["---", "elasticsearch:", "  client:", "    hosts: {0}"])


def random_envvar(size):
    """Generate a random environment variable"""
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(size)
    )


class TestEnsureList(TestCase):
    """Test the u.ensure_list function"""

    def test_utils_ensure_list_returns_lists(self):
        """Test several examples of lists: existing lists, strings, mixed lists/numbers, etc."""
        verify = ["a", "b", "c", "d"]
        source = ["a", "b", "c", "d"]
        self.assertEqual(verify, u.ensure_list(source))
        verify = ["abcd"]
        source = "abcd"
        self.assertEqual(verify, u.ensure_list(source))
        verify = [["abcd", "defg"], 1, 2, 3]
        source = [["abcd", "defg"], 1, 2, 3]
        self.assertEqual(verify, u.ensure_list(source))
        verify = [{"a": "b", "c": "d"}]
        source = {"a": "b", "c": "d"}
        self.assertEqual(verify, u.ensure_list(source))


class TestPruneNones(TestCase):
    """Test the u.prune_nones function"""

    def test_utils_prune_nones_with(self):
        """Ensure that a dict with a single None value comes back as an empty dict"""
        self.assertEqual({}, u.prune_nones({"a": None}))

    def test_utils_prune_nones_without(self):
        """Ensure that a dict with no None values comes back unchanged"""
        testval = {"foo": "bar"}
        self.assertEqual(testval, u.prune_nones(testval))


class TestReadFile:
    """Test the u.read_file function"""

    def test_utils_read_file_present(self):
        """Ensure that the written value is what was in the filename"""
        obj = FileTestObj()
        assert obj.written_value == u.read_file(obj.args["filename"])
        obj.teardown()

    def test_raise_when_no_file(self):
        """Raise an exception when there is no file"""
        obj = FileTestObj()
        with pytest.raises(ConfigurationError):
            u.read_file(obj.args["no_file_here"])
        obj.teardown()


class TestReadCerts:
    """Test the u.verify_ssl_paths function"""

    def test_all_as_one(self):
        """Test all 3 possible cert files at once from the same file"""
        obj = FileTestObj()
        config = {
            "ca_certs": obj.args["filename"],
            "client_cert": obj.args["filename"],
            "client_key": obj.args["filename"],
        }
        try:
            u.verify_ssl_paths(config)
        except Exception:
            pytest.fail("Unexpected Exception...")


class TestEnvVars:
    """Test the ability to read environment variables"""

    def test_present(self):
        """Test an existing (present) envvar"""
        obj = FileTestObj()
        evar = random_envvar(8)
        os.environ[evar] = "1234"
        dollar = "${" + evar + "}"
        obj.write_config(obj.args["configfile"], YAML.format(dollar))
        cfg = u.get_yaml(obj.args["configfile"])
        assert cfg["elasticsearch"]["client"]["hosts"] == os.environ.get(evar)
        del os.environ[evar]
        obj.teardown()

    def test_not_present(self):
        """Test a non-existent (not-present) envvar. It should set None here"""
        obj = FileTestObj()
        evar = random_envvar(8)
        dollar = "${" + evar + "}"
        obj.write_config(obj.args["configfile"], YAML.format(dollar))
        cfg = u.get_yaml(obj.args["configfile"])
        assert cfg["elasticsearch"]["client"]["hosts"] is None
        obj.teardown()

    def test_not_present_with_default(self):
        """Test a non-existent (not-present) envvar. It should set a default value here"""
        obj = FileTestObj()
        evar = random_envvar(8)
        default = random_envvar(8)
        dollar = "${" + evar + ":" + default + "}"
        obj.write_config(obj.args["configfile"], YAML.format(dollar))
        cfg = u.get_yaml(obj.args["configfile"])
        assert cfg["elasticsearch"]["client"]["hosts"] == default
        obj.teardown()

    def test_raises_exception(self):
        """Ensure that improper formatting raises a ConfigurationError exception"""
        obj = FileTestObj()
        obj.write_config(
            obj.args["configfile"],
            """
            [weird brackets go here]
            I'm not a yaml file!!!=I have no keys
            I have lots of spaces
            """,
        )
        with pytest.raises(ConfigurationError):
            u.get_yaml(obj.args["configfile"])
        obj.teardown()


class TestVerifyURLSchema:
    """Test the u.verify_url_schema function"""

    def test_full_schema(self):
        """Verify that a proper schema comes back unchanged"""
        url = "https://127.0.0.1:9200"
        assert u.verify_url_schema(url) == url

    def test_http_schema_no_port(self):
        """Verify that port 80 is tacked on when no port is specified as a port is required"""
        http_port = "80"
        url = "http://127.0.0.1"
        assert u.verify_url_schema(url) == "http://127.0.0.1" + ":" + http_port

    def test_https_schema_no_port(self):
        """Verify that 443 is tacked on when no port is specified but https is the schema"""
        https_port = "443"
        url = "https://127.0.0.1"
        assert u.verify_url_schema(url) == "https://127.0.0.1" + ":" + https_port

    def test_bad_schema_no_port(self):
        """A URL starting with other than http or https raises an exception w/o port"""
        url = "abcd://127.0.0.1"
        with pytest.raises(ConfigurationError):
            u.verify_url_schema(url)

    def test_bad_schema_with_port(self):
        """A URL starting with other than http or https raises an exception w/port"""
        url = "abcd://127.0.0.1:1234"
        with pytest.raises(ConfigurationError):
            u.verify_url_schema(url)

    def test_bad_schema_too_many_colons(self):
        """An invalid URL with too many colons raises an exception"""
        url = "http://127.0.0.1:1234:5678"
        with pytest.raises(ConfigurationError):
            u.verify_url_schema(url)


class TestGetVersion:
    """Test the u.get_version function"""

    def test_positive(self):
        """Ensure that what goes in comes back out unchanged"""
        client = Mock()
        client.info.return_value = {"version": {"number": "9.9.9"}}
        version = u.get_version(client)
        assert version == (9, 9, 9)

    def test_negative(self):
        """Ensure that mismatches are caught"""
        client = Mock()
        client.info.return_value = {"version": {"number": "9.9.9"}}
        version = u.get_version(client)
        assert version != (8, 8, 8)

    def test_dev_version_4_dots(self):
        """Test that anything after a third value and a period is truncated"""
        client = Mock()
        client.info.return_value = {"version": {"number": "9.9.9.dev"}}
        version = u.get_version(client)
        assert version == (9, 9, 9)

    def test_dev_version_with_dash(self):
        """Test that anything after a third value and a dash is truncated"""
        client = Mock()
        client.info.return_value = {"version": {"number": "9.9.9-dev"}}
        version = u.get_version(client)
        assert version == (9, 9, 9)


class TestFileExists:
    """Test the u.file_exists function"""

    def test_positive(self):
        """Ensure that an existing file returns True"""
        obj = FileTestObj()
        obj.write_config(
            obj.args["configfile"],
            """
            [weird brackets go here]
            I'm not a yaml file!!!=I have no keys
            I have lots of spaces
            """,
        )
        assert u.file_exists(obj.args["configfile"])
        obj.teardown()

    def test_negative(self):
        """Ensure that a non-existing file returns False"""
        obj = FileTestObj()
        obj.write_config(
            obj.args["configfile"],
            """
            This file will be deleted
            """,
        )
        obj.teardown()
        assert not u.file_exists(obj.args["configfile"])


class TestParseAPIKeyToken:
    """Test the u.parse_apikey_token function"""

    def success(self):
        """Successfully parse a token"""
        token = "X1VoN0VZY0JJV0lrUTlrdS1QZ2k6QjNZN1VJMlVRd0NHM1VTdHhuNnRKdw=="
        expected = ("_Uh7EYcBIWIkQ9ku-Pgi", "B3Y7UI2UQwCG3UStxn6tJw")
        assert expected == u.parse_apikey_token(token)

    def raises_exception1(self):
        """Raise a binascii.Error when unable to base64 decode a token"""
        token = "Not a valid token"
        with pytest.raises(binascii.Error):
            u.parse_apikey_token(token)

    def raises_exception2(self):
        """Raise an IndexError when able to base64 decode a token, not split by colon"""
        token = "VGhpcyB0ZXh0IGhhcyBubyBjb2xvbg=="
        with pytest.raises(IndexError):
            u.parse_apikey_token(token)
