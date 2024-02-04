"""Test helpers.config"""
# pylint: disable=protected-access, import-error
# add import-error here ^^^ to avoid false-positives for the local import
import ast
from unittest import TestCase
import click
from click.testing import CliRunner
from es_client.defaults import CLICK_SETTINGS, ES_DEFAULT
from es_client.exceptions import ConfigurationError
from es_client.helpers import config as cfgfn
from es_client.helpers.utils import option_wrapper
from es_client.version import __version__
from . import (
    DEFAULTCFG, TESTUSER, TESTPASS, YAMLCONFIG,
    FileTestObj,
    simulator, default_config_cmd, simulate_override_client_args)

ONOFF = {'on': '', 'off': 'no-'}
click_opt_wrap = option_wrapper()

def get_configdict(args, func):
    """Use a dummy click function to return the ctx.obj['configdict'] contents"""
    ctx = click.Context(func)
    with ctx:
        runner = CliRunner()
        result = runner.invoke(func, args)
    click.echo(f'RESULT = {result.output}')
    try:
        configdict = ast.literal_eval(result.output.splitlines()[-1])
    except (ValueError, IndexError):
        configdict = {}
    return configdict, result

class TestOverrideSettings(TestCase):
    """Test override_settings functionality"""
    key = 'dict_key'
    orig = {key: '1'}
    over = {key: '2'}
    def test_basic_operation(self):
        """Ensure basic functionality"""
        self.assertEqual(self.over, cfgfn.override_settings(self.orig, self.over))
    def test_raises(self):
        """Ensure exception is raised when override is a non-dictionary"""
        self.assertRaises(ConfigurationError, cfgfn.override_settings, self.orig, 'non-dict')

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
            cfgfn.cli_opts(self.argname, settings=self.settings, override=self.override)
        )
    def test_empty_override(self):
        """Ensure value is not changed when no override dictionary provided"""
        self.assertEqual(
            ((f'--{self.argname}',), self.settings[self.argname]),
            cfgfn.cli_opts(self.argname, settings=self.settings)
        )
    def test_settings_is_none(self):
        """Ensure defaults are pulled up when no value is provided for settings"""
        value = 'ssl_version'
        self.assertEqual(
            ((f'--{value}',), CLICK_SETTINGS[value]),
            cfgfn.cli_opts(value)
        )
    def test_settings_is_nondict(self):
        """Ensure exception is raised when settings is not a dictionary"""
        self.assertRaises(ConfigurationError, cfgfn.cli_opts, self.argname, 'non-dictionary')
    def test_value_not_in_settings(self):
        """Ensure exception is raised when value is not a key in settings"""
        self.assertRaises(ConfigurationError, cfgfn.cli_opts, self.argname, {'no': 'match'})
    def test_onoff_operation(self):
        """Ensure onoff arg naming functionality"""
        self.assertEqual(
            ((f"--{self.onoff['on']}{self.argname}/--{self.onoff['off']}{self.argname}",),
                self.settings[self.argname]),
            cfgfn.cli_opts(self.argname, settings=self.settings, onoff=self.onoff)
        )
    def test_onoff_raises_on_keyerror(self):
        """Ensure onoff raises when there's a KeyError"""
        self.assertRaises(ConfigurationError,
            cfgfn.cli_opts, self.argname, settings=self.settings, onoff={'foo': 'bar'}
        )

class TestCloudIdOverride(TestCase):
    """Test cloud_id_override functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args['configfile'], DEFAULTCFG)

        test_param = 'cloud_id'
        test_value = 'dummy'

        cmdargs = ['--config', file_obj.args['configfile'], f'--{test_param}', f'{test_value}']

        # Test
        configdict, _ = get_configdict(cmdargs, simulator)
        assert configdict
        assert configdict['elasticsearch']['client'][test_param] == test_value
        assert 'hosts' not in configdict['elasticsearch']['client']

        # Teardown
        file_obj.teardown()

class TestContextSettings(TestCase):
    """Test context_settings functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        key = 'help_option_names'
        value = ['-h', '--help']
        retval = cfgfn.context_settings()
        self.assertEqual(value, retval[key])

class TestOverrideClientArgs(TestCase):
    """Test override_client_args functionality, indirectly"""
    def test_uses_default(self):
        """
        Test to ensure that the default URL is used when there are no hosts
        in either the config file or the command-line args
        """
        cmdargs = []
        configdict, _ = get_configdict(cmdargs, simulate_override_client_args)
        assert configdict
        assert ES_DEFAULT['elasticsearch']['client']['hosts'] == configdict['elasticsearch']['client']['hosts']

class TestGetConfig(TestCase):
    """Test get_config functionality"""
    def test_provided_config(self):
        """Test reading YAML provided as --config"""
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args['configfile'], YAMLCONFIG.format(TESTUSER, TESTPASS))
        cmdargs = ['--config', file_obj.args['configfile']]

        # Test
        configdict, _ = get_configdict(cmdargs, simulator)
        assert configdict
        assert TESTUSER == configdict['elasticsearch']['other_settings']['username']

        # Teardown
        file_obj.teardown()

    def test_default_config(self):
        """Test reading YAML provided as default config"""
        # This one is special because it needs to test the default_config
        cmdargs = []
        configdict, _ = get_configdict(cmdargs, default_config_cmd)
        assert configdict
        assert TESTPASS == configdict['elasticsearch']['other_settings']['password']


class TestGetHosts(TestCase):
    """Test get_hosts functionality"""
    def test_basic_operation(self):
        """Ensure basic operation"""
        url = 'http://127.0.0.123:9200'
        cmdargs = ['--hosts', url]
        configdict, _ = get_configdict(cmdargs, simulator)
        assert configdict
        assert [url] == configdict['elasticsearch']['client']['hosts']

    def test_params_has_no_hosts(self):
        """Ensure the default hosts value is used when neither config nor params has any hosts"""
        cmdargs = []
        expected = 'http://127.0.0.1:9200'
        configdict, _ = get_configdict(cmdargs, simulator)
        assert configdict
        assert [expected] == configdict['elasticsearch']['client']['hosts']
    def test_raises_on_bad_url(self):
        """Ensure an exception is raised when a host has a bad URL schema"""
        url = 'hppt://elastic.co'
        cmdargs = ['--hosts', url]
        _, result = get_configdict(cmdargs, simulator)
        assert result.exit_code == 1
        assert isinstance(result.exception, ConfigurationError)

# class TestHostsOverride(TestCase):
#     """Test hosts_override functionality"""
#     def test_basic_operation(self):
#         """Ensure basic operation"""
#         client_args = ClientArgs()
#         url = ES_DEFAULT['elasticsearch']['client']['hosts']
#         client_args.hosts = url
#         client_args.cloud_id = 'no'
#         params = {'hosts': ['http://127.0.0.23:9999']}
#         args = {'cloud_id': 'yes', 'key': 'val'}
#         # Pre-execution assertions
#         self.assertEqual(url, client_args.hosts)
#         self.assertEqual('no', client_args.cloud_id)
#         self.assertEqual('yes', args['cloud_id'])
#         ### Execution
#         retval = cfgfn.hosts_override(args, params, client_args)
#         # Post-execution assertions
#         self.assertEqual({'key': 'val'}, retval)
#         self.assertIsNone(client_args.hosts)
#         self.assertIsNone(client_args.cloud_id)
