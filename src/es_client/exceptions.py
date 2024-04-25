"""es_client Exception classes"""


class ESClientException(Exception):
    """
    Base class for all exceptions raised by es_client which are not Elasticsearch
    exceptions.
    """


class ConfigurationError(ESClientException):
    """
    Exception raised when a misconfiguration is detected
    """


class MissingArgument(ESClientException):
    """
    Exception raised when a needed argument is not passed.
    """


class NotMaster(ESClientException):
    """
    Exception raised when connected node is not the elected master node.
    """


class LoggingException(ESClientException):
    """
    Exception raised when logging cannot be configured properly
    """


class SchemaException(ESClientException):
    """
    Exception base class for all exceptions related to Schema failure
    """


class FailedValidation(SchemaException):
    """
    Exception raised when SchemaCheck validation fails.
    """
