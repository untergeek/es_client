"""Exception classes for es_client

This module defines custom exceptions for es_client, used in
:class:`~es_client.builder.Builder`, :mod:`~es_client.logging`,
:mod:`~es_client.config`, :mod:`~es_client.schemacheck`, and
:mod:`~es_client.utils` to handle specific error conditions.

Classes:
    ESClientException: Base class for non-Elasticsearch exceptions.
    ConfigurationError: Exception for misconfiguration issues.
    MissingArgument: Exception for missing required arguments.
    NotMaster: Exception for non-master node connections.
    LoggingException: Exception for logging configuration failures.
    SchemaException: Base class for schema-related exceptions.
    FailedValidation: Exception for SchemaCheck validation failures.
"""

import typing as t
from copy import deepcopy
from .defaults import KEYS_TO_REDACT


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


class ESClientException(Exception):
    """
    Base class for non-Elasticsearch exceptions in es_client.

    Example:
        >>> raise ESClientException('Generic error')
        Traceback (most recent call last):
            ...
        es_client.exceptions.ESClientException: Generic error
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: Formatted string with class name and redacted message.
        """
        message = (
            password_filter(self.args[0])
            if self.args and isinstance(self.args[0], dict)
            else self.args[0] if self.args else ''
        )
        return f"<{self.__class__.__name__} message='{message}'>"


class ConfigurationError(ESClientException):
    """
    Exception for configuration errors in es_client.

    Raised when invalid settings are detected, such as malformed hosts or YAML files.

    Example:
        >>> raise ConfigurationError('Invalid host schema')
        Traceback (most recent call last):
            ...
        es_client.exceptions.ConfigurationError: Invalid host schema
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: Formatted string with class name and redacted message.
        """
        message = (
            password_filter(self.args[0])
            if self.args and isinstance(self.args[0], dict)
            else self.args[0] if self.args else ''
        )
        return f"<{self.__class__.__name__} message='{message}'>"


class MissingArgument(ESClientException):
    """
    Exception for missing required arguments in es_client.

    Raised when a necessary parameter is not provided.

    Example:
        >>> raise MissingArgument('Missing username')
        Traceback (most recent call last):
            ...
        es_client.exceptions.MissingArgument: Missing username
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: Formatted string with class name and redacted message.
        """
        message = (
            password_filter(self.args[0])
            if self.args and isinstance(self.args[0], dict)
            else self.args[0] if self.args else ''
        )
        return f"<{self.__class__.__name__} message='{message}'>"


class NotMaster(ESClientException):
    """
    Exception for non-master node connections in es_client.

    Raised when a node is not the elected master and master_only is True.

    Example:
        >>> raise NotMaster('Not the master node')
        Traceback (most recent call last):
            ...
        es_client.exceptions.NotMaster: Not the master node
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: Formatted string with class name and redacted message.
        """
        message = (
            password_filter(self.args[0])
            if self.args and isinstance(self.args[0], dict)
            else self.args[0] if self.args else ''
        )
        return f"<{self.__class__.__name__} message='{message}'>"


class LoggingException(ESClientException):
    """
    Exception for logging configuration failures in es_client.

    Raised when logging cannot be configured properly.

    Example:
        >>> raise LoggingException('Logging setup failed')
        Traceback (most recent call last):
            ...
        es_client.exceptions.LoggingException: Logging setup failed
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: Formatted string with class name and redacted message.
        """
        message = (
            password_filter(self.args[0])
            if self.args and isinstance(self.args[0], dict)
            else self.args[0] if self.args else ''
        )
        return f"<{self.__class__.__name__} message='{message}'>"


class SchemaException(ESClientException):
    """
    Base class for schema-related exceptions in es_client.

    Example:
        >>> raise SchemaException('Schema error')
        Traceback (most recent call last):
            ...
        es_client.exceptions.SchemaException: Schema error
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: Formatted string with class name and redacted message.
        """
        message = (
            password_filter(self.args[0])
            if self.args and isinstance(self.args[0], dict)
            else self.args[0] if self.args else ''
        )
        return f"<{self.__class__.__name__} message='{message}'>"


class FailedValidation(SchemaException):
    """
    Exception for SchemaCheck validation failures in es_client.

    Raised when :class:`~es_client.schemacheck.SchemaCheck` validation fails.

    Example:
        >>> raise FailedValidation('Invalid value detected')
        Traceback (most recent call last):
            ...
        es_client.exceptions.FailedValidation: Invalid value detected
    """

    def __repr__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: Formatted string with class name and redacted message.
        """
        message = (
            password_filter(self.args[0])
            if self.args and isinstance(self.args[0], dict)
            else self.args[0] if self.args else ''
        )
        return f"<{self.__class__.__name__} message='{message}'>"
