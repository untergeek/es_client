"""Logging Helpers"""

# The __future__ annotations line allows support for Python 3.8 and 3.9 to continue
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
from es_client.exceptions import LoggingException
from es_client.defaults import config_logging, LOGDEFAULTS
from es_client.helpers.schemacheck import SchemaCheck
from es_client.helpers.utils import ensure_list, prune_nones

# from pathlib import Path  # used in the is_docker() function

# pylint: disable=R0903

logger = logging.getLogger('')  # Get the root logger for this module


class Whitelist(logging.Filter):
    """
    Child class inheriting :py:class:`logging.Filter`, patched to permit only
    specifically named :py:func:`loggers <logging.getLogger()>` to write logs.
    """

    # pylint: disable=super-init-not-called
    def __init__(self, *whitelist: list):
        """
        :param whitelist: List of names defined by :py:func:`logging.getLogger()`
            e.g.

              .. code-block: python

                ['es_client.helpers.config', 'es_client.builder']
        """
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)


class Blacklist(Whitelist):
    """
    Child class inheriting :py:class:`Whitelist`, patched to permit all but
    specifically named :py:func:`loggers <logging.getLogger()>` to write logs.

    A monkey-patched inversion of Whitelist, i.e.

    .. code-block: python

      return not Whitelist.filter(self, record)
    """

    def filter(self, record):
        return not Whitelist.filter(self, record)


