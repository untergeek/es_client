"""Test helpers.config"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
from unittest import TestCase
from es_client.builder import ClientArgs, OtherArgs
from es_client.defaults import CLICK_SETTINGS, ES_DEFAULT
from es_client.exceptions import ConfigurationError
from es_client.helpers import config
from . import FileTestObj

YAMLCONFIG = ('---\n'
'elasticsearch:\n'
'  client:\n'
'    hosts: ["http://127.0.0.1:9200"]\n'
'  other_settings:\n'
'    username: {0}\n'
'    password: {1}\n')

class TestOverrideSettings(TestCase):
    """Test override_settings functionality"""
    key = 'dict_key'
    orig = {key: '1'}
    over = {key: '2'}
    def test_basic_operation(self):
        """Ensure basic functionality"""
        self.assertEqual(self.over, config.override_settings(self.orig, self.over))
    def test_raises(self):
        """Ensure exception is raised when override is a non-dictionary"""
        self.assertRaises(ConfigurationError, config.override_settings, self.orig, 'non-dict')

class TestCliOpts(TestCase):
    """Test cli_opts function"""
    argname = 'arg'
    key = 'test'
    src = '1'
    ovr = '2'
    settings = {argname: {key: src}}
    onoff = {'on': '', 'off': 'no-'}
    override = {key: ovr}
    def test_basic_operation(self):
        """Ensure basic functionality"""
        self.assertEqual(
            ((f'--{self.argname}',), self.override),
            config.cli_opts(self.argname, settings=self.settings, override=self.override)
        )
    def test_empty_override(self):
        """Ensure value is not changed when no override dictionary provided"""
        self.assertEqual(
            ((f'--{self.argname}',), self.settings[self.argname]),
            config.cli_opts(self.argname, settings=self.settings)
        )
    def test_settings_is_none(self):
        """Ensure defaults are pulled up when no value is provided for settings"""
        value = 'ssl_version'
        self.assertEqual(
            ((f'--{value}',), CLICK_SETTINGS[value]),
            config.cli_opts(value)
        )
    def test_settings_is_nondict(self):
        """Ensure exception is raised when settings is not a dictionary"""
        self.assertRaises(ConfigurationError, config.cli_opts, self.argname, 'non-dictionary')
    def test_value_not_in_settings(self):
        """Ensure exception is raised when value is not a key in settings"""
        self.assertRaises(ConfigurationError, config.cli_opts, self.argname, {'no': 'match'})
    def test_onoff_operation(self):
        """Ensure onoff arg naming functionality"""
        self.assertEqual(
            ((f"--{self.onoff['on']}{self.argname}/--{self.onoff['off']}{self.argname}",),
                self.settings[self.argname]),
            config.cli_opts(self.argname, settings=self.settings, onoff=self.onoff)
        )
    def test_onoff_raises_on_keyerror(self):
        """Ensure onoff raises when there's a KeyError"""
        self.assertRaises(ConfigurationError,
            config.cli_opts, self.argname, settings=self.settings, onoff={'foo': 'bar'}
        )

class TestCloudIdOverride(TestCase):
    """Test cloud_id_override functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        client_args = ClientArgs()
        client_args.hosts = ES_DEFAULT
        params = {'cloud_id': 'dummy'}
        args = {'hosts': ES_DEFAULT, 'key': 'val'}
        # Pre-execution assertions
        self.assertEqual(ES_DEFAULT, client_args.hosts)
        self.assertEqual(ES_DEFAULT, args['hosts'])
        ### Execution
        retval = config.cloud_id_override(args, params, client_args)
        # Post-execution assertions
        self.assertEqual({'key': 'val'}, retval)
        self.assertIsNone(client_args.hosts)

class TestContextSettings(TestCase):
    """Test context_settings functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        key = 'help_option_names'
        value = ['-h', '--help']
        retval = config.context_settings()
        self.assertEqual(value, retval[key])

class TestGetArgObjects(TestCase):
    """Test get_arg_objects functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        client_args, other_args = config.get_arg_objects({})
        self.assertTrue(isinstance(client_args, ClientArgs))
        self.assertTrue(isinstance(other_args, OtherArgs))
        self.assertEqual(ES_DEFAULT['elasticsearch']['client']['hosts'], client_args.hosts)

class TestGetArgs(TestCase):
    """Test get_args functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        empty_client = ClientArgs()
        empty_other = OtherArgs()
        empty = {
            'elasticsearch': {
                'client': empty_client.asdict(),
                'other_settings': empty_other.asdict()
            }
        }
        params = {
            'master_only': False,
            'skip_version_test': False,
            'username': None,
            'password': None,
            'id': None,
            'api_key': None,
            'api_token': None
        }
        client_args, other_args = config.get_args(params, empty)
        self.assertTrue(isinstance(client_args, ClientArgs))
        self.assertTrue(isinstance(other_args, OtherArgs))
        self.assertEqual(ES_DEFAULT['elasticsearch']['client']['hosts'], client_args.hosts)

class TestGetConfig(TestCase):
    """Test get_config functionality"""
    user = 'joe_user'
    pswd = 'password'
    def test_provided_config(self):
        """Test reading YAML provided as --config"""
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args['configfile'], YAMLCONFIG.format(self.user, self.pswd))
        # Test
        params = {'config': file_obj.args['configfile']}
        result = config.get_config(params)
        self.assertEqual(self.user, result['elasticsearch']['other_settings']['username'])
        # Teardown
        file_obj.teardown()
    def test_default_config(self):
        """Test reading YAML provided as default config"""# Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args['configfile'], YAMLCONFIG.format(self.user, self.pswd))
        # Test
        params = {'config': None}
        result = config.get_config(params, default_config=file_obj.args['configfile'])
        self.assertEqual(self.pswd, result['elasticsearch']['other_settings']['password'])
        # Teardown
        file_obj.teardown()

class TestGetHosts(TestCase):
    """Test get_hosts functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        params = {'hosts': ['http://127.0.0.1:9200']}
        self.assertListEqual(params['hosts'], config.get_hosts(params))
    def test_params_has_no_hosts(self):
        """Ensure return value is None when params has no hosts"""
        params = {'hosts': None}
        self.assertIsNone(config.get_hosts(params))
    def test_raises_on_bad_url(self):
        """Ensure an exception is raised when a host has a bad URL schema"""
        params = {'hosts': ['hppt://elastic.co']}
        self.assertRaises(ConfigurationError, config.get_hosts, params)

class TestHostsOverride(TestCase):
    """Test hosts_override functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        client_args = ClientArgs()
        url = ES_DEFAULT['elasticsearch']['client']['hosts']
        client_args.hosts = url
        client_args.cloud_id = 'no'
        params = {'hosts': ['http://127.0.0.23:9999']}
        args = {'cloud_id': 'yes', 'key': 'val'}
        # Pre-execution assertions
        self.assertEqual(url, client_args.hosts)
        self.assertEqual('no', client_args.cloud_id)
        self.assertEqual('yes', args['cloud_id'])
        ### Execution
        retval = config.hosts_override(args, params, client_args)
        # Post-execution assertions
        self.assertEqual({'key': 'val'}, retval)
        self.assertIsNone(client_args.hosts)
        self.assertIsNone(client_args.cloud_id)
