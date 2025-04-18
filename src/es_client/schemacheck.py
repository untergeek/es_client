"""Schema validation and redaction utilities

This module provides the :class:`SchemaCheck` class to validate configuration
dictionaries against a :class:`voluptuous.Schema` and a function to redact sensitive
data for secure logging. It supports configuration validation for
:class:`~es_client.builder.Builder` and logging in :mod:`~es_client.logging`.

Classes:
    SchemaCheck: Validates a configuration dictionary against a schema.

Functions:
    password_filter: Redact sensitive values from a configuration dictionary.
"""

# pylint: disable=E1101,W0718
import typing as t
import logging
from re import sub
from copy import deepcopy
from voluptuous import Schema
from .debug import debug, begin_end
from .defaults import KEYS_TO_REDACT
from .exceptions import FailedValidation

logger = logging.getLogger(__name__)


def password_filter(data: t.Dict) -> t.Dict:
    """
    Redact sensitive values from a configuration dictionary.

    Args:
        data (dict): Configuration dictionary to process.

    Returns:
        dict: A deep copy of `data` with sensitive values (keys in
            :data:`~es_client.defaults.KEYS_TO_REDACT`) replaced with 'REDACTED'.

    Recursively traverses `data`, replacing values of keys listed in
    :data:`~es_client.defaults.KEYS_TO_REDACT` (e.g., 'password', 'api_key') with
    'REDACTED' for secure logging.

    Example:
        >>> data = {'user': 'test', 'password': 'secret', 'nested': {'api_key': 'key'}}
        >>> filtered = password_filter(data)
        >>> filtered
        {'user': 'test', 'password': 'REDACTED', 'nested': {'api_key': 'REDACTED'}}
        >>> data['password']  # Original unchanged
        'secret'
    """

    def iterdict(mydict):
        for key, value in mydict.items():
            if isinstance(value, dict):
                iterdict(value)
            elif key in KEYS_TO_REDACT:
                mydict.update({key: "REDACTED"})
        return mydict

    return iterdict(deepcopy(data))


class SchemaCheck:
    """
    Validate a configuration dictionary against a voluptuous schema.

    Args:
        config (dict): Configuration dictionary to validate.
        schema (:class:`voluptuous.Schema`): Schema to validate against.
        test_what (str): Description of the configuration block (e.g., 'Client Config').
        location (str): Context of the configuration (e.g., 'elasticsearch.client').

    Attributes:
        config (dict): The configuration dictionary.
        schema (:class:`voluptuous.Schema`): The validation schema.
        test_what (str): Description of the configuration block.
        location (str): Context of the configuration.
        badvalue (str): Invalid value causing validation failure, or 'no bad value yet'.
        error (str): Validation error message, or 'No error yet'.

    Raises:
        :exc:`~es_client.exceptions.FailedValidation`: If validation fails.

    Example:
        >>> from voluptuous import Schema
        >>> schema = Schema({'host': str})
        >>> config = {'host': 'localhost'}
        >>> check = SchemaCheck(config, schema, 'Test Config', 'test')
        >>> check.result()
        {'host': 'localhost'}
        >>> config = {'host': 123}
        >>> check = SchemaCheck(config, schema, 'Test Config', 'test')
        >>> check.result()
        Traceback (most recent call last):
            ...
        es_client.exceptions.FailedValidation: Configuration: Test Config: Location:
        test: Bad Value: "123", expected str @ data['host']. Check configuration file.
    """

    def __init__(self, config: t.Dict, schema: Schema, test_what: str, location: str):
        debug.lv2('Starting function...')
        debug.lv5(f'Schema: {schema}')
        if isinstance(config, dict):
            debug.lv5(f'"{test_what} config: {password_filter(config)}"')
        else:
            debug.lv5(f'"{test_what} config: {config}"')
        self.config = config
        self.schema = schema
        self.test_what = test_what
        self.location = location
        self.badvalue = "no bad value yet"
        self.error = "No error yet"

    @begin_end()
    def parse_error(self) -> t.Any:
        """
        Extract and report the invalid value causing a validation error.

        Attempts to parse the error message to identify the bad value, updating
        :attr:`badvalue`. Logs errors if parsing fails.

        Returns:
            None: Updates :attr:`badvalue` and logs the result.

        Example:
            >>> from voluptuous import Schema
            >>> schema = Schema({'host': str})
            >>> config = {'host': 123}
            >>> check = SchemaCheck(config, schema, 'Test Config', 'test')
            >>> try:
            ...     check.result()
            ... except FailedValidation:
            ...     check.badvalue
            '123'
        """

        def get_badvalue(data_string, data):
            debug.lv5('Starting nested function...')
            elements = sub(r"[\'\]]", "", data_string).split("[")
            elements.pop(0)  # Remove 'data' prefix
            value = None
            for k in elements:
                try:
                    debug.lv4('TRY: parsing key')
                    key = int(k)
                except ValueError:
                    key = k
                if value is None:
                    value = data[key]
            debug.lv5(f'Exiting nested function, returning {value}')
            return value

        try:
            debug.lv4('TRY: parsing error')
            self.badvalue = get_badvalue(str(self.error).split()[-1], self.config)
        except Exception as exc:
            logger.error(f'Unable to extract value: {exc}')
            self.badvalue = "(could not determine)"

    @begin_end()
    def result(self) -> Schema:
        """
        Validate the configuration and return the result.

        Returns:
            :class:`voluptuous.Schema`: Validated configuration from
                :attr:`config` if successful.

        Raises:
            :exc:`~es_client.exceptions.FailedValidation`: If validation fails,
                including error details and bad value.

        Calls :meth:`parse_error` to extract the invalid value if validation fails.

        Example:
            >>> from voluptuous import Schema
            >>> schema = Schema({'host': str})
            >>> config = {'host': 'localhost'}
            >>> check = SchemaCheck(config, schema, 'Test Config', 'test')
            >>> check.result()
            {'host': 'localhost'}
        """
        try:
            debug.lv4('TRY: validating configuration...')
            return self.schema(self.config)
        except Exception as exc:
            try:
                debug.lv4('TRY: parsing exception...')
                self.error = exc.errors[0]
            except Exception as err:
                logger.error(f'Could not parse exception: {err}')
                self.error = f"{exc}"
            self.parse_error()
            logger.error(f'Schema error: {self.error}')
            msg = (
                f"Configuration: {self.test_what}: Location: {self.location}: "
                f'Bad Value: "{self.badvalue}", {self.error}. Check configuration file.'
            )
            debug.lv3('Exiting function, raising exception')
            debug.lv5(f'Value = "{exc}"')
            logger.error(msg)
            raise FailedValidation(msg) from exc

    def __repr__(self) -> str:
        """
        Return a string representation of the SchemaCheck instance.

        Returns:
            str: Description of the configuration being validated.

        Example:
            >>> from voluptuous import Schema
            >>> check = SchemaCheck(
                {'host': 'localhost'}, Schema({'host': str}), 'Test Config', 'test'
            )
            >>> repr(check)
            "<SchemaCheck test_what='Test Config' location='test'>"
        """
        return f"<SchemaCheck test_what='{self.test_what}' location='{self.location}'>"