class JSONFormatter(logging.Formatter):
    """JSON message formatting"""

    # The LogRecord attributes we want to carry over to the JSON message,
    # mapped to the corresponding output key.
    WANTED_ATTRS = {
        "levelname": "loglevel",
        "funcName": "function",
        "lineno": "linenum",
        "message": "message",
        "name": "name",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        :param record: The incoming log message

        :rtype: :py:meth:`json.dumps`
        """
        self.converter = time.gmtime
        fmt = "%Y-%m-%dT%H:%M:%S"
        mil = str(record.msecs).split(".", maxsplit=1)[0]
        timestamp = f"{self.formatTime(record, datefmt=fmt)}.{mil}Z"
        result = {"@timestamp": timestamp}
        available = record.__dict__
        # This is cleverness because 'message' is NOT a member key of
        # ``record.__dict__`` the ``getMessage()`` method is effectively ``msg % args``
        # (actual keys) By manually adding 'message' to ``available``, it simplifies
        # the code
        available["message"] = record.getMessage()
        for attribute in set(self.WANTED_ATTRS).intersection(available):
            result = deepmerge(
                de_dot(self.WANTED_ATTRS[attribute], getattr(record, attribute)), result
            )
        # The following is mostly for mimicking the ecs format. You can't have 2x
        # 'message' keys in WANTED_ATTRS, so we set the value to 'log.original' for
        # ecs, and this code block guarantees it still appears as 'message' too.
        if "message" not in result.items():
            result["message"] = available["message"]
        return json.dumps(result, sort_keys=True)


def check_logging_config(config: t.Dict) -> Schema:
    """
    :param config: Logging configuration data

    :type config: dict

    :returns: :py:class:`~.es_client.helpers.schemacheck.SchemaCheck` validated logging
        configuration.

    Ensure that the top-level key ``logging`` is in `config`. Set empty default
    dictionary if key ``logging`` is not in `config`.

    Pass the result to
    :py:class:`~.es_client.helpers.schemacheck.SchemaCheck` for full validation.
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
    :param ctx: The Click command context

    :type params: :py:class:`~.click.Context`

    :rtype: None

    Configure logging based on a combination of :py:attr:`ctx.obj['draftcfg']
    <click.Context.obj>` and :py:attr:`ctx.params <click.Context.params>`.

    Values in :py:attr:`ctx.params <click.Context.params>` will override anything set in
    :py:attr:`ctx.obj['draftcfg'] <click.Context.obj>`
    """
    logcfg = override_logging(ctx)
    # Now enable logging with the merged settings, verifying the settings are still good
    set_logging(logcfg)


def de_dot(dot_string: str, msg: str) -> t.Union[t.Dict[str, str], None]:
    """
    :param dot_string: The dotted string
    :param msg: The message

    :type dot_string: str
    :type msg: str

    :rtype: dict
    :returns: A nested dictionary of keys with the final value being the message

    Turn `message` and `dot_string` into a nested dictionary. Used by
    :py:class:`JSONFormatter`
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
    :param source: Source dictionary
    :param destination: Destination dictionary

    :type source: dict
    :type destination: dict

    :returns: destination
    :rtype: dict

    Recursively merge deeply nested dictionary structure `source` into `destination`.
    Used by :py:class:`JSONFormatter`
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
    :param nll: The numeric log level

    :type nll: int

    :rtype: str
    :returns: The format string based on the numeric log level
    """
    return (
        "%(asctime)s %(levelname)-9s %(name)22s "
        "%(funcName)22s:%(lineno)-4d %(message)s"
        if nll == 10
        else "%(asctime)s %(levelname)-9s %(message)s"
    )


def get_logger(log_opts: t.Dict) -> None:
    """Get the root logger with the appropriate handler(s) attached

    If a log file is provided in `log_opts`, a :py:class:`~.logging.FileHandler` is
    returned. If not, it will split logs into stdout and stderr, with the former
    handling messages up to INFO level, and the latter handling messages above that
    level.

    :param
        log_opts: Logging configuration data
        logger_name: Default logger name to use in :py:func:`logging.getLogger()`
    :type
        log_opts: dict
        logger_name: str
    :rtype
        logging.Logger
    :returns
        The root logger with the appropriate handler(s) attached
    """
    logfile = log_opts.get("logfile", None)
    kind = log_opts.get("logformat", "default")
    nll = get_numeric_loglevel(log_opts.get("loglevel", "INFO"))

    # Set the level for the root logger
    logger.setLevel(nll)

    handler_map = {
        # We can't set FileHandler to a null pointer/None
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
            # Establish our upper bound filter for stderr, in case it's set to
            # ERROR or CRITICAL, and filter them.
            handler.setLevel(logging.WARNING)
            fltr = max(logging.WARNING, nll)
            handler.addFilter(lambda record: record.levelno >= fltr)
            for entry in ensure_list(log_opts["blacklist"]):
                handler.addFilter(Blacklist(entry))

        logger.addHandler(handler)  # Add to the root logger

    # if we have a logfile, then use that
    if logfile:
        add_handler('logfile')
    else:
        add_handler('stdout')
        add_handler('stderr')


def get_numeric_loglevel(level: str) -> int:
    """
    :param level: The log level

    :type level: str

    :rtype: int

    :returns: A numeric value mapped from `level`. The mapping is as follows:

      .. list-table:: Log Levels
         :widths: 10 5 85
         :header-rows: 1

         * - Level
           - #
           - Description
         * - NOTSET
           - 0
           - When set on a logger, indicates that ancestor loggers are to be consulted
             to determine the effective level. If that still resolves to NOTSET, then
             all events are logged. When set on a handler, all events are handled.
         * - DEBUG
           - 10
           - Detailed information, typically only of interest to a developer trying to
             diagnose a problem.
         * - INFO
           - 20
           - Confirmation that things are working as expected.
         * - WARNING
           - 30
           - An indication that something unexpected happened, or that a problem might
             occur in the near future (e.g. 'disk space low'). The software is still
             working as expected.
         * - ERROR
           - 40
           - Due to a more serious problem, the software has not been able to perform
             some function.
         * - CRITICAL
           - 50
           - A serious error, indicating that the program itself may be unable to
             continue running.

    Raises a :py:exc:`ValueError` exception if an invalid value for `level` is provided.
    """
    numeric_log_level = getattr(logging, level.upper(), None)

    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {level}")
    return numeric_log_level


# def is_docker() -> bool:
#     """
#     :rtype: bool
#     :returns: Boolean result of whether we are runinng in a Docker container or not
#     """
#     cgroup = Path("/proc/self/cgroup")
#     return (
#         Path("/.dockerenv").is_file()
#         or cgroup.is_file()
#         and "docker" in cgroup.read_text(encoding="utf8")
#     )


def override_logging(ctx: Context) -> t.Dict:
    """
    :param ctx: The Click command context

    :type params: :py:class:`~.click.Context`

    :returns: Log configuration ready for validation

    Get logging configuration from `ctx.obj['draftcfg']` and override with any
    command-line options
    """
    # Check for log settings from config file
    init_logcfg = check_logging_config(ctx.obj["draftcfg"])

    # Set debug to True if config file says loglevel is DEBUG
    debug = "loglevel" in init_logcfg and init_logcfg["loglevel"] == "DEBUG"
    # if 'loglevel' is not None
    if "loglevel" in ctx.params and ctx.params["loglevel"] is not None:
        # Set debug to True if command-line options says loglevel is DEBUG,
        # otherwise set debug to False (overriding what was set by config file)
        debug = ctx.params["loglevel"] == "DEBUG"

    # Override anything with options from the command-line
    paramlist = ["loglevel", "logfile", "logformat", "blacklist"]

    for entry in paramlist:
        if entry in ctx.params:
            if not ctx.params[entry]:
                continue
            # Output to stdout if debug is True and we're not overriding a None
            # (the default) and we're not overriding DEBUG with DEBUG ;)
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
    :param log_opts: Logging configuration data

    :returns: Updated `log_opts` dictionary with default values where unset
    """
    for k, v in LOGDEFAULTS.items():
        log_opts[k] = v if k not in log_opts else log_opts[k]
    return log_opts


def set_logging(options: t.Dict) -> None:
    """
    :param options: Logging configuration data
    :param logger_name: Default logger name to use in :py:func:`logging.getLogger()`

    Configure global logging options from `options` and set a default `logger_name`
    """
    log_opts = check_log_opts(options)
    get_logger(log_opts)

    # Set up NullHandler() to handle nested elasticsearch8.trace Logger
    # instance in elasticsearch python client
    logging.getLogger("elasticsearch8.trace").addHandler(logging.NullHandler())
    if log_opts["blacklist"]:
        for entry in ensure_list(log_opts["blacklist"]):
            for handler in logging.root.handlers:
                handler.addFilter(Blacklist(entry))
