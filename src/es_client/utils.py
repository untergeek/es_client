"""Utility functions for es_client

This module provides helper functions for configuration validation, file handling, and
CLI setup in es_client. It supports :class:`~es_client.builder.Builder`,
:mod:`~es_client.logging`, and :mod:`~es_client.config` with tasks like URL validation,
YAML parsing, and sensitive data redaction.

Functions:
    check_config: Validate an Elasticsearch configuration dictionary.
    ensure_list: Convert a scalar or list to a list.
    file_exists: Check if a file exists.
    get_version: Retrieve the Elasticsearch version as a tuple.
    get_yaml: Load a YAML file with environment variable parsing.
    option_wrapper: Wrap click.option for configuration storage.
    parse_apikey_token: Decode a base64-encoded API key token.
    passthrough: Generic wrapper for click decorators.
    prune_nones: Remove keys with None values from a dictionary.
    read_file: Read a file's contents.
    verify_ssl_paths: Verify readability of SSL certificate/key paths.
    verify_url_schema: Validate and normalize URL schemas for hosts.
"""

import typing as t
import logging
import os
import re
import base64
import binascii
from pathlib import Path
import yaml  # type: ignore
import click
from elasticsearch8 import Elasticsearch
from .debug import debug, begin_end
from .defaults import ES_DEFAULT, config_schema
from .exceptions import ConfigurationError
from .schemacheck import SchemaCheck, password_filter

logger = logging.getLogger(__name__)


@begin_end()
def check_config(config: dict, quiet: bool = False) -> dict:
    """
    Validate an Elasticsearch configuration dictionary.

    Args:
        config (dict): Configuration dictionary to validate.
        quiet (bool, optional): Suppress warning logs if True. Defaults to False.

    Returns:
        dict: Validated configuration for :class:`~es_client.builder.Builder`.

    Ensures 'elasticsearch', 'client', and 'other_settings' keys are present in
    `config`, using :data:`~es_client.defaults.ES_DEFAULT` if missing. Validates
    against :func:`~es_client.defaults.config_schema` via
    :class:`~es_client.schemacheck.SchemaCheck`.

    Raises:
        :exc:`~es_client.exceptions.FailedValidation`: If validation fails.

    Example:
        >>> config = {'elasticsearch': {'client': {'hosts': ['http://localhost:9200']}}}
        >>> result = check_config(config, quiet=True)
        >>> result['client']['hosts']
        ['http://localhost:9200']
        >>> check_config([], quiet=True)
        {'client': {}, 'other_settings': {}}
    """
    if not isinstance(config, dict):
        logger.warning(
            "Elasticsearch client configuration must be provided as a dictionary."
        )
        logger.warning('You supplied: "%s" which is "%s".', config, type(config))
        logger.warning("Using default values.")
        es_settings = ES_DEFAULT
    elif "elasticsearch" not in config:
        if not quiet:
            logger.warning(
                'No "elasticsearch" setting in configuration. Using defaults.'
            )
        es_settings = ES_DEFAULT
    else:
        es_settings = config
    for key in ["client", "other_settings"]:
        if key not in es_settings["elasticsearch"]:
            es_settings["elasticsearch"][key] = {}
        else:
            es_settings["elasticsearch"][key] = prune_nones(
                es_settings["elasticsearch"][key]
            )
    retval = SchemaCheck(
        es_settings["elasticsearch"],
        config_schema(),
        "Elasticsearch Configuration",
        "elasticsearch",
    ).result()
    debug.lv5(f'Return value = "{password_filter(retval)}"')
    return retval


@begin_end()
def ensure_list(data: t.Any) -> list:
    """
    Convert a scalar or list to a list.

    Args:
        data: A scalar or list to convert.

    Returns:
        list: A list containing `data` if scalar, or `data` itself if already a list.

    Example:
        >>> ensure_list('item')
        ['item']
        >>> ensure_list(['item1', 'item2'])
        ['item1', 'item2']
    """
    if not isinstance(data, list):
        data = [data]
    debug.lv5(f'Return value = "{data}"')
    return data


@begin_end()
def file_exists(file: str) -> bool:
    """
    Check if a file exists.

    Args:
        file (str): Path to the file.

    Returns:
        bool: True if `file` exists, False otherwise.

    Example:
        >>> from pathlib import Path
        >>> Path('test.txt').write_text('test')
        4
        >>> file_exists('test.txt')
        True
        >>> file_exists('nonexistent.txt')
        False
        >>> Path('test.txt').unlink()
    """
    retval = Path(file).is_file()
    debug.lv5(f'Return value = "{retval}"')
    return retval


