"""Test helpers.config"""

import ast
from unittest import TestCase
import pytest
import click
from click.testing import CliRunner
from es_client.defaults import CLICK_SETTINGS, ES_DEFAULT
from es_client.exceptions import ConfigurationError
from es_client.helpers import config as cfgfn
from es_client.helpers.utils import option_wrapper
from . import (
    DEFAULTCFG,
    DEFAULT_HOST,
    TESTUSER,
    TESTPASS,
    YAMLCONFIG,
    FileTestObj,
    simulator,
    default_config_cmd,
    simulate_override_client_args,
)

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
        assert self.over == cfgfn.override_settings(self.orig, self.over)

    def test_raises(self):
        """Ensure exception is raised when override is a non-dictionary"""
        with pytest.raises(ConfigurationError):
            cfgfn.override_settings(self.orig, 'non-dict')


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
        assert ((f'--{self.argname}',), self.override) == cfgfn.cli_opts(
            self.argname, settings=self.settings, override=self.override
        )

    def test_empty_override(self):
        """Ensure value is not changed when no override dictionary provided"""
        assert ((f'--{self.argname}',), self.settings[self.argname]) == cfgfn.cli_opts(
            self.argname, settings=self.settings
        )

    def test_settings_is_none(self):
        """Ensure defaults are pulled up when no value is provided for settings"""
        value = 'ssl_version'
        assert ((f'--{value}',), CLICK_SETTINGS[value]) == cfgfn.cli_opts(value)

    def test_settings_is_nondict(self):
        """Ensure exception is raised when settings is not a dictionary"""
        with pytest.raises(ConfigurationError):
            cfgfn.cli_opts(self.argname, 'non-dictionary')

    def test_value_not_in_settings(self):
        """Ensure exception is raised when value is not a key in settings"""
        with pytest.raises(ConfigurationError):
            cfgfn.cli_opts(self.argname, {'no': 'match'})

    def test_onoff_operation(self):
        """Ensure onoff arg naming functionality"""
        onval = f"{self.onoff['on']}{self.argname}"
        offval = f"{self.onoff['off']}{self.argname}"
        assert (
            (f"--{onval}/--{offval}",),
            self.settings[self.argname],
        ) == cfgfn.cli_opts(self.argname, settings=self.settings, onoff=self.onoff)

    def test_onoff_raises_on_keyerror(self):
        """Ensure onoff raises when there's a KeyError"""
        with pytest.raises(ConfigurationError):
            cfgfn.cli_opts(self.argname, settings=self.settings, onoff={'foo': 'bar'})


class TestCloudIdOverride(TestCase):
    """Test cloud_id_override functionality"""

    def test_basic_operation(self):
        """Ensure basic operation"""
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args['configfile'], DEFAULTCFG)

        test_param = 'cloud_id'
        test_value = 'dummy'

        cmdargs = [
            '--config',
            file_obj.args['configfile'],
            f'--{test_param}',
            f'{test_value}',
        ]

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
        assert value == retval[key]


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
        assert (
            ES_DEFAULT['elasticsearch']['client']['hosts']
            == configdict['elasticsearch']['client']['hosts']
        )


class TestGetConfig(TestCase):
    """Test get_config functionality"""

    def test_provided_config(self):
        """Test reading YAML provided as --config"""
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(
            file_obj.args['configfile'], YAMLCONFIG.format(TESTUSER, TESTPASS)
        )
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

    def test_crazy_sauce(self):
        """Test this crazy configuration"""
        yamlconfig = "\n".join(
            [
                "---",
                "elasticsearch:",
                "  client:",
                "    hosts:",
                f"      - {DEFAULT_HOST}",
                "    cloud_id:",
                "    ca_certs:",
                "    client_cert:",
                "    client_key:",
                "    verify_certs: False",
                "    request_timeout: 30",
                "  other_settings:",
                "    master_only: False",
                f"    username: {TESTUSER}",
                f"    password: {TESTPASS}",
                "    api_key:",
                "      id:",
                "      api_key:",
                "      token:",
            ]
        )
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args['configfile'], yamlconfig)
        cmdargs = ['--config', file_obj.args['configfile']]

        # Test
        configdict, _ = get_configdict(cmdargs, simulator)
        for key in ['cloud_id', 'ca_certs', 'client_certs', 'client_key']:
            assert key not in configdict['elasticsearch']['client']
        for key in ['id', 'api_key', 'token']:
            assert configdict['elasticsearch']['other_settings']['api_key'][key] is None

        # Teardown
        file_obj.teardown()


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
        """
        Ensure the default hosts value is used when neither config nor params has any
        hosts
        """
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
