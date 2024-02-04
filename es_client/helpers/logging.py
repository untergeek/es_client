"""Logging Helpers"""
from typing import Union
import sys
import json
import logging
import time
from pathlib import Path
from click import Context, echo as clicho
import ecs_logging
from es_client.helpers.schemacheck import SchemaCheck
from es_client.helpers.utils import ensure_list, prune_nones
from es_client.exceptions import LoggingException
from es_client.defaults import config_logging, LOGDEFAULTS

###############
### Classes ###
###############

class Whitelist(logging.Filter):
    """
    Child class inheriting :py:class:`logging.Filter`, patched to permit only specifically named
    :py:func:`loggers <logging.getLogger()>` to write logs.
    """
    # pylint: disable=super-init-not-called
    def __init__(self, *whitelist):
        """
        :param whitelist: List of names defined by :py:func:`logging.getLogger()`
            e.g. 

              .. code-block: python

                ['es_client.helpers.config', 'es_client.builder']

        :type whitelist: list
        """
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)

class Blacklist(Whitelist):
    """
    Child class inheriting :py:class:`Whitelist`, patched to permit all but specifically named
    :py:func:`loggers <logging.getLogger()>` to write logs.

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
        'levelname': 'loglevel',
        'funcName': 'function',
        'lineno': 'linenum',
        'message': 'message',
        'name': 'name'
    }

    def format(self, record):
        """
        :param record: The incoming log message

        :rtype: :py:meth:`json.dumps`
        """
        self.converter = time.gmtime
        timestamp = f"{self.formatTime(record, datefmt='%Y-%m-%dT%H:%M:%S')}.{record.msecs:03}Z"
        result = {'@timestamp': timestamp}
        available = record.__dict__
        # This is cleverness because 'message' is NOT a member key of ``record.__dict__``
        # the ``getMessage()`` method is effectively ``msg % args`` (actual keys)
        # By manually adding 'message' to ``available``, it simplifies the code
        available['message'] = record.getMessage()
        for attribute in set(self.WANTED_ATTRS).intersection(available):
            result = deepmerge(
                de_dot(self.WANTED_ATTRS[attribute], getattr(record, attribute)), result
            )
        # The following is mostly for mimicking the ecs format. You can't have 2x 'message' keys in
        # WANTED_ATTRS, so we set the value to 'log.original' for ecs, and this code block
        # guarantees it still appears as 'message' too.
        if 'message' not in result.items():
            result['message'] = available['message']
        return json.dumps(result, sort_keys=True)

#################
### Functions ###
#################

def check_logging_config(config):
    """
    :param config: Logging configuration data

    :type config: dict

    :returns: :py:class:`~.es_client.helpers.schemacheck.SchemaCheck` validated logging
        configuration.

    Ensure that the top-level key ``logging`` is in `config`. Set empty default dictionary if key
    ``logging`` is not in `config`.

    Pass the result to
    :py:class:`~.es_client.helpers.schemacheck.SchemaCheck` for full validation.
    """

    if not isinstance(config, dict):
        clicho(
            f'Must supply logging information as a dictionary. '
            f'You supplied: "{config}" which is "{type(config)}"'
            f'Using default logging values.'
        )
        log_settings = {}
    elif not 'logging' in config:
        # None provided. Use defaults.
        log_settings = {}
    else:
        if config['logging']:
            log_settings = prune_nones(config['logging'])
        else:
            log_settings = {}
    return SchemaCheck(
        log_settings, config_logging(), 'Logging Configuration', 'logging').result()

def configure_logging(ctx: Context) -> None:
    """
    :param ctx: The Click command context 

    :type params: :py:class:`~.click.Context`

    :rtype: None

    Configure logging based on a combination of :py:attr:`ctx.obj['draftcfg'] <click.Context.obj>`
    and :py:attr:`ctx.params <click.Context.params>`.

    Values in :py:attr:`ctx.params <click.Context.params>` will override anything set in
    :py:attr:`ctx.obj['draftcfg'] <click.Context.obj>`
    """
    logcfg = override_logging(ctx.obj['draftcfg'], ctx.params)
    # Now enable logging with the merged settings, verifying the settings are still good
    set_logging(check_logging_config({'logging': logcfg}))

def de_dot(dot_string: str, msg: str) -> dict:
    """
    :param dot_string: The dotted string
    :param msg: The message

    :type dot_string: str
    :type msg: str

    :rtype: dict
    :returns: A nested dictionary of keys with the final value being the message

    Turn `message` and `dot_string` into a nested dictionary. Used by :py:class:`JSONFormatter`
    """
    arr = dot_string.split('.')
    arr.append(msg)
    retval = None
    for idx in range(len(arr), 1, -1):
        if not retval:
            try:
                retval = {arr[idx-2]: arr[idx-1]}
            except Exception as err:
                raise LoggingException(err) from err
        else:
            try:
                new_d = {arr[idx-2]: retval}
                retval = new_d
            except Exception as err:
                raise LoggingException(err) from err
    return retval

def deepmerge(source: dict, destination: dict) -> dict:
    """
    :param source: Source dictionary
    :param destination: Destination dictionary

    :type source: dict
    :type destination: dict

    :returns: destination
    :rtype: dict

    Recursively merge deeply nested dictionary structure `source` into `destination`. Used by
    :py:class:`JSONFormatter`
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deepmerge(value, node)
        else:
            destination[key] = value
    return destination