@begin_end()
def get_version(client: Elasticsearch) -> t.Tuple:
    """
    Retrieve the Elasticsearch version as a tuple.

    Args:
        client (:class:`elasticsearch8.Elasticsearch`): Elasticsearch client instance.

    Returns:
        tuple: Version as (major, minor, patch).

    Extracts the version from `client.info()['version']['number']`, stripping
    non-semantic tags (e.g., '-dev', '-beta') and limiting to three parts.

    Example:
        >>> from unittest.mock import Mock
        >>> client = Mock()
        >>> client.info.return_value = {'version': {'number': '8.0.0'}}
        >>> get_version(client)
        (8, 0, 0)
    """
    version = client.info()["version"]["number"]
    version = version.split("-")[0]
    if len(version.split(".")) > 3:
        version = version.split(".")[:-1]
    else:
        version = version.split(".")
    retval = tuple(map(int, version))
    debug.lv5(f'Return value = "{retval}"')
    return retval


@begin_end()
def get_yaml(path: str) -> t.Dict:
    """
    Load a YAML file with environment variable parsing.

    Args:
        path (str): Path to the YAML file.

    Returns:
        dict: Parsed YAML contents.

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If the YAML file is invalid
            or unreadable.

    Supports environment variable substitution in YAML using `${VAR:DEFAULT}` syntax.

    Example:
        >>> from pathlib import Path
        >>> Path('test.yaml').write_text('host: ${HOST:localhost}')
        23
        >>> os.environ['HOST'] = '127.0.0.1'
        >>> config = get_yaml('test.yaml')
        >>> config['host']
        '127.0.0.1'
        >>> Path('test.yaml').unlink()
    """
    single = re.compile(r"^\$\{(.*)\}$")
    yaml.add_implicit_resolver("!single", single)

    def single_constructor(loader, node):
        value = loader.construct_scalar(node)
        proto = single.match(value).group(1)
        default = None
        if len(proto.split(":")) > 1:
            envvar, default = proto.split(":")
        else:
            envvar = proto
        return os.environ[envvar] if envvar in os.environ else default

    yaml.add_constructor("!single", single_constructor)
    try:
        debug.lv4('TRY: yaml.load()')
        retval = yaml.load(read_file(path), Loader=yaml.FullLoader)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as exc:
        raise ConfigurationError(f"Unable to parse YAML file. Error: {exc}") from exc
    debug.lv5('Return value = "<REDACTED YAML>"')
    return retval


def option_wrapper() -> t.Callable:
    """
    Wrap click.option for configuration storage.

    Returns:
        callable: Wrapper function for :func:`click.option`.

    Example:
        >>> wrapper = option_wrapper()
        >>> isinstance(wrapper(('option',), {}), click.decorators._Option)
        True
    """
    return passthrough(click.option)


@begin_end()
def parse_apikey_token(token: str) -> t.Tuple:
    """
    Decode a base64-encoded API key token.

    Args:
        token (str): Base64-encoded token in the format 'id:api_key'.

    Returns:
        tuple: (id, api_key) extracted from the token.

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If the token is invalid.

    Example:
        >>> parse_apikey_token('Zm9vOmJhcg==')  # base64 for 'foo:bar'
        ('foo', 'bar')
        >>> parse_apikey_token('invalid')
        Traceback (most recent call last):
            ...
        es_client.exceptions.ConfigurationError: Unable to parse base64 API Key
        Token: Incorrect padding
    """
    try:
        debug.lv4('TRY: base64.b64decode()')
        decoded = base64.b64decode(token).decode("utf-8")
        split = decoded.split(":")
    except (binascii.Error, IndexError, UnicodeDecodeError) as exc:
        debug.lv3('Exiting function, raising exception')
        debug.lv5(f'Value = "{exc}"')
        logger.error(
            "Unable to parse base64 API Key Token. Ensure you are using the correct "
            "format: <id>:<api_key>"
        )
        raise ConfigurationError(
            f"Unable to parse base64 API Key Token: {exc}"
        ) from exc
    retval = (split[0], split[1])
    debug.lv5('Return value = "<REDACTED API Key>"')
    return retval


def passthrough(func) -> t.Callable:
    """
    Generic wrapper for click decorators.

    Args:
        func (callable): Function to wrap (e.g., :func:`click.option`).

    Returns:
        callable: Wrapped function passing arguments through.

    Example:
        >>> wrapped = passthrough(lambda x: x * 2)
        >>> wrapped(5)
        10
    """
    return lambda a, k: func(*a, **k)


