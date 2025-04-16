"""Unit tests for logging-related helper functions."""

from io import StringIO
import logging
import json
import re
import tempfile
import unittest
from unittest.mock import MagicMock
from es_client.logging import (
    Whitelist,
    Blacklist,
    JSONFormatter,
    check_logging_config,
    override_logging,
    get_logger,
    get_numeric_loglevel,
    get_format_string,
    check_log_opts,
    de_dot,
    deepmerge,
)


# Test custom logging filters
class TestLoggingFilters(unittest.TestCase):
    """Test custom logging filters."""

    def test_whitelist_filter(self):
        """Test that Whitelist filter allows only specified logger names."""
        whitelist = Whitelist('test_logger')
        record_allowed = logging.LogRecord(
            'test_logger', logging.INFO, 'path', 1, 'message', None, None
        )
        record_blocked = logging.LogRecord(
            'other_logger', logging.INFO, 'path', 1, 'message', None, None
        )
        self.assertTrue(whitelist.filter(record_allowed))
        self.assertFalse(whitelist.filter(record_blocked))

    def test_blacklist_filter(self):
        """Test that Blacklist filter blocks specified logger names."""
        blacklist = Blacklist('test_logger')
        record_blocked = logging.LogRecord(
            'test_logger', logging.INFO, 'path', 1, 'message', None, None
        )
        record_allowed = logging.LogRecord(
            'other_logger', logging.INFO, 'path', 1, 'message', None, None
        )
        self.assertFalse(blacklist.filter(record_blocked))
        self.assertTrue(blacklist.filter(record_allowed))


# Test JSONFormatter
class TestJSONFormatter(unittest.TestCase):
    """Test JSONFormatter class."""

    def test_format(self):
        """Test that JSONFormatter correctly formats log records into JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            'test_logger', logging.INFO, 'path', 1, 'Test message', None, None
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)
        self.assertIn('@timestamp', data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Test message')
        self.assertIn('loglevel', data)
        self.assertEqual(data['loglevel'], 'INFO')
        # Verify timestamp format (ISO 8601 with milliseconds)
        self.assertTrue(
            re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', data['@timestamp'])
        )


# Test configuration-related functions
class TestConfigurationFunctions(unittest.TestCase):
    """Test configuration-related functions."""

    def test_check_logging_config_valid(self):
        """Test check_logging_config with a valid configuration."""
        valid_config = {'logging': {'loglevel': 'DEBUG', 'logformat': 'json'}}
        result = check_logging_config(valid_config)
        self.assertEqual(result['loglevel'], 'DEBUG')
        self.assertEqual(result['logformat'], 'json')

    def test_check_logging_config_invalid(self):
        """Test check_logging_config with an invalid log level."""
        invalid_config = {'logging': {'loglevel': 'INVALID'}}
        with self.assertRaises(
            Exception
        ):  # Schema validation should raise an exception
            check_logging_config(invalid_config)

    def test_check_logging_config_no_config(self):
        """Test check_logging_config with no configuration provided."""
        no_config = {}
        result = check_logging_config(no_config)
        self.assertEqual(result['loglevel'], 'INFO')  # Default value

    def test_override_logging(self):
        """Test override_logging merges CLI options over config file settings."""
        ctx = MagicMock()
        ctx.obj = {'draftcfg': {'logging': {'loglevel': 'INFO'}}}
        ctx.params = {'loglevel': 'DEBUG'}
        result = override_logging(ctx)
        self.assertEqual(result['loglevel'], 'DEBUG')


# Test logger setup and related functions
class TestLoggerSetup(unittest.TestCase):
    """Test logger setup and related functions."""

    def setUp(self):
        """Reset logging configuration before each test."""
        logging.root.handlers = []
        logging.root.setLevel(logging.NOTSET)

    def tearDown(self):
        """Reset logging configuration after each test."""
        logging.root.handlers = []
        logging.root.setLevel(logging.NOTSET)

    def test_get_logger_with_logfile(self):
        """Test get_logger with a logfile specified."""
        with tempfile.NamedTemporaryFile() as tmpfile:
            log_opts = {
                'loglevel': 'INFO',
                'logfile': tmpfile.name,
                'logformat': 'default',
                'blacklist': [],
            }
            get_logger(log_opts)
            logger = logging.getLogger('test_logger_with_logfile')
            logger.info('Test message')
            with open(tmpfile.name, 'r', encoding='utf8') as f:
                content = f.read()
                self.assertIn('Test message', content)

    def test_get_logger_without_logfile(self):
        """Test get_logger without a logfile, using stream handlers."""
        log_opts = {'loglevel': 'INFO', 'logformat': 'default', 'blacklist': []}
        get_logger(log_opts)
        logger = logging.getLogger('test_logger_without_logfile')
        stdout = StringIO()
        stderr = StringIO()
        handler_stdout = logging.StreamHandler(stdout)
        handler_stderr = logging.StreamHandler(stderr)
        logger.addHandler(handler_stdout)
        logger.addHandler(handler_stderr)
        logger.info('Test info message')
        logger.error('Test error message')
        self.assertIn('Test info message', stdout.getvalue())
        self.assertIn('Test error message', stderr.getvalue())

    def test_get_numeric_loglevel(self):
        """Test conversion of string log levels to numeric values."""
        self.assertEqual(get_numeric_loglevel('DEBUG'), 10)
        self.assertEqual(get_numeric_loglevel('INFO'), 20)
        with self.assertRaises(ValueError):
            get_numeric_loglevel('INVALID')


# Test utility functions
class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""

    def test_get_format_string(self):
        """Test format string selection based on log level."""
        debug_format = get_format_string(10)  # DEBUG
        info_format = get_format_string(20)  # INFO
        self.assertIn('%(funcName)', debug_format)  # Detailed format for DEBUG
        self.assertNotIn('%(funcName)', info_format)  # Simpler format for INFO

    def test_check_log_opts(self):
        """Test that check_log_opts applies defaults to partial configs."""
        partial_opts = {'loglevel': 'DEBUG'}
        result = check_log_opts(partial_opts)
        self.assertEqual(result['loglevel'], 'DEBUG')
        self.assertEqual(result['logfile'], None)  # Default
        self.assertEqual(result['logformat'], 'default')  # Default

    def test_de_dot(self):
        """Test conversion of dotted strings to nested dictionaries."""
        self.assertEqual(de_dot('loglevel', 'INFO'), {'loglevel': 'INFO'})
        self.assertEqual(de_dot('a.b.c', 'value'), {'a': {'b': {'c': 'value'}}})

    def test_deepmerge(self):
        """Test recursive merging of dictionaries."""
        source = {'a': {'b': {'c': 'value'}}}
        destination = {'a': {'b': {'d': 'other'}}}
        result = deepmerge(source, destination)
        self.assertEqual(result, {'a': {'b': {'c': 'value', 'd': 'other'}}})
