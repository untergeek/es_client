"""Client builder helper functions"""
from typing import Tuple
import logging
from shutil import get_terminal_size
from click import secho
from elasticsearch8 import Elasticsearch
from es_client.builder import Builder, ClientArgs, OtherArgs
from es_client import defaults
from es_client.exceptions import ESClientException, ConfigurationError
from es_client.helpers.utils import check_config, get_yaml, prune_nones, verify_url_schema

def cli_opts(
        value: str, settings: dict=None,
        onoff: dict=None, override: dict=None) -> Tuple[Tuple[str,], dict]:
    """
    In order to make building a Click interface more cleanly, this function returns all Click
    option settings indicated by ``value``, both forming the lone argument (e.g. ``--option``),
    and all key word arguments as a dict.

    The single arg is rendered as ``f'--{value}'``. Likewise, ``value`` is the key to extract
    all keyword args from the supplied dictionary.
    The facilities to override default values and show hidden values is added here.
    For default value overriding, the NOPE constant is used as None and False are valid default
    values
    """
    if override is None:
        override = {}
    if settings is None:
        settings = defaults.CLICK_SETTINGS
    if not isinstance(settings, dict):
        raise ConfigurationError(f'"settings" is not a dictionary: {type(settings)}')
    if not value in settings:
        raise ConfigurationError(f'{value} not in settings')
    argval = f'--{value}'
    if isinstance(onoff, dict):
        try:
            argval = f'--{onoff["on"]}{value}/--{onoff["off"]}{value}'
        except KeyError as exc:
            raise ConfigurationError from exc
    return (argval,), override_settings(settings[value], override)

def cloud_id_override(args: dict, params: dict, client_args: ClientArgs) -> dict:
    """
    If hosts are in the config file, but cloud_id is specified at the command-line,
    we need to remove the hosts parameter as cloud_id and hosts are mutually exclusive

    This function returns an updated dictionary ``args`` to be used for the final configuration as
    well as updates the ``client_args`` object.

    :param args: The argument dictionary derived params.
    :param params: Click context params, e.g. ``ctx.params``
    :param client_args: The working list of client args

    :type args: dict
    :type params: dict from :py:class:`~.click.Context.params`
    :type client_args: :py:class:`~.es_client.builder.ClientArgs`

    :rtype: dict
    :returns: Updated version of ``args``
    """
    logger = logging.getLogger(__name__)
    if 'cloud_id' in params and params['cloud_id']:
        logger.info('cloud_id from command-line superseding configuration file settings')
        client_args.hosts = None
        args.pop('hosts', None)
    return args

def context_settings():
    """Return Click context settings dictionary"""
    help_options = {'help_option_names': ['-h', '--help']}
    return {**get_width(), **help_options}

def get_arg_objects(config: dict) -> Tuple[ClientArgs, OtherArgs]:
    """
    Return initial tuple of :py:class:`~.es_client.builder.ClientArgs`, 
    :py:class:`~.es_client.builder.OtherArgs`

    They will be either empty/default, or with values from ``config``

    :param config: Config dict derived from a YAML configuration file.

    :type config: dict
    
    :rtype: tuple
    :returns: :py:class:`~.es_client.builder.ClientArgs` and 
        :py:class:`~.es_client.builder.OtherArgs` objects in a tuple
    """
    client_args = ClientArgs()
    other_args = OtherArgs()
    validated_config = check_config(config)
    client_args.update_settings(validated_config['client'])
    other_args.update_settings(validated_config['other_settings'])
    return client_args, other_args

def get_args(params: dict, config: dict) -> Tuple[ClientArgs, OtherArgs]:
    """
    Return ClientArgs, OtherArgs tuple from params overriding whatever may be in config

    :param params: Click context params, e.g. ``ctx.params``
    :param default_filepath: File path to a default config file location.

    :type params: dict from :py:class:`~.click.Context.params``
    :type default_filepath: str

    :rtype: tuple
    :returns: :py:class:`~.es_client.builder.ClientArgs` and 
        :py:class:`~.es_client.builder.OtherArgs` objects in a tuple
    """
    client_args, other_args = get_arg_objects(config)
    override_client_args(params, client_args)
    override_other_args(params, other_args)
    return client_args, other_args

def get_client(
    configdict: dict=None, configfile: str=None, autoconnect: bool=False,
    version_min: tuple=defaults.VERSION_MIN,
    version_max: tuple=defaults.VERSION_MAX) -> Elasticsearch:
    """Get an Elasticsearch Client using :py:class:`es_client.builder.Builder`

    Build a client out of settings from `configfile` or `configdict`
    If neither `configfile` nor `configdict` is provided, empty defaults will be used.
    If both are provided, `configdict` will be used, and `configfile` ignored.

    :param configdict: A configuration dictionary
    :param configfile: A configuration file
    :param autoconnect: Connect to client automatically
    :param verion_min: Minimum acceptable version of Elasticsearch (major, minor, patch)
    :param verion_max: Maximum acceptable version of Elasticsearch (major, minor, patch)

    :type configdict: dict
    :type configfile: str
    :type autoconnect: bool
    :type version_min: tuple
    :type version_max: tuple

    :returns: A client connection object
    :rtype: :py:class:`~.elasticsearch.Elasticsearch`
    """
    logger = logging.getLogger(__name__)
    logger.debug('Creating client object and testing connection')

    builder = Builder(
        configdict=configdict, configfile=configfile, autoconnect=autoconnect,
        version_min=version_min, version_max=version_max
    )

    try:
        builder.connect()
    except Exception as exc:
        logger.critical('Unable to establish client connection to Elasticsearch!')
        logger.critical('Exception encountered: %s', exc)
        raise ESClientException from exc

    return builder.client