@begin_end()
def prune_nones(mydict: t.Dict) -> t.Dict:
    """
    Remove keys with None values from a dictionary.

    Args:
        mydict (dict): Dictionary to process.

    Returns:
        dict: Dictionary with None-valued keys removed.

    Example:
        >>> prune_nones({'a': 1, 'b': None, 'c': 'None'})
        {'a': 1}
    """
    retval = dict([(k, v) for k, v in mydict.items() if v is not None and v != "None"])
    debug.lv5(f'Return value = "{password_filter(retval)}"')
    return retval


@begin_end()
def read_file(myfile: str) -> str:
    """
    Read a file's contents.

    Args:
        myfile (str): Path to the file.

    Returns:
        str: File contents.

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If the file cannot be read.

    Example:
        >>> from pathlib import Path
        >>> Path('test.txt').write_text('test')
        4
        >>> read_file('test.txt')
        'test'
        >>> Path('test.txt').unlink()
    """
    try:
        debug.lv4('TRY: open() and read() file...')
        with open(myfile, "r", encoding="utf-8") as f:
            data = f.read()
        debug.lv3('Exiting function, returning value')
        debug.lv5('Value = "<REDACTED FILE>"')
        return data
    except IOError as exc:
        msg = f"Unable to read file {myfile}. Exception: {exc}"
        debug.lv3('Exiting function, raising exception')
        logger.error(msg)
        raise ConfigurationError(msg) from exc


@begin_end()
def verify_ssl_paths(args: t.Dict) -> None:
    """
    Verify readability of SSL certificate/key paths.

    Args:
        args (dict): Configuration with 'ca_certs', 'client_cert', or 'client_key' keys.

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If any file is unreadable.

    Checks if paths in `args` for 'ca_certs', 'client_cert', or 'client_key' are
    readable using :func:`read_file`.

    Example:
        >>> from pathlib import Path
        >>> Path('cert.pem').write_text('cert')
        4
        >>> verify_ssl_paths({'ca_certs': 'cert.pem'})
        >>> verify_ssl_paths({'ca_certs': 'nonexistent.pem'})
        Traceback (most recent call last):
            ...
        es_client.exceptions.ConfigurationError: Unable to read file nonexistent.pem.
        Exception: [Errno 2] No such file or directory: 'nonexistent.pem'
        >>> Path('cert.pem').unlink()
    """
    if "ca_certs" in args and args["ca_certs"] is not None:
        read_file(args["ca_certs"])
    if "client_cert" in args and args["client_cert"] is not None:
        read_file(args["client_cert"])
    if "client_key" in args and args["client_key"] is not None:
        read_file(args["client_key"])


@begin_end()
def verify_url_schema(url: str) -> str:
    """
    Validate and normalize a URL schema for Elasticsearch hosts.

    Args:
        url (str): URL to validate (e.g., 'http://localhost:9200').

    Returns:
        str: Normalized URL with schema and port (e.g., 'http://localhost:80').

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If the URL schema is invalid.

    Ensures the URL uses 'http' or 'https' and includes a port (defaults to 80 for
    http, 443 for https if omitted).

    Example:
        >>> verify_url_schema('https://localhost')
        'https://localhost:443'
        >>> verify_url_schema('ftp://localhost')
        Traceback (most recent call last):
            ...
        es_client.exceptions.ConfigurationError: URL Schema invalid for ftp://localhost
    """
    parts = url.lower().split(":")
    errmsg = f"URL Schema invalid for {url}"
    if len(parts) < 3:
        if parts[0] == "https":
            port = "443"
        elif parts[0] == "http":
            port = "80"
        else:
            debug.lv3('Exiting function, raising exception')
            debug.lv5(f'Value = "{errmsg}"')
            logger.error(f'Invalid URL schema: "{url}". Missing port?')
            raise ConfigurationError(errmsg)
    elif len(parts) == 3:
        if (parts[0] != "http") and (parts[0] != "https"):
            debug.lv3('Exiting function, raising exception')
            debug.lv5(f'Value = "{errmsg}"')
            logger.error(f'Invalid URL schema: "{url}"')
            raise ConfigurationError(errmsg)
        port = parts[2]
    else:
        debug.lv3('Exiting function, raising exception')
        debug.lv5(f'Value = "{errmsg}"')
        logger.error(f'Invalid URL schema: "{url}"')
        raise ConfigurationError(errmsg)
    retval = parts[0] + ":" + parts[1] + ":" + port
    debug.lv5(f'Return value = "{retval}"')
    return retval
