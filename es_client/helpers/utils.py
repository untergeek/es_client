import logging
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

def check_config(config):
    """
    Ensure that the top-level key ``elasticsearch`` and its sub-keys, ``aws``
    and ``client`` are in ``config`` before passing it to 
    :class:`~es_client.helpers.schemacheck.SchemaCheck` for value validation.
    """
    if 'elasticsearch' not in config:
        config['elasticsearch'] = {}
    else:
        config = prune_nones(config)
    for key in ['client', 'aws']:
        if key not in config['elasticsearch']:
            config['elasticsearch'][key] = {}
        else:
            config['elasticsearch'][key] = prune_nones(config['elasticsearch'][key])
    return SchemaCheck(config, config_schema(),
        'Client Configuration', 'full configuration dictionary').result()

def process_config(config_dict):
    """
    Handles the schema checking function call and the ssl file path function
    call before returning a fully vetted configuration dictionary.

    :arg config_dict: The ``raw_dict`` from :class:`~es_client.Builder`.
    :type config_dict: dict
    :rtype dict:
    """
    config = check_config(config_dict)['elasticsearch']
    verify_ssl_paths(config['client'])
    return config