def get_config(params: dict, default_config: str = None) -> dict:
    """
    If params['config'] is a valid path, return the validated dictionary from the YAML

    If nothing has been provided to params['config'], but default_config is populated, use that.

    :param params: Click context params, e.g. ``ctx.params``
    :param default_config: Path to a configuration file

    :type params: dict from :py:class:`~.click.Context.params``
    :type default_config: str

    :returns: Configuration dictionary
    :rtype: dict
    """
    config = {'config':{}} # Set a default empty value
    if params['config']:
        config = get_yaml(params['config'])
    # If no config was provided, but default config path exists, use it instead
    elif default_config:
        secho(f'Using default configuration file at {default_config}', bold=True)
        config = get_yaml(default_config)
    return config

def get_hosts(params: dict) -> list:
    """
    Return hostlist suitable for client object. Validate url schema for each entry.
    
    :param params: Click context params, e.g. ``ctx.params``

    :type params: dict from :py:class:`~.click.Context.params``

    :returns: List of hosts
    :rtype: list
    """
    logger = logging.getLogger(__name__)
    hostslist = []
    if 'hosts' in params and params['hosts']:
        for host in list(params['hosts']):
            try:
                hostslist.append(verify_url_schema(host))
            except ConfigurationError as err:
                logger.error('Incorrect URL Schema: %s', err)
                raise ConfigurationError from err
    else:
        hostslist = None
    return hostslist

def get_width():
    """Determine terminal width"""
    return {"max_content_width": get_terminal_size()[0]}

def hosts_override(args: dict, params: dict, client_args: ClientArgs) -> dict:
    """
    If hosts are provided at the command-line, but cloud_id was in the config file, we need to
    remove the cloud_id parameter from the config file-based dictionary before merging.
    This function returns an updated dictionary ``args`` to be used for the final configuration as
    well as updates the ``client_args`` object.

    :param args: The argument dictionary derived params.
    :param params: Click context params, e.g. ``ctx.params``
    :param client_args: The working list of client args

    :type args: dict
    :type params: dict from :py:class:`~.click.Context.params`
    :type client_args: :py:class:`~.es_client.builder.ClientArgs`

    :rtype: dict
    :returns: Updated version of ``args``
    """
    logger = logging.getLogger(__name__)
    if 'hosts' in params and params['hosts']:
        logger.info('hosts from command-line superseding configuration file settings')
        client_args.hosts = None
        client_args.cloud_id = None
        args.pop('cloud_id', None)
    return args

def override_client_args(params: dict, client_args: ClientArgs) -> ClientArgs:
    """
    Override client_args settings with any values found in params
    
    :param params: Click context params, e.g. ``ctx.params``
    :param client_args: The working list of client args

    :type params: dict from :py:class:`~.click.Context.params``
    :type client_args: :py:class:`~.es_client.builder.ClientArgs`

    :returns: The updated working list ClientArgs object
    :rtype: :py:class:`~.es_client.builder.ClientArgs`
    """
    logger = logging.getLogger(__name__)
    args = {}
    # Populate args from params
    for key, value in params.items():
        if key in defaults.CLIENT_SETTINGS:
            if key == 'hosts':
                args[key] = get_hosts(params)
            elif value is not None:
                args[key] = value
    args = cloud_id_override(args, params, client_args)
    args = hosts_override(args, params, client_args)
    args = prune_nones(args)
    # Update the object if we have settings to override after pruning None values
    if args:
        client_args.update_settings(args)
    # Use a default hosts value of localhost:9200 if there is no host and no cloud_id set
    if client_args.hosts is None and client_args.cloud_id is None:
        logger.debug('No hosts or cloud_id set! Setting default host to http://127.0.0.1:9200')
        client_args.hosts = ["http://127.0.0.1:9200"]
    return client_args

def override_other_args(params: dict, other_args: OtherArgs) -> OtherArgs:
    """
    Override other_args settings with any values found in params

    :param params: Click context params, e.g. ``ctx.params``
    :param other_args: The working list of other args

    :type params: dict from :py:class:`~.click.Context.params``
    :type other_args: :py:class:`~.es_client.builder.OtherArgs`

    :returns: The updated working list OtherArgs object
    :rtype: :py:class:`~.es_client.builder.OtherArgs`
    """
    args = prune_nones({
        'master_only': params['master_only'],
        'skip_version_test': params['skip_version_test'],
        'username': params['username'],
        'password': params['password'],
        'api_key': {
            'id': params['id'],
            'api_key': params['api_key'],
            'token': params['api_token'],
        }
    })

    # Remove `api_key` root key if `id` and `api_key` and `token` are all None
    if params['id'] is None and params['api_key'] is None and params['api_token'] is None:
        del args['api_key']

    if args:
        other_args.update_settings(args)
    return other_args

def override_settings(settings: dict, override: dict) -> dict:
    """
    Override keys in settings with values matching in override

    :param settings: The source data
    :param override: The data which will override ``settings``

    :type settings: dict
    :type override: dict

    :rtype: dict
    :returns: An dictionary based on ``settings`` updated with values from ``override``
    """
    if not isinstance(override, dict):
        raise ConfigurationError(f'override must be of type dict: {type(override)}')
    for key in list(override.keys()):
        # This formerly checked for the presence of key in settings, but override should add
        # non-existing keys if desired.
        settings[key] = override[key]
    return settings
