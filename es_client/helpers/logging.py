"""Logging Helpers"""
import sys
import json
import logging
import time
from pathlib import Path
from click import echo as clicho
import ecs_logging
from es_client.helpers.schemacheck import SchemaCheck
from es_client.helpers.utils import ensure_list, prune_nones
from es_client.exceptions import LoggingException
from es_client.defaults import config_logging

###############
### Classes ###
###############

class Whitelist(logging.Filter):
    """How to whitelist logs"""
    # pylint: disable=super-init-not-called
    def __init__(self, *whitelist):
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)

class Blacklist(Whitelist):
    """Blacklist monkey-patch of Whitelist"""
    def filter(self, record):
        return not Whitelist.filter(self, record)

class LogInfo:
    """Logging Class"""
    def __init__(self, cfg):
        """Class Setup

        :param cfg: The logging configuration
        :type: cfg: dict
        """
        cfg['loglevel'] = 'INFO' if not 'loglevel' in cfg else cfg['loglevel']
        cfg['logfile'] = None if not 'logfile' in cfg else cfg['logfile']
        cfg['logformat'] = 'default' if not 'logformat' in cfg else cfg['logformat']
        #: Attribute. The numeric equivalent of ``cfg['loglevel']``
        self.numeric_log_level = getattr(logging, cfg['loglevel'].upper(), None)
        #: Attribute. The logging format string to use.
        self.format_string = '%(asctime)s %(levelname)-9s %(message)s'

        if not isinstance(self.numeric_log_level, int):
            raise ValueError(f"Invalid log level: {cfg['loglevel']}")

        #: Attribute. Which logging handler to use
        if is_docker():
            # We only do this if we detect Docker
            fpath = '/proc/1/fd/1'
            permission = False
            with open(fpath, 'wb+', buffering=0) as fhdl:
                try:
                    # And we've verified that the path is a tty
                    if fhdl.isatty():
                        # And verified that we have write permissions to that path
                        fhdl.write(f'Permission to write to {fpath}?\n'.encode())
                        permission = True
                except PermissionError:
                    clicho(f'Docker container does not appear to have a writable tty at {fpath}.')
            if permission:
                self.handler = logging.FileHandler(fpath)
        else:
            self.handler = logging.StreamHandler(stream=sys.stdout)
        # So while we can have either tty or stdout with Docker, regardless, we will write to the
        # configured logfile if one is specified.
        if cfg['logfile']:
            self.handler = logging.FileHandler(cfg['logfile'])

        if self.numeric_log_level == 10: # DEBUG
            self.format_string = (
                '%(asctime)s %(levelname)-9s %(name)22s %(funcName)22s:%(lineno)-4d %(message)s')

        if cfg['logformat'] == 'json':
            self.handler.setFormatter(JSONFormatter())
        elif cfg['logformat'] == 'ecs':
            self.handler.setFormatter(ecs_logging.StdlibFormatter())
        else:
            self.handler.setFormatter(logging.Formatter(self.format_string))

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
        # timestamp = '%s.%03dZ' % (
        #     self.formatTime(record, datefmt='%Y-%m-%dT%H:%M:%S'), record.msecs)
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
        # The following is mostly for the ecs format. You can't have 2x 'message' keys in
        # WANTED_ATTRS, so we set the value to 'log.original' in ecs, and this code block
        # guarantees it still appears as 'message' too.
        if 'message' not in result.items():
            result['message'] = available['message']
        return json.dumps(result, sort_keys=True)

#################
### Functions ###
#################

def check_logging_config(config):
    """
    Ensure that the top-level key ``logging`` is in ``config`` before passing it to
    :py:class:`~.es_client.helpers.schemacheck.SchemaCheck` for value validation.

    :param config: Logging configuration data

    :type config: dict

    :returns: :py:class:`~.es_client.helpers.schemacheck.SchemaCheck` validated logging
        configuration.
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

def configure_logging(config: dict, params: dict) -> None:
    """
    Configure logging based on a combination of config and params

    Values in params will override anything set in config

    :param config: Config dict derived from a YAML configuration file.
    :param params: Click context params, e.g. ``ctx.params``. A dict of configuration options.

    :type config: dict
    :type params: dict from :py:class:`~.click.Context.params``

    :rtype: None
    """
    logcfg = override_logging(config, params['loglevel'], params['logfile'], params['logformat'])
    # Now enable logging with the merged settings, verifying the settings are still good
    set_logging(check_logging_config({'logging': logcfg}))

def de_dot(dot_string: str, msg: str) -> dict:
    """
    Turn message and dotted string into a nested dictionary. Used by :py:class:`JSONFormatter`

    :param dot_string: The dotted string
    :param msg: The message

    :type dot_string: str
    :type msg: str

    :rtype: dict
    :returns: Nested dictionary of keys with the final value being the message
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
    Recursively merge deeply nested dictionary structures, ``source`` into ``destination``

    :param source: Source dictionary
    :param destination: Destination dictionary

    :type source: dict
    :type destination: dict

    :returns: destination
    :rtype: dict
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deepmerge(value, node)
        else:
            destination[key] = value
    return destination

def is_docker() -> bool:
    """Check if we're running in a docker container"""
    cgroup = Path('/proc/self/cgroup')
    return (
        Path('/.dockerenv').is_file() or cgroup.is_file() and
            'docker' in cgroup.read_text(encoding='utf8')
    )

def override_logging(config: dict, loglevel: str, logfile: str, logformat: str) -> dict:
    """Get logging config and override from command-line options

    :param config: The configuration from file
    :param loglevel: The log level
    :param logfile: The log file to write
    :param logformat: Which log format to use

    :type config: dict
    :type loglevel: str
    :type logfile: str
    :type logformat: str

    :returns: Log configuration ready for validation
    :rtype: dict
    """
    # Check for log settings from config file
    init_logcfg = check_logging_config(config)

    # Override anything with options from the command-line
    if loglevel:
        init_logcfg['loglevel'] = loglevel
    if logfile:
        init_logcfg['logfile'] = logfile
    if logformat:
        init_logcfg['logformat'] = logformat
    return init_logcfg

def set_logging(log_opts: dict) -> None:
    """Configure global logging options

    :param log_opts: Logging configuration data

    :type log_opts: dict

    :rtype: None
    """
    # Set up logging
    loginfo = LogInfo(log_opts)
    logging.root.addHandler(loginfo.handler)
    logging.root.setLevel(loginfo.numeric_log_level)
    _ = logging.getLogger('es_client')
    # Set up NullHandler() to handle nested elasticsearch8.trace Logger
    # instance in elasticsearch python client
    logging.getLogger('elasticsearch8.trace').addHandler(logging.NullHandler())
    if log_opts['blacklist']:
        for bl_entry in ensure_list(log_opts['blacklist']):
            for handler in logging.root.handlers:
                handler.addFilter(Blacklist(bl_entry))
