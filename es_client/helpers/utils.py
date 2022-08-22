import logging
import os
import yaml
import re
from es_client.defaults import config_schema
from es_client.exceptions import ConfigurationError
from es_client.helpers.schemacheck import SchemaCheck

logger = logging.getLogger(__name__)

def prune_nones(mydict):
    """
    Remove keys from `mydict` whose values are `None`

    :arg mydict: The dictionary to act on
    :rtype: dict
    """
    # Test for `None` instead of existence or zero values will be caught
    return dict([(k,v) for k, v in mydict.items() if v != None and v != 'None'])

def ensure_list(data):
    """
    Return a list, even if data is a single value

    :arg data: A list or scalar variable to act upon
    :rtype: list
    """
    if not isinstance(data, list): # in case of a single value passed
        data = [data]
    return data

def read_file(myfile):
    """
    Read a file and return the resulting data.

    :arg myfile: A file to read.
    :rtype: str
    """
    try:
        with open(myfile, 'r') as f:
            data = f.read()
        return data
    except IOError as e:
        msg = 'Unable to read file {0}. Exception: {1}'.format(myfile, e)
        logger.error(msg)
        raise ConfigurationError(msg)

def verify_ssl_paths(args):
    """
    Verify that the various certificate/key paths are readable.  The
    :func:`~es_client.helpers.utils.read_file` function will raise a
    :exc:`~es_client.exceptions.ConfigurationError` if a file fails to be read.


    :arg args: The ``client`` block of the config dictionary.
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

def get_yaml(path):
    """
    Read the file identified by `path` and import its YAML contents.

    :arg path: The path to a YAML configuration file.
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
    # except yaml.scanner.ScannerError as err:
    #     print('Unable to read/parse YAML file: {0}'.format(path))
    #     print(err)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as err:
        raise ConfigurationError(
            'Unable to parse YAML file. Error: {0}'.format(err))
