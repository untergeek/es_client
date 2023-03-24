"""Helper Utility Functions"""
import logging
import os
import re
import base64
import binascii
from pathlib import Path
import yaml
from es_client.defaults import config_schema
from es_client.exceptions import ConfigurationError
from es_client.helpers.schemacheck import SchemaCheck

LOGGER = logging.getLogger(__name__)

ES_DEFAULT = {'elasticsearch':{'client':{'hosts':'http://127.0.0.1:9200'}}}

def check_config(config):
    """
    Ensure that the top-level key ``elasticsearch`` and its sub-keys, ``other_settings`` and
    ``client`` as contained in ``config`` before passing it (or empty defaults) to
    :class:`~es_client.helpers.schemacheck.SchemaCheck` for value validation.

    :param config: The configuration
    :type config: dict
    """
    if not isinstance(config, dict):
        LOGGER.warning('Elasticsearch client configuration must be provided as a dictionary.')
        LOGGER.warning('You supplied: "%s" which is "%s".', config, type(config))
        LOGGER.warning('Using default values.')
        es_settings = ES_DEFAULT
    elif not 'elasticsearch' in config:
        LOGGER.warning('No "elasticsearch" setting in supplied configuration.  Using defaults.')
        es_settings = ES_DEFAULT
    else:
        es_settings = config
    for key in ['client', 'other_settings']:
        if key not in es_settings['elasticsearch']:
            es_settings['elasticsearch'][key] = {}
        else:
            es_settings['elasticsearch'][key] = prune_nones(es_settings['elasticsearch'][key])
    return SchemaCheck(es_settings['elasticsearch'], config_schema(),
        'Elasticsearch Configuration', 'elasticsearch').result()

def ensure_list(data):
    """
    Return a list, even if data is a single value

    :param data: A list or scalar variable to act upon
    :rtype: list
    """
    if not isinstance(data, list): # in case of a single value passed
        data = [data]
    return data

def file_exists(file):
    """
    Verify the file exists

    :param file: The file to test
    :type file: str

    :returns: Whether the file exists
    :rtype: bool
    """
    return Path(file).is_file()

def get_version(client):
    """
    Get the Elasticsearch version of the connected node

    :param client: An Elasticsearch client object
    :type client: :py:class:`~.elasticsearch.Elasticsearch`

    :returns: The Elasticsearch version as a 3-part tuple, (major, minor, patch)
    :rtype: tuple
    """
    version = client.info()['version']['number']
    # Split off any -dev, -beta, or -rc tags
    version = version.split('-')[0]
    # Only take SEMVER (drop any fields over 3)
    if len(version.split('.')) > 3:
        version = version.split('.')[:-1]
    else:
        version = version.split('.')
    return tuple(map(int, version))

def get_yaml(path):
    """
    Read the file identified by `path` and import its YAML contents.

    :param path: The path to a YAML configuration file.
    :type path: str

    :returns: The contents of ``path`` translated from YAML to :py:class:`dict`
    :rtype: dict
    """
    # Set the stage here to parse single scalar value environment vars from
    # the YAML file being read
    single = re.compile(r'^\$\{(.*)\}$')
    yaml.add_implicit_resolver("!single", single)
    def single_constructor(loader, node):
        value = loader.construct_scalar(node)
        proto = single.match(value).group(1)
        default = None
        if len(proto.split(':')) > 1:
            envvar, default = proto.split(':')
        else:
            envvar = proto
        return os.environ[envvar] if envvar in os.environ else default

    yaml.add_constructor('!single', single_constructor)

    try:
        return yaml.load(read_file(path), Loader=yaml.FullLoader)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as exc:
        raise ConfigurationError(f'Unable to parse YAML file. Error: {exc}') from exc

def parse_apikey_token(token):
    """
    Split a base64 encoded API Key Token into id and api_key

    :param token: The base64 encoded API Key
    :type token: str

    :returns: A tuple of (id, api_key)
    :rtype: tuple
    """
    try:
        decoded=base64.b64decode(token).decode('utf-8')
        split = decoded.split(':')
    except (binascii.Error, IndexError, UnicodeDecodeError) as exc:
        raise ConfigurationError(f'Unable to parse base64 API Key Token: {exc}') from exc
    return (split[0], split[1])

def prune_nones(mydict):
    """
    Remove keys from `mydict` whose values are `None`

    :param mydict: The dictionary to act on
    :rtype: dict
    """
    # Test for `None` instead of existence or zero values will be caught
    return dict([(k,v) for k, v in mydict.items() if v is not None and v != 'None'])

def read_file(myfile):
    """
    Read a file and return the resulting data.

    :param myfile: A file to read.
    :rtype: str
    """
    try:
        with open(myfile, 'r', encoding='utf-8') as f:
            data = f.read()
        return data
    except IOError as exc:
        msg = f'Unable to read file {myfile}. Exception: {exc}'
        LOGGER.error(msg)
        raise ConfigurationError(msg) from exc

def verify_ssl_paths(args):
    """
    Verify that the various certificate/key paths are readable.  The
    :py:func:`~.es_client.helpers.utils.read_file` function will raise a
    :py:exc:`~.es_client.exceptions.ConfigurationError` if a file fails to be read.

    :param args: The ``client`` block of the config dictionary.
    :type args: dict
    """
    # Test whether certificate is a valid file path
    if 'ca_certs' in args and args['ca_certs'] is not None:
        read_file(args['ca_certs'])
    # Test whether client_cert is a valid file path
    if 'client_cert' in args and args['client_cert'] is not None:
        read_file(args['client_cert'])
    # Test whether client_key is a valid file path
    if 'client_key' in args and args['client_key'] is not None:
        read_file(args['client_key'])

def verify_url_schema(url):
    """
    Ensure that a valid URL schema (HTTP[S]://URL:PORT) is used

    :param url: The url to verify
    :type url: str

    :returns: Verified URL
    :rtype: str
    """
    parts = url.lower().split(':')
    errmsg = f'URL Schema invalid for {url}'
    if len(parts) < 3:
        # We do not have a port
        if parts[0] == 'https':
            port = '443'
        elif parts[0] == 'http':
            port = '80'
        else:
            raise ConfigurationError(errmsg)
    elif len(parts) == 3:
        if (parts[0] != 'http') and (parts[0] != 'https'):
            raise ConfigurationError(errmsg)
        port = parts[2]
    else:
        raise ConfigurationError(errmsg)
    return parts[0] + ':' + parts[1] + ':' + port
