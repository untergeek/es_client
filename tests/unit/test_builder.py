import certifi
from unittest import TestCase
from . import FileTestCase
from botocore.exceptions import NoCredentialsError
from es_client.builder import Builder
from es_client.exceptions import ConfigurationError, MissingArgument
from mock import Mock, patch

class TestUrlPrefix(TestCase):
    def test_url_prefix_is_none(self):
        obj = Builder({}, autoconnect=False)
        obj.client_args['url_prefix'] = None
        obj._fix_url_prefix()
        self.assertEqual('', obj.client_args['url_prefix'])

class TestHttpAuth(TestCase):
    def test_user_but_no_pass(self):
        obj = Builder({}, autoconnect=False)
        obj.client_args['username'] = 'test'
        self.assertRaises(ConfigurationError, obj._check_http_auth)
    def test_pass_but_no_user(self):
        obj = Builder({}, autoconnect=False)
        obj.client_args['password'] = 'test'
        self.assertRaises(ConfigurationError, obj._check_http_auth)
    def test_http_auth_tuple(self):
        u = 'username'
        p = 'password'
        obj = Builder({}, autoconnect=False)
        obj.client_args[u] = u
        obj.client_args[p] = p
        obj._check_http_auth()
        self.assertFalse(u in obj.client_args)
        self.assertFalse(p in obj.client_args)
        self.assertEqual((u, p), obj.client_args['http_auth'])

class TestCheckSSL(TestCase):
    def test_certifi(self):
        obj = Builder({}, autoconnect=False)
        obj.client_args['use_ssl'] = True
        obj._check_ssl()
        self.assertTrue(obj.client_args['verify_certs'])
        self.assertEqual(certifi.where(), obj.client_args['ca_certs'])

class TestAWS(TestCase):
    def test_no_region_raises(self):
        obj = Builder({}, autoconnect=False)
        obj.use_aws = True
        self.assertRaises(MissingArgument, obj._parse_aws)
    def test_no_credentials_raises(self):
        obj = Builder({}, autoconnect=False)
        obj.use_aws = True
        obj.aws['aws_region'] = 'us_east'
        self.assertRaises(NoCredentialsError, obj._parse_aws)
    @patch('boto3.session.Session', autospec=True)
    def test_mock_session_creds(self, mock_session):
        session_instance = mock_session.return_value
        credentials_instance = session_instance.get_credentials.return_value
        credentials_instance.access_key = 'access_key'
        credentials_instance.secret_key = 'secret_key'
        credentials_instance.token = 'token'
        obj = Builder({}, autoconnect=False)
        obj.use_aws = True
        obj.aws['aws_region'] = 'us_east'
        obj._parse_aws()
        self.assertTrue(obj.client_args['use_ssl'])

    