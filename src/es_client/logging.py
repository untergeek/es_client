"""Logging configuration for es_client

This module provides utilities for configuring logging in es_client, including filters
(:class:`Whitelist`, :class:`Blacklist`) and a JSON formatter (:class:`JSONFormatter`).
It supports log level conversion, logger name normalization, and setup for CLI and
configuration file inputs, integrating with :py:class:`click.Context`.

Classes:
    Whitelist: Logging filter to allow specific logger names.
    Blacklist: Logging filter to block specific logger names.
    JSONFormatter: Custom formatter for JSON log output.

Functions:
    check_logging_config: Validate logging configuration using SchemaCheck.
    configure_logging: Configure logging from a click context.
    de_dot: Replace dots in logger names with underscores.
    deepmerge: Recursively merge dictionaries for JSON formatting.
    get_format_string: Return a log format string based on log level.
    get_logger: Set up the root logger with handlers and filters.
    get_numeric_loglevel: Convert a string log level to a logging constant.
    override_logging: Merge CLI and config file logging settings.
    check_log_opts: Apply default logging options.
    set_logging: Configure global logging with handlers and filters.
"""

# The __future__ annotations line allows support for Python 3.8 and 3.9
from __future__ import annotations
import typing as t
import sys
import json
import time
import logging
from logging import FileHandler, StreamHandler
from voluptuous import Schema
from click import Context, echo as clicho
import ecs_logging
from .exceptions import LoggingException
from .defaults import config_logging, LOGDEFAULTS
from .schemacheck import SchemaCheck
from .utils import ensure_list, prune_nones

# pylint: disable=R0903

logger = logging.getLogger('')  # Root logger for this module


def check_logging_config(config: t.Dict) -> Schema:
    """
    Validate logging configuration using SchemaCheck.

    Args:
        config (dict): Logging configuration data.

    Returns:
        :class:`voluptuous.Schema`: Validated logging configuration from
            :class:`~es_client.schemacheck.SchemaCheck`.

    Ensures the top-level key ``logging`` is in `config`. Sets an empty default
    dictionary if ``logging`` is absent. Passes the result to
    :class:`~es_client.schemacheck.SchemaCheck` for validation against
    :func:`~es_client.defaults.config_logging`.

    Raises:
        :exc:`TypeError`: If `config` is not a dictionary.

    Example:
        >>> config = {'logging': {'loglevel': 'INFO'}}
        >>> result = check_logging_config(config)
        >>> result['loglevel']
        'INFO'
        >>> config = {}
        >>> result = check_logging_config(config)
        >>> result
        {}
    """
    if not isinstance(config, dict):
        clicho(
            f"Must supply logging information as a dictionary. "
            f'You supplied: "{config}" which is "{type(config)}"'
            f"Using default logging values."
        )
        log_settings = {}
    elif "logging" not in config:
        # None provided. Use defaults.
        log_settings = {}
    else:
        if config["logging"]:
            log_settings = prune_nones(config["logging"])
        else:
            log_settings = {}
    return SchemaCheck(
        log_settings, config_logging(), "Logging Configuration", "logging"
    ).result()


def configure_logging(ctx: Context) -> None:
    """
    Configure logging based on a click context.

    Merges logging settings from :attr:`ctx.obj['draftcfg'] <click.Context.obj>` and
    :attr:`ctx.params <click.Context.params>`, with CLI parameters taking precedence.
    Validates and applies the merged settings using :func:`set_logging`.

    Args:
        ctx (:class:`click.Context`): Click command context containing logging config.

    Example:
        >>> from click import Context, Command
        >>> cfg = {
            'logging': {'loglevel': 'INFO', 'logfile': None, 'logformat': 'default'}
        }
        >>> ctx = Context(Command('cmd'), obj={'draftcfg': cfg}, params={})
        >>> configure_logging(ctx)
        >>> logging.getLogger('').level
        20
    """
    logcfg = override_logging(ctx)
    set_logging(logcfg)


def de_dot(dot_string: str, msg: str) -> t.Dict[str, t.Any]:
    """
    Convert a dotted string and message into a nested dictionary.

    Args:
        dot_string (str): Dotted string (e.g., 'es_client.utils').
        msg (str): Message to nest under the final key.

    Returns:
        dict: Nested dictionary with `msg` as the leaf value.

    Raises:
        :exc:`~es_client.exceptions.LoggingException`: If dictionary creation fails.

    Used by :class:`JSONFormatter` to structure log data.

    Example:
        >>> de_dot('es_client.utils', 'test')
        {'es_client': {'utils': 'test'}}
        >>> de_dot('simple', 'test')
        {'simple': 'test'}
    """
    arr = dot_string.split(".")
    arr.append(msg)
    retval = None
    for idx in range(len(arr), 1, -1):
        if not retval:
            try:
                retval = {arr[idx - 2]: arr[idx - 1]}
            except Exception as err:
                raise LoggingException(err) from err
        else:
            try:
                new_d = {arr[idx - 2]: retval}
                retval = new_d
            except Exception as err:
                raise LoggingException(err) from err
    return retval


def deepmerge(source: t.Dict, destination: t.Dict) -> t.Dict:
    """
    Recursively merge a source dictionary into a destination dictionary.

    Args:
        source (dict): Source dictionary to merge.
        destination (dict): Destination dictionary to update.

    Returns:
        dict: Updated `destination` dictionary.

    Used by :class:`JSONFormatter` to combine log attributes.

    Example:
        >>> source = {'a': {'b': 1}, 'c': 2}
        >>> destination = {'a': {'d': 3}, 'e': 4}
        >>> deepmerge(source, destination)
        {'a': {'b': 1, 'd': 3}, 'e': 4, 'c': 2}
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deepmerge(value, node)
        else:
            destination[key] = value
    return destination


def get_format_string(nll: int) -> str:
    """
    Return a log format string based on the numeric log level.

    Args:
        nll (int): Numeric log level (e.g., 10 for DEBUG, 20 for INFO).

    Returns:
        str: Format string for :class:`logging.Formatter`.

    Example:
        >>> get_format_string(10)  # DEBUG
        '%(asctime)s %(levelname)-9s %(name)30s %(funcName)23s:%(lineno)-4d %(message)s'
        >>> get_format_string(20)  # INFO
        '%(asctime)s %(levelname)-9s %(message)s'
    """
    return (
        "%(asctime)s %(levelname)-9s %(name)30s "
        "%(funcName)23s:%(lineno)-4d %(message)s"
        if nll == 10
        else "%(asctime)s %(levelname)-9s %(message)s"
    )


def get_logger(log_opts: t.Dict) -> None:
    """
    Configure the root logger with appropriate handlers.

    If `logfile` is provided in `log_opts`, uses a :class:`logging.FileHandler`.
    Otherwise, splits logs into :class:`logging.StreamHandler` instances for stdout
    (up to INFO) and stderr (WARNING and above). Applies formatters and filters based
    on `logformat` and `blacklist`.

    Args:
        log_opts (dict): Logging configuration with keys: loglevel, logfile, logformat,
            blacklist.

    Raises:
        OSError: If `logfile` cannot be opened.
        ValueError: If `loglevel` is invalid.

    Example:
        >>> log_opts = {
            'loglevel': 'INFO',
            'logfile': None,
            'logformat': 'default',
            'blacklist': []
        }
        >>> get_logger(log_opts)
        >>> len(logging.getLogger('').handlers) >= 1
        True
    """
    logfile = log_opts.get("logfile", None)
    kind = log_opts.get("logformat", "default")
    nll = get_numeric_loglevel(log_opts.get("loglevel", "INFO"))

    logger.setLevel(nll)

    handler_map = {
        "logfile": FileHandler(logfile) if logfile else None,
        "stdout": StreamHandler(stream=sys.stdout),
        "stderr": StreamHandler(stream=sys.stderr),
    }
    format_map = {
        "default": logging.Formatter(get_format_string(nll)),
        "json": JSONFormatter(),
        "ecs": ecs_logging.StdlibFormatter(),
    }

    def add_handler(source: t.Literal['logfile', 'stdout', 'stderr']) -> None:
        handler = handler_map[source]
        handler.setFormatter(format_map[kind])
        handler.setLevel(nll)
        if source == 'stdout':
            handler.addFilter(lambda record: record.levelno <= logging.INFO)
        if source == 'stderr':
            handler.setLevel(logging.WARNING)
            fltr = max(logging.WARNING, nll)
            handler.addFilter(lambda record: record.levelno >= fltr)
            for entry in ensure_list(log_opts["blacklist"]):
                handler.addFilter(Blacklist(entry))

        logger.addHandler(handler)

    if logfile:
        add_handler('logfile')
    else:
        add_handler('stdout')
        add_handler('stderr')


def get_numeric_loglevel(level: str) -> int:
    """
    Convert a string log level to a logging module constant.

    Args:
        level (str): Log level name (e.g., 'DEBUG', 'INFO').

    Returns:
        int: Corresponding logging constant (e.g., :data:`logging.DEBUG`).

    Raises:
        ValueError: If the level is not a valid log level.

    The mapping is:

    .. list-table:: Log Levels
       :widths: 10 5 85
       :header-rows: 1

       * - Level
         - #
         - Description
       * - NOTSET
         - 0
         - When set on a logger, ancestor loggers determine the effective level.
           If NOTSET, all events are logged. On a handler, all events are handled.
       * - DEBUG
         - 10
         - Detailed information for diagnosing problems.
       * - INFO
         - 20
         - Confirmation that things are working as expected.
       * - WARNING
         - 30
         - Indicates an unexpected issue or potential problem (e.g., 'disk space low').
       * - ERROR
         - 40
         - A serious problem preventing some functionality.
       * - CRITICAL
         - 50
         - A severe error, possibly halting the program.

    Example:
        >>> get_numeric_loglevel('DEBUG')
        10
        >>> get_numeric_loglevel('INFO')
        20
        >>> get_numeric_loglevel('INVALID')
        Traceback (most recent call last):
            ...
        ValueError: Invalid log level: INVALID
    """
    numeric_log_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {level}")
    return numeric_log_level


def override_logging(ctx: Context) -> t.Dict:
    """
    Merge CLI and config file logging settings.

    Retrieves logging configuration from :attr:`ctx.obj['draftcfg'] <click.Context.obj>`
    and overrides with :attr:`ctx.params <click.Context.params>`, with CLI taking
    precedence. Validates the config using :func:`check_logging_config`.

    Args:
        ctx (:class:`click.Context`): Click command context.

    Returns:
        dict: Merged and validated logging configuration.

    Example:
        >>> from click import Context, Command
        >>> cfg = {'logging': {'loglevel': 'INFO'}}
        >>> ctx = Context(
            Command('cmd'), obj={'draftcfg': cfg}, params={'loglevel': 'DEBUG'}
        )
        >>> result = override_logging(ctx)
        >>> result['loglevel']
        'DEBUG'
    """
    init_logcfg = check_logging_config(ctx.obj["draftcfg"])
    debug = "loglevel" in init_logcfg and init_logcfg["loglevel"] == "DEBUG"
    if "loglevel" in ctx.params and ctx.params["loglevel"] is not None:
        debug = ctx.params["loglevel"] == "DEBUG"

    paramlist = ["loglevel", "logfile", "logformat", "blacklist"]
    for entry in paramlist:
        if entry in ctx.params:
            if not ctx.params[entry]:
                continue
            if (
                debug
                and init_logcfg[entry] is not None
                and init_logcfg["loglevel"] != "DEBUG"
            ):
                clicho(
                    f"DEBUG: Overriding configuration file setting {entry}="
                    f"{init_logcfg[entry]} with command-line option {entry}="
                    f"{ctx.params[entry]}"
                )
            if entry == "blacklist":
                init_logcfg[entry] = list(ctx.params[entry])
            else:
                init_logcfg[entry] = ctx.params[entry]
    return init_logcfg


def check_log_opts(log_opts: t.Dict) -> t.Dict:
    """
    Apply default logging options to unset keys.

    Args:
        log_opts (dict): Logging configuration data.

    Returns:
        dict: Updated `log_opts` with defaults from
            :data:`~es_client.defaults.LOGDEFAULTS`.

    Example:
        >>> log_opts = {'loglevel': 'INFO'}
        >>> result = check_log_opts(log_opts)
        >>> result['loglevel']
        'INFO'
        >>> 'logfile' in result
        True
    """
    for k, v in LOGDEFAULTS.items():
        log_opts[k] = v if k not in log_opts else log_opts[k]
    return log_opts


def set_logging(options: t.Dict) -> None:
    """
    Configure global logging options.

    Applies settings from `options` to the root logger, attaching handlers and filters.
    Adds a :class:`logging.NullHandler` for the 'elasticsearch8.trace' logger
    to suppress trace logs.

    Args:
        options (dict): Logging configuration with keys: loglevel, logfile, logformat,
            blacklist.

    Raises:
        OSError: If `logfile` cannot be opened.
        ValueError: If `loglevel` is invalid.

    Example:
        >>> options = {
            'loglevel': 'INFO',
            'logfile': None,
            'logformat': 'default',
            'blacklist': []
        }
        >>> set_logging(options)
        >>> len(logging.getLogger('').handlers) >= 1
        True
    """
    log_opts = check_log_opts(options)
    get_logger(log_opts)
    logging.getLogger("elasticsearch8.trace").addHandler(logging.NullHandler())
    if log_opts["blacklist"]:
        for entry in ensure_list(log_opts["blacklist"]):
            for handler in logging.root.handlers:
                handler.addFilter(Blacklist(entry))


class Whitelist(logging.Filter):
    """
    Logging filter to allow only specified logger names.

    Args:
        *whitelist (list): Logger names to allow (e.g., ['es_client']).

    Attributes:
        whitelist (list): List of :class:`logging.Filter` objects for allowed names.

    Example:
        >>> import logging
        >>> record = logging.makeLogRecord({'name': 'es_client.test', 'msg': 'Test'})
        >>> whitelist = Whitelist(['es_client'])
        >>> whitelist.filter(record)
        True
        >>> record = logging.makeLogRecord({'name': 'other.test', 'msg': 'Test'})
        >>> whitelist.filter(record)
        False
    """

    def __init__(self, *whitelist: t.List[str]):
        super().__init__()
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records based on logger name."""
        return any(f.filter(record) for f in self.whitelist)

    def __repr__(self) -> str:
        """Return a string representation of the filter."""
        return f"<Whitelist names={[f.name for f in self.whitelist]}>"