def get_handler(logfile: str | None) -> Union[logging.FileHandler, logging.StreamHandler]:
    """
    :param logfile: The path of a log file

    :type logfile: str

    :rtype: Either :py:class:`~.logging.FileHandler` or :py:class:`~.logging.StreamHandler`
    :returns: A logging handler

    This function checks first to see if a file path has been provided via `logfile`. If
    so, it will return :py:class:`logging.Filehandler(logfile) <logging.FileHandler>`

    If this is not provided, it will then proceed to check if it is running in a Docker container,
    and, if so, whether it has write permissions to ``/proc/1/fd/1``, which is the default TTY path.
    If so, it will return :py:class:`logging.Filehandler('/proc/1/fd/1') <logging.FileHandler>`.
    Writing to this path permits an app using :py:mod:`es_client` to read logs by way of:

      .. code-block:: shell

         docker logs CONTAINERNAME
    
    If neither of the prior are true, then it will return
    :py:class:`logging.StreamHandler(stream=sys.stdout) <logging.StreamHandler>`, and will write to
    STDOUT.
    """
    handler = None
    # Priority handling of provided logfile first
    if logfile:
        handler = logging.FileHandler(logfile)
    # If no logfile is specified, check to see if we're running in a Docker container next
    elif is_docker():
        fpath = '/proc/1/fd/1'
        permission = False
        try:
            with open(fpath, 'wb+', buffering=0) as fhdl:
                # And we've verified that the path is a tty
                if fhdl.isatty():
                    # And verified that we have write permissions to that path
                    fhdl.write('...\n'.encode())
                    permission = True
        except PermissionError:
            clicho(f'Docker container does not appear to have a writable tty at {fpath}.')
        if permission:
            handler = logging.FileHandler(fpath)
    # Otherwise, write to STDOUT
    if handler is None:
        handler = logging.StreamHandler(stream=sys.stdout)
    return handler

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
           - When set on a logger, indicates that ancestor loggers are to be consulted to
             determine the effective level. If that still resolves to NOTSET, then all events
             are logged. When set on a handler, all events are handled.
         * - DEBUG
           - 10
           - Detailed information, typically only of interest to a developer trying to diagnose
             a problem.
         * - INFO
           - 20
           - Confirmation that things are working as expected.
         * - WARNING
           - 30
           - An indication that something unexpected happened, or that a problem might occur in
             the near future (e.g. 'disk space low'). The software is still working as expected.
         * - ERROR
           - 40
           - Due to a more serious problem, the software has not been able to perform some
             function.
         * - CRITICAL
           - 50
           - A serious error, indicating that the program itself may be unable to continue
             running.

    Raises a :py:exc:`ValueError` exception if an invalid value for `level` is provided.
    """
    numeric_log_level = getattr(logging, level.upper(), None)

    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {level}")
    return numeric_log_level

def is_docker() -> bool:
    """
    :rtype: bool
    :returns: Boolean result of whether we are runinng in a Docker container or not
    """
    cgroup = Path('/proc/self/cgroup')
    return (
        Path('/.dockerenv').is_file() or cgroup.is_file() and
            'docker' in cgroup.read_text(encoding='utf8')
    )

def override_logging(config: dict, params: dict) -> dict:
    """
    :param config: The configuration from file
    :param params: The parameters entered at the command-line 

    :type config: dict
    :type params: dict from :py:attr:`ctx.params <click.Context.params>`

    :returns: Log configuration ready for validation
    :rtype: dict

    Get logging configuration from `config` and override with any command-line options
    """
    # Check for log settings from config file
    init_logcfg = check_logging_config(config)

    # Override anything with options from the command-line
    paramlist = ['loglevel', 'logfile', 'logformat', 'blacklist']
    for entry in paramlist:
        if entry in params:
            if entry == 'blacklist':
                init_logcfg[entry] = list(params[entry])
            else:
                init_logcfg[entry] = params[entry]

    return init_logcfg

def check_log_opts(log_opts: dict) -> dict:
    """
    :param log_opts: Logging configuration data

    :type log_opts: dict

    :rtype: dict
    :returns: Updated `log_opts` dictionary with default values where unset
    """
    for k, v in LOGDEFAULTS.items():
        log_opts[k] = v if not k in log_opts else log_opts[k]
    return log_opts

def set_logging(options: dict, logger_name: str='es_client') -> None:
    """
    :param options: Logging configuration data
    :param logger_name: Default logger name to use in :py:func:`logging.getLogger()`

    :type options: dict
    :type logger_name: str

    :rtype: None
    
    Configure global logging options from `options` and set a default `logger_name`
    """
    log_opts = check_log_opts(options)
    handler = get_handler(log_opts['logfile'])
    numeric_log_level = get_numeric_loglevel(log_opts['loglevel'])

    if numeric_log_level == 10: # DEBUG
        format_string = (
            '%(asctime)s %(levelname)-9s %(name)22s %(funcName)22s:%(lineno)-4d %(message)s')
    else:
        format_string = '%(asctime)s %(levelname)-9s %(message)s'

    if log_opts['logformat'] == 'json':
        handler.setFormatter(JSONFormatter())
    elif log_opts['logformat'] == 'ecs':
        handler.setFormatter(ecs_logging.StdlibFormatter())
    else:
        handler.setFormatter(logging.Formatter(format_string))

    logging.root.addHandler(handler)
    logging.root.setLevel(numeric_log_level)

    _ = logging.getLogger(logger_name)
    # Set up NullHandler() to handle nested elasticsearch8.trace Logger
    # instance in elasticsearch python client
    logging.getLogger('elasticsearch8.trace').addHandler(logging.NullHandler())
    if log_opts['blacklist']:
        for entry in ensure_list(log_opts['blacklist']):
            for handler in logging.root.handlers:
                handler.addFilter(Blacklist(entry))