"""Test cli_example"""

from os import devnull
from unittest import TestCase
from click import testing as clicktest
from es_client.cli_example import run
from . import CACRT, HOST, PASS, USER
from ..unit import FileTestObj

YAMLCONFIG = "\n".join(
    [
        "---",
        "logging:",
        "  loglevel: INFO",
        "  logfile:",
        "  logformat: default",
        "  blacklist: ['elastic_transport', 'urllib3']",
    ]
)


class TestCLIExample(TestCase):
    """Test CLI Example"""

    def test_basic_operation(self):
        "Ensure basic functionality"
        args = [
            "--hosts",
            HOST,
            "--username",
            USER,
            "--password",
            PASS,
            "--ca_certs",
            CACRT,
            "--loglevel",
            "DEBUG",
            "test-connection",
        ]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args)
        assert result.exit_code == 0

    def test_show_all_options(self):
        """Ensure show-all-options works"""
        args = ["show-all-options"]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args=args)
        assert result.exit_code == 0

    def test_logging_options_json(self):
        """Testing JSON log options"""
        args = [
            "--hosts",
            HOST,
            "--username",
            USER,
            "--password",
            PASS,
            "--ca_certs",
            CACRT,
            "--loglevel",
            "DEBUG",
            "--logformat",
            "json",
            "test-connection",
        ]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args=args)
        assert result.exit_code == 0

    def test_logging_options_ecs(self):
        """Testing ECS log options"""
        args = [
            "--hosts",
            HOST,
            "--username",
            USER,
            "--password",
            PASS,
            "--ca_certs",
            CACRT,
            "--loglevel",
            "WARNING",
            "--logfile",
            devnull,
            "--logformat",
            "ecs",
            "test-connection",
        ]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args)
        assert result.exit_code == 0

    def test_logging_options_from_config_file(self):
        """Testing logging options from a config file"""
        # Build
        file_obj = FileTestObj()
        file_obj.write_config(file_obj.args["configfile"], YAMLCONFIG)
        # Test
        args = [
            "--config",
            file_obj.args["configfile"],
            "--hosts",
            HOST,
            "--username",
            USER,
            "--password",
            PASS,
            "--ca_certs",
            CACRT,
            "test-connection",
        ]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args)
        assert result.exit_code == 0
        # Teardown
        file_obj.teardown()