class Blacklist(Whitelist):
    """
    Logging filter to block specified logger names.

    Inherits from :class:`Whitelist`, inverting the filter logic to block listed names.

    Args:
        *blacklist (list): Logger names to block (e.g., ['es_client.utils']).

    Attributes:
        whitelist (list): List of :class:`logging.Filter` objects for blocked names.

    Example:
        >>> import logging
        >>> record = logging.makeLogRecord({'name': 'es_client.test', 'msg': 'Test'})
        >>> blacklist = Blacklist(['es_client.test'])
        >>> blacklist.filter(record)
        False
        >>> record = logging.makeLogRecord({'name': 'other.test', 'msg': 'Test'})
        >>> blacklist.filter(record)
        True
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records based on logger name."""
        return not super().filter(record)

    def __repr__(self) -> str:
        """Return a string representation of the filter."""
        return f"<Blacklist names={[f.name for f in self.whitelist]}>"


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter for JSON output.

    Formats log records as JSON objects with timestamp, log level, logger name,
    function, line number, and message.

    Attributes:
        WANTED_ATTRS (dict): Mapping of LogRecord attributes to JSON keys.

    Example:
        >>> import logging
        >>> record = logging.makeLogRecord({
        ...     'name': 'test', 'levelname': 'INFO', 'msg': 'Test message',
        ...     'funcName': 'test_func', 'lineno': 42, 'created': 1625097600.0,
        ...     'msecs': 123.456
        ... })
        >>> formatter = JSONFormatter()
        >>> formatted = formatter.format(record)
        >>> 'test' in formatted and 'INFO' in formatted
        True
    """

    WANTED_ATTRS = {
        "levelname": "loglevel",
        "funcName": "function",
        "lineno": "linenum",
        "message": "message",
        "name": "name",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        self.converter = time.gmtime
        fmt = "%Y-%m-%dT%H:%M:%S"
        mil = str(record.msecs).split(".", maxsplit=1)[0]
        timestamp = f"{self.formatTime(record, datefmt=fmt)}.{mil}Z"
        result = {"@timestamp": timestamp}
        available = record.__dict__
        available["message"] = record.getMessage()
        for attribute in set(self.WANTED_ATTRS).intersection(available):
            result = deepmerge(
                de_dot(self.WANTED_ATTRS[attribute], getattr(record, attribute)), result
            )
        if "message" not in result:
            result["message"] = available["message"]
        return json.dumps(result, sort_keys=True)

    def __repr__(self) -> str:
        """Return a string representation of the formatter."""
        return "<JSONFormatter>"
