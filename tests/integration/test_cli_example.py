"""Test cli_example"""
from os import devnull
from unittest import TestCase
from click import testing as clicktest
from es_client.cli_example import run


class TestCLIExample(TestCase):
    """Test CLI Example"""

    def test_basic_operation(self):
        """Ensure basic functionality"""
        args = [
            '--hosts', 'http://127.0.0.1:9200', 'test-connection'
        ]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args)
        self.assertEqual(0, result.exit_code)

    def test_show_all_options(self):
        """Ensure show-all-options works"""
        args = ['show-all-options']
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args=args)
        self.assertEqual(0, result.exit_code)

    def test_logging_options_json(self):
        """Testing JSON log options"""
        args = [
            '--hosts', 'http://127.0.0.1:9200',
            '--loglevel', 'DEBUG',
            '--logformat', 'json',
            'test-connection'
        ]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args=args)
        self.assertEqual(0, result.exit_code)

    def test_logging_options_ecs(self):
        """Testing ECS log options"""
        args = [
            '--hosts', 'http://127.0.0.1:9200',
            '--loglevel', 'WARNING',
            '--logfile', devnull,
            '--logformat', 'ecs',
            'test-connection'
        ]
        runner = clicktest.CliRunner()
        result = runner.invoke(run, args)
        self.assertEqual(0, result.exit_code)
