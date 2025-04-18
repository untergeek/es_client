"""Command-line configuration parsing and client builder helpers

This module provides functions to manage configuration for es_client, including CLI
option setup, configuration loading from YAML files, merging CLI and config settings,
and creating Elasticsearch clients. It integrates with :mod:`click` for command-line
interfaces and supports environment variables with the
:data:`~es_client.defaults.ENV_VAR_PREFIX` prefix.

Functions:
    cli_opts: Generate click option tuples for CLI decorators.
    cloud_id_override: Remove hosts from config if cloud_id is provided via CLI.
    context_settings: Configure click context with environment variable support.
    generate_configdict: Merge CLI and config file settings.
    get_arg_objects: Initialize client_args and other_args in click context.
    get_client: Create an Elasticsearch client using Builder.
    get_config: Load configuration from a YAML file or defaults.
    get_hosts: Validate and return a list of host URLs.
    get_width: Return terminal width for click context settings.
    hosts_override: Remove cloud_id from config if hosts is provided via CLI.
    options_from_dict: Decorator to add CLI options from a dictionary.
    override_client_args: Override client_args with CLI parameters.
    override_other_args: Override other_args with CLI parameters.
    override_settings: Merge override settings into a base settings dictionary.
"""

# pylint: disable=R0913
import typing as t
import logging
from shutil import get_terminal_size
from dotmap import DotMap  # type: ignore
from click import Context, secho, option as clickopt
from elasticsearch8 import Elasticsearch
from .debug import debug, begin_end
from .builder import Builder
from .defaults import (
    CLICK_SETTINGS,
    ENV_VAR_PREFIX,
    VERSION_MIN,
    VERSION_MAX,
    config_settings,
)
from .exceptions import ConfigurationError, ESClientException
from .utils import check_config, get_yaml, prune_nones, verify_url_schema

logger = logging.getLogger(__name__)


def cli_opts(
    value: str,
    settings: t.Union[t.Dict, None] = None,
    onoff: t.Union[t.Dict, None] = None,
    override: t.Union[t.Dict, None] = None,
) -> t.Tuple[t.Tuple[str,], t.Dict]:
    """
    Generate click option tuples for CLI decorators.

    Args:
        value (str): Option name, must be in `settings` or
            :data:`~es_client.defaults.CLICK_SETTINGS`.
        settings (dict, optional): Dictionary of click option parameters. Defaults to
            :data:`~es_client.defaults.CLICK_SETTINGS`.
        onoff (dict, optional): Dictionary with 'on' and 'off' keys for boolean flags
            (e.g., {'on': '', 'off': 'no-'}).
        override (dict, optional): Dictionary to override `settings` values.

    Returns:
        tuple: A tuple of (option names, parameters) for :func:`click.option`, e.g.,
            (('--option',), {'type': str, 'help': 'Description'}).

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If `value` is not in
            `settings`, `settings` is not a dict, or `onoff` parsing fails.

    Example:
        >>> opts = cli_opts('hosts', settings={'hosts': {'type': str, 'help': 'Hosts'}})
        >>> opts[0][0]
        '--hosts'
        >>> cli_opts('invalid', settings={'valid': {}})
        Traceback (most recent call last):
            ...
        es_client.exceptions.ConfigurationError: "invalid" not in settings

    Click uses decorators to establish :py:class:`options <click.Option>` and
    :py:class:`arguments <click.Argument>` for a :py:class:`command <click.Command>`.
    The parameters specified for these decorator functions can be stored as default
    dictionaries, then expanded and overridden, if desired.

    In the `cli_example.py` file, the regular
    :py:func:`click.option decorator function <click.option>` is wrapped by
    :py:func:`option_wrapper() <es_client.helpers.utils.option_wrapper>`, and is
    aliased as ``click_opt_wrap``. This wrapped decorator in turn calls this function
    and utilizes ``*`` arg expansion. If `settings` is `None`, default values from
    :py:const:`CLICK_SETTINGS <es_client.defaults.CLICK_SETTINGS>`, are used to
    populate `settings`. This function calls :func:`override_settings()` to override
    keys in `settings` with values from matching keys in `override`.

    In the example file, this looks like this:

    .. code-block:: python

      import click
      from es_client.helpers.utils import option_wrapper
      defaults.ONOFF = {'on': '', 'off': 'no-'}
      click_opt_wrap = option_wrapper()
      # ...
      @click.group(context_settings=context_settings())
      @click_opt_wrap(*cli_opts('OPTION1', settings={KEY: NEWVALUE}))
      @click_opt_wrap(*cli_opts('OPTION2', onoff=tgl))
      # ...
      @click_opt_wrap(*cli_opts('OPTIONX'))
      @click.pass_context
      def run(ctx, OPTION1, OPTION2, ..., OPTIONX):
          # code here

    The default setting KEY of ``OPTION1`` would be overriden by NEWVALUE.

    ``OPTION2`` automatically becomes a `Click boolean option`_, which splits the
    option into an enabled/disabled dichotomy by option name. In this example, it will
    be rendered as:

    .. code-block:: shell

      '--OPTION2/--no-OPTION2'

    The dictionary structure of `defaults.ONOFF` is what this what this function
    requires, i.e. an `on` key and an `off` key. The values for `on` and `off` can be
    whatever you like, e.g.

    .. code-block:: python

      defaults.ONOFF = {'on': 'enable-', 'off': 'disable-'}

    which, based on the above example, would render as:

    .. code-block:: shell

      '--enable-OPTION2/--disable-OPTION2'

    It could also be:

    .. code-block:: python

      defaults.ONOFF = {'on': 'monty-', 'off': 'python-'}

    which would render as:

    .. code-block:: shell

      '--monty-OPTION2/--python-OPTION2'

    but that would be too silly.

    A :py:exc:`ConfigurationError <es_client.exceptions.ConfigurationError>` is raised
    `value` is not found as a key in `settings`, or if the `onoff` parsing fails.

    .. _Click boolean option:
      https://click.palletsprojects.com/en/8.1.x/options/#boolean-flags
    """
    if override is None:
        override = {}
    if settings is None:
        settings = CLICK_SETTINGS
    if not isinstance(settings, dict):
        msg = f'"settings" is not a dictionary: {type(settings)}'
        secho(f'Error: {msg}', bold=True)
        raise ConfigurationError(msg)
    if value not in settings:
        msg = f'"{value}" not in settings'
        secho(f'Error: {msg}', bold=True)
        raise ConfigurationError(f"{value} not in settings")
    argval = f"--{value}"
    if isinstance(onoff, dict):
        try:
            argval = f'--{onoff["on"]}{value}/--{onoff["off"]}{value}'
        except KeyError as exc:
            secho(f'Error: Unable to parse --on/--off option: {exc}', bold=True)
            raise ConfigurationError from exc
    return (argval,), override_settings(settings[value], override)


@begin_end()
def cloud_id_override(args: t.Dict, ctx: Context) -> t.Dict:
    """
    Remove hosts from config if cloud_id is provided via CLI.

    Args:
        args (dict): Parameters from :attr:`ctx.params <click.Context.params>`.
        ctx (:class:`click.Context`): Click command context.

    Returns:
        dict: Updated `args` with `hosts` removed if `cloud_id` is present.

    Ensures command-line `cloud_id` supersedes config file `hosts`, as they are mutually
    exclusive. Updates :attr:`ctx.obj['client_args'] <click.Context.obj>`.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('cmd'), obj={'client_args':
        DotMap({'hosts': ['http://localhost']})})
        >>> ctx.params = {'cloud_id': 'my_cloud_id'}
        >>> args = {'hosts': ['http://localhost']}
        >>> cloud_id_override(args, ctx)
        {}
        >>> ctx.obj['client_args'].hosts is None
        True

    If ``hosts`` are defined in the YAML configuration file, but ``cloud_id`` is
    specified at the command-line, we need to remove the ``hosts`` parameter from the
    configuration dictionary built from the YAML file before merging. Command-line
    provided arguments always supersede configuration file ones. In this case,
    ``cloud_id`` and ``hosts`` are mutually exclusive, and the command-line provided
    ``cloud_id`` must supersede a configuration file provided ``hosts``.

    This function returns an updated dictionary `args` to be used for the final
    configuration as well as updates the :py:attr:`ctx.obj['client_args']
    <click.Context.obj>` object. It's simply easier to merge dictionaries using a
    separate object. It would be a pain and unnecessary to make another entry in
    :py:attr:`ctx.obj <click.Context.obj>` for this.
    """
    if "cloud_id" in ctx.params and ctx.params["cloud_id"]:
        debug.lv1("cloud_id from command-line superseding configuration file settings")
        ctx.obj["client_args"].hosts = None
        args.pop("hosts", None)
    debug.lv3('Exiting function, returning value')
    debug.lv5(f'Value = {args}')
    return args


def context_settings() -> t.Dict:
    """
    Configure click context settings.

    Returns:
        dict: Settings for :class:`click.Command` context, including terminal width,
            help options, default config, and environment variable prefix.

    Combines terminal width from :func:`get_width`, help options
    (``-h``, ``--help``), default config (``None``), and
    :data:`~es_client.defaults.ENV_VAR_PREFIX` for environment variables.

    Example:
        >>> settings = context_settings()
        >>> settings['auto_envvar_prefix']
        'ESCLIENT'
        >>> 'max_content_width' in settings
        True

    Includes the terminal width from :py:func:`get_width()`

    Help format settings:

    .. code-block:: python

       help_option_names=['-h', '--help']

    The default context object (``ctx.obj``) dictionary:

    .. code-block:: python

       obj={'default_config': None}

    And automatic environment variable reading based on a prefix value:

    .. code-block:: python

       auto_envvar_prefix=ENV_VAR_PREFIX

    from :py:const:`ENV_VAR_PREFIX <es_client.defaults.ENV_VAR_PREFIX>`
    """
    objdef = {"obj": {"default_config": None}}
    prefix = {"auto_envvar_prefix": ENV_VAR_PREFIX}
    help_options = {"help_option_names": ["-h", "--help"]}
    retval = {**get_width(), **help_options, **objdef, **prefix}
    return retval


def generate_configdict(ctx: Context) -> None:
    """
    Merge CLI and config file settings.

    Combines settings from :attr:`ctx.obj['draftcfg'] <click.Context.obj>` and
    :attr:`ctx.params <click.Context.params>`, with CLI parameters taking precedence.
    Stores the result in :attr:`ctx.obj['configdict'] <click.Context.obj>` for
    :class:`~es_client.builder.Builder`.

    Args:
        ctx (:class:`click.Context`): Click context with draft config and parameters.

    Example:
        >>> from click import Context, Command
        >>> cfg = {'client': {'hosts': ['http://localhost']}, 'other_settings': {}}
        >>> ctx = Context(Command('cmd'), obj={'draftcfg': {'elasticsearch': cfg}})
        >>> ctx.params = {'hosts': ['http://127.0.0.1:9200'], 'config': None}
        >>> generate_configdict(ctx)
        >>> ctx.obj['configdict']['elasticsearch']['client']['hosts']
        ['http://127.0.0.1:9200']

    Generate a client configuration dictionary from :py:attr:`ctx.params
    <click.Context.params>` and :py:attr:`ctx.obj['default_config']
    <click.Context.obj>` (if provided), suitable for use as the ``VALUE`` in
    :py:class:`Builder(configdict=VALUE) <es_client.builder.Builder>`

    It is stored as :py:attr:`ctx.obj['default_config'] <click.Context.obj>` and can be
    referenced after this function returns.

    The flow of this function is as follows:

    Step 1: Call :func:`get_arg_objects()` to create
    :py:attr:`ctx.obj['client_args'] <click.Context.obj>` and
    :py:attr:`ctx.obj['other_args'] <click.Context.obj>`, then update their values from
    :py:attr:`ctx.obj['draftcfg'] <click.Context.obj>` (which was populated by
    :func:`get_config()`).

    Step 2: Call :func:`override_client_args()` and :func:`override_other_args()`, which
    will use command-line args from :py:attr:`ctx.params <click.Context.params>` to
    override any values from the YAML configuration file.

    Step 3: Populate :py:attr:`ctx.obj['configdict'] <click.Context.obj>` from the
    resulting values.
    """
    get_arg_objects(ctx)
    override_client_args(ctx)
    override_other_args(ctx)
    ctx.obj["configdict"] = {
        "elasticsearch": {
            "client": prune_nones(ctx.obj["client_args"].toDict()),
            "other_settings": prune_nones(ctx.obj["other_args"].toDict()),
        }
    }


@begin_end()
def get_arg_objects(ctx: Context) -> None:
    """
    Initialize client_args and other_args in click context.

    Sets :attr:`ctx.obj['client_args'] <click.Context.obj>` and
    :attr:`ctx.obj['other_args'] <click.Context.obj>` as :class:`dotmap.DotMap` objects,
    populating them from :attr:`ctx.obj['draftcfg'] <click.Context.obj>` via
    :func:`~es_client.utils.check_config`.

    Args:
        ctx (:class:`click.Context`): Click context with draft configuration.

    Example:
        >>> from click import Context, Command
        >>> cfg = {'client': {'hosts': ['http://localhost']}, 'other_settings': {}}
        >>> ctx = Context(Command('cmd'), obj={'draftcfg': {'elasticsearch': cfg}})
        >>> get_arg_objects(ctx)
        >>> ctx.obj['client_args'].hosts
        ['http://localhost']

    Set :py:attr:`ctx.obj['client_args'] <click.Context.obj>` as a
    :py:class:`~.dotmap.DotMap` object, and
    :py:attr:`ctx.obj['other_args'] <click.Context.obj>` as an
    :py:class:`~.dotmap.DotMap` object.

    These will be updated with values returned from
    :func:`check_config(ctx.obj['draftcfg']) <es_client.helpers.utils.check_config>`.

    :py:attr:`ctx.obj['draftcfg'] <click.Context.obj>` was populated when
    :func:`get_config()` was called.
    """
    ctx.obj["client_args"] = DotMap()
    ctx.obj["other_args"] = DotMap()
    validated_config = check_config(ctx.obj["draftcfg"], quiet=True)
    ctx.obj["client_args"].update(DotMap(validated_config["client"]))
    ctx.obj["other_args"].update(DotMap(validated_config["other_settings"]))


@begin_end()
def get_client(
    configdict: t.Union[t.Dict, None] = None,
    configfile: t.Union[str, None] = None,
    autoconnect: bool = False,
    version_min: t.Tuple = VERSION_MIN,
    version_max: t.Tuple = VERSION_MAX,
) -> Elasticsearch:
    """
    Create an Elasticsearch client using Builder.

    Args:
        configdict (dict, optional): Configuration dictionary with 'elasticsearch' key.
        configfile (str, optional): Path to a YAML configuration file.
        autoconnect (bool, optional): Connect to client automatically. Defaults to False.
        version_min (tuple, optional): Minimum Elasticsearch version. Defaults to
            :data:`~es_client.defaults.VERSION_MIN`.
        version_max (tuple, optional): Maximum Elasticsearch version. Defaults to
            :data:`~es_client.defaults.VERSION_MAX`.

    Returns:
        :class:`elasticsearch8.Elasticsearch`: Configured Elasticsearch client.

    Raises:
        :exc:`~es_client.exceptions.ESClientException`: If client connection fails.
        :exc:`~es_client.exceptions.ConfigurationError`: If configuration is invalid.

    Prioritizes `configdict` over `configfile`. Uses defaults if neither is provided.

    Example:
        >>> config = {'elasticsearch': {'client': {'hosts': ['http://localhost:9200']}}}
        >>> client = get_client(configdict=config)
        >>> isinstance(client, Elasticsearch)
        True

    Get an Elasticsearch Client using :py:class:`~.es_client.builder.Builder`

    Build a client connection object out of settings from `configfile` or `configdict`.

    If neither `configfile` nor `configdict` is provided, empty defaults will be used.

    If both are provided, `configdict` will be used, and `configfile` ignored.

    Raises :py:exc:`ESClientException <es_client.exceptions.ESClientException>` if
    unable to connect.
    """
    debug.lv1("Creating client object and testing connection")

    builder = Builder(
        configdict=configdict,
        configfile=configfile,
        autoconnect=autoconnect,
        version_max=version_max,
        version_min=version_min,
    )

    try:
        debug.lv4('TRY: Connecting to Elasticsearch')
        builder.connect()
    except Exception as exc:
        debug.lv3('Exiting function, raising exception')
        logger.critical("Unable to establish client connection to Elasticsearch!")
        logger.critical(f"Exception encountered: {exc}")
        raise ESClientException from exc
    debug.lv5('Return value = (Elasticsearch Client object)')
    return builder.client


def get_config(ctx: Context, quiet: bool = True) -> Context:
    """
    Load configuration from a YAML file or defaults.

    Checks :attr:`ctx.params['config'] <click.Context.params>` for a YAML file path,
    falling back to :attr:`ctx.obj['default_config'] <click.Context.obj>`. Stores the
    result in :attr:`ctx.obj['draftcfg'] <click.Context.obj>`.

    Args:
        ctx (:class:`click.Context`): Click context to store configuration.
        quiet (bool, optional): Suppress stdout messages for default config. Defaults to
            True.

    Returns:
        :class:`click.Context`: Updated context with 'draftcfg' set.

    Raises:
        OSError: If the YAML file cannot be read.
        :exc:`yaml.YAMLError`: If the YAML file is invalid.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('cmd'), obj={'default_config': None},
        params={'config': None})
        >>> ctx = get_config(ctx, quiet=True)
        >>> 'draftcfg' in ctx.obj
        True

    If :py:attr:`ctx.params['config'] <click.Context.params>` is a valid path, return
    the validated dictionary from the YAML.

    If nothing has been provided to :py:attr:`ctx.params['config']
    <click.Context.params>`, but :py:attr:`ctx.obj['default_config']
    <click.Context.obj>` is populated, use that, and write a line to ``STDOUT``
    explaining this, unless `quiet` is `True`.

    Writing directly to ``STDOUT`` is done here because logging has not yet been
    configured, nor can it be as the configuration options are just barely being read.

    Store the result in :py:attr:`ctx.obj['draftcfg'] <click.Context.obj>`
    """
    ctx.obj["draftcfg"] = {"config": {}}  # Set a default empty value
    if ctx.params["config"]:
        ctx.obj["draftcfg"] = get_yaml(ctx.params["config"])
    # If no config was provided, but default config path exists, use it instead
    elif "default_config" in ctx.obj and ctx.obj["default_config"]:
        if not quiet:
            secho(
                f"Using default configuration file at {ctx.obj['default_config']}",
                bold=True,
            )
        ctx.obj["draftcfg"] = get_yaml(ctx.obj["default_config"])
    return ctx


@begin_end()
def get_hosts(ctx: Context) -> t.Union[t.Sequence[str], None]:
    """
    Validate and return a list of host URLs.

    Retrieves hosts from :attr:`ctx.params['hosts'] <click.Context.params>` and
    validates their URL schemas using :func:`~es_client.utils.verify_url_schema`.

    Args:
        ctx (:class:`click.Context`): Click context with host parameters.

    Returns:
        list or None: List of validated host URLs, or None if no hosts are provided.

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If URL schema validation fails.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('cmd'), params={'hosts': ['http://localhost:9200']})
        >>> hosts = get_hosts(ctx)
        >>> hosts
        ['http://localhost:9200']
    """
    hostslist = []
    if "hosts" in ctx.params and ctx.params["hosts"]:
        for host in list(ctx.params["hosts"]):
            try:
                debug.lv4('TRY: validating host URL schema')
                hostslist.append(verify_url_schema(host))
            except ConfigurationError as err:
                msg = f'Invalid URL schema: "{host}"'
                debug.lv3('Exiting function, raising exception')
                logger.error(f'{msg}, Exception: {err}')
                raise ConfigurationError(msg) from err
        retval = hostslist
    else:
        retval = None
    debug.lv5(f'Return value = {", ".join(hostslist)}')
    return retval


def get_width() -> t.Dict:
    """
    Return terminal width for click context settings.

    Returns:
        dict: Dictionary with 'max_content_width' set to terminal width from
            :func:`shutil.get_terminal_size`.

    Example:
        >>> width = get_width()
        >>> 'max_content_width' in width
        True
    """
    return {"max_content_width": get_terminal_size()[0]}


@begin_end()
def hosts_override(args: t.Dict, ctx: Context) -> t.Dict:
    """
    Remove cloud_id from config if hosts is provided via CLI.

    Args:
        args (dict): Parameters from :attr:`ctx.params <click.Context.params>`.
        ctx (:class:`click.Context`): Click command context.

    Returns:
        dict: Updated `args` with `cloud_id` removed if `hosts` is present.

    Ensures command-line `hosts` supersedes config file `cloud_id`, as they are mutually
    exclusive. Updates :attr:`ctx.obj['client_args'] <click.Context.obj>`.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('cmd'), obj={'client_args': DotMap({'cloud_id': 'my_cloud_id'})})
        >>> ctx.params = {'hosts': ['http://localhost']}
        >>> args = {'cloud_id': 'my_cloud_id'}
        >>> hosts_override(args, ctx)
        {}
        >>> ctx.obj['client_args'].cloud_id is None
        True

    If `hosts` are provided at the command-line and are present in
    :py:attr:`ctx.params['hosts'] <click.Context.params>`, but `cloud_id` was in the
    config file, we need to remove the `cloud_id` key from the configuration dictionary
    built from the YAML file before merging. Command-line provided arguments always
    supersede configuration file ones, including `hosts` overriding a file-based
    `cloud_id`.

    This function returns an updated dictionary `args` to be used for the final
    configuration as well as updates the :py:attr:`ctx.obj['client_args']
    <click.Context.obj>` object. It's simply easier to merge dictionaries using a
    separate object. It would be a pain and unnecessary to make another entry in
    :py:attr:`ctx.obj <click.Context.obj>` for this.
    """
    if "hosts" in ctx.params and ctx.params["hosts"]:
        debug.lv1("hosts from command-line superseding configuration file settings")
        ctx.obj["client_args"].hosts = None
        ctx.obj["client_args"].cloud_id = None
        args.pop("cloud_id", None)
    debug.lv5(f'Return value = {args}')
    return args


def options_from_dict(options_dict) -> t.Callable:
    """
    Decorator to add CLI options from a dictionary.

    Args:
        options_dict (dict): Dictionary of option names and their click parameters.

    Returns:
        callable: Decorator function to apply click options to a command.

    Example:
        >>> opts = {'hosts': {'settings': {'type': str, 'help': 'Hosts'}}}
        >>> @options_from_dict(opts)
        ... def cmd(hosts): pass
        >>> hasattr(cmd, '__click_params__')
        True
    """

    def decorator(func):
        for option in reversed(options_dict):
            # Shorten our "if" statements by making dct shorthand for
            # options_dict[option]
            dct = options_dict[option]
            onoff = dct["onoff"] if "onoff" in dct else None
            override = dct["override"] if "override" in dct else None
            settings = dct["settings"] if "settings" in dct else None
            if settings is None:
                settings = CLICK_SETTINGS[option]
            argval = f"--{option}"
            if isinstance(onoff, dict):
                try:
                    argval = f'--{onoff["on"]}{option}/--{onoff["off"]}{option}'
                except KeyError as exc:
                    secho(f'Error: Unable to parse --on/--off option: {exc}', bold=True)
                    raise ConfigurationError from exc
            param_decls = (argval, option.replace("-", "_"))
            attrs = override_settings(settings, override) if override else settings
            clickopt(*param_decls, **attrs)(func)
        return func

    return decorator


@begin_end()
def override_client_args(ctx: Context) -> None:
    """
    Override client_args with CLI parameters.

    Updates :attr:`ctx.obj['client_args'] <click.Context.obj>` with values from
    :attr:`ctx.params <click.Context.params>` for keys in
    :func:`~es_client.defaults.config_settings`. Sets default hosts if neither hosts nor
    cloud_id is provided.

    Args:
        ctx (:class:`click.Context`): Click context with parameters and client_args.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('cmd'), obj={'client_args': DotMap()})
        >>> ctx.params = {'hosts': ['http://127.0.0.1:9200'], 'config': None}
        >>> override_client_args(ctx)
        >>> ctx.obj['client_args'].hosts
        ['http://127.0.0.1:9200']

    Override :py:attr:`ctx.obj['client_args'] <click.Context.obj>` settings with any
        values found in :py:attr:`ctx.params <click.Context.params>`

    Update :py:attr:`ctx.obj['client_args'] <click.Context.obj>` with the results.

    In the event that there are neither ``hosts`` nor a ``cloud_id`` after the updates,
    log to debug that this is the case, and that the default value for ``hosts`` of
    ``http://127.0.0.1:9200`` will be used.
    """
    args = {}
    # Populate args from ctx.params
    for key, value in ctx.params.items():
        if key in config_settings():
            if key == "hosts":
                args[key] = get_hosts(ctx)
            elif value is not None:
                args[key] = value
    args = cloud_id_override(args, ctx)
    args = hosts_override(args, ctx)
    args = prune_nones(args)
    # Update the object if we have settings to override after pruning None values
    if args:
        for arg in args:
            debug.lv1(f'Using value for {arg} provided as a command-line option')
        ctx.obj["client_args"].update(DotMap(args))
    # Use a default hosts value of localhost:9200 if there is no host and no cloud_id
    if ctx.obj["client_args"].hosts is None and ctx.obj["client_args"].cloud_id is None:
        debug.lv1(
            "No hosts or cloud_id set! Setting default host to http://127.0.0.1:9200"
        )
        ctx.obj["client_args"].hosts = ["http://127.0.0.1:9200"]


@begin_end()
def override_other_args(ctx: Context) -> None:
    """
    Override other_args with CLI parameters.

    Updates :attr:`ctx.obj['other_args'] <click.Context.obj>` with values from
    :attr:`ctx.params <click.Context.params>` for non-client settings (e.g.,
    master_only, username, api_key).

    Args:
        ctx (:class:`click.Context`): Click context with parameters and other_args.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('cmd'), obj={'other_args': DotMap()})
        >>> ctx.params = {
            'username': 'user',
            'password': 'pass',
            'id': None,
            'api_key': None,
            'api_token': None,
            'config': None
        }
        >>> override_other_args(ctx)
        >>> ctx.obj['other_args'].username
        'user'

    Override :py:attr:`ctx.obj['other_args'] <click.Context.obj>` settings with any
    values found in :py:attr:`ctx.params <click.Context.params>`

    Update :py:attr:`ctx.obj['other_args'] <click.Context.obj>` with the results.
    """
    apikey = prune_nones(
        {
            "id": ctx.params["id"],
            "api_key": ctx.params["api_key"],
            "token": ctx.params["api_token"],
        }
    )
    args = prune_nones(
        {
            "master_only": ctx.params["master_only"],
            "skip_version_test": ctx.params["skip_version_test"],
            "username": ctx.params["username"],
            "password": ctx.params["password"],
        }
    )
    args["api_key"] = apikey

    # Remove `api_key` root key if `id` and `api_key` and `token` are all None
    if (
        ctx.params["id"] is None
        and ctx.params["api_key"] is None
        and ctx.params["api_token"] is None
    ):
        del args["api_key"]

    if args:
        for arg in args:
            debug.lv1(f'Using value for {arg} provided as a command-line option')
        ctx.obj["other_args"].update(DotMap(args))


@begin_end()
def override_settings(settings: t.Dict, override: t.Dict) -> t.Dict:
    """
    Merge override settings into a base settings dictionary.

    Args:
        settings (dict): Base settings dictionary.
        override (dict): Settings to override `settings`.

    Returns:
        dict: Updated `settings` with `override` values.

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If `override` is not a dict.

    Used by :func:`cli_opts` and :func:`options_from_dict` to customize click options.

    Example:
        >>> settings = {'type': str, 'help': 'Hosts'}
        >>> override = {'help': 'Updated Hosts'}
        >>> override_settings(settings, override)
        {'type': <class 'str'>, 'help': 'Updated Hosts'}

    This function is called by :func:`cli_opts()` in order to override settings used in
    a :py:class:`Click Option <click.Option>`.

    Click uses decorators to establish :py:class:`options <click.Option>` and
    :py:class:`arguments <click.Argument>` for a :py:class:`command <click.Command>`.
    The parameters specified for these decorator functions can be stored as default
    dictionaries, then expanded and overridden, if desired.

    In the `cli_example.py` file, the regular :py:func:`click.option decorator function
    <click.option>` is wrapped by :py:func:`option_wrapper()
    <es_client.helpers.utils.option_wrapper>`, and is aliased as ``click_opt_wrap``.
    This wrapped decorator in turn calls :func:`cli_opts()` and utilizes ``*`` arg
    expansion. :func:`cli_opts()` references defaults, and calls this function to
    override keys in `settings` with values from matching keys in `override`.

    In the example file, this looks like this:

    .. code-block:: python

      import click
      from es_client.helpers.utils import option_wrapper
      defaults.OVERRIDE = {KEY: NEWVALUE}
      click_opt_wrap = option_wrapper()

      @click.group(context_settings=context_settings())
      @click_opt_wrap(*cli_opts('OPTION1'))
      @click_opt_wrap(*cli_opts('OPTION2', settings=defaults.OVERRIDE))
      ...
      @click_opt_wrap(*cli_opts('OPTIONX'))
      @click.pass_context
      def run(ctx, OPTION1, OPTION2, ..., OPTIONX):
          # code here

    The default setting KEY of ``OPTION2`` would be overriden by NEWVALUE.
    """
    if not isinstance(override, dict):
        secho(f'Error: override must be of type dict: {type(override)}', bold=True)
        raise ConfigurationError(f"override must be of type dict: {type(override)}")
    for key in list(override.keys()):
        # This formerly checked for the presence of key in settings, but override
        # should add non-existing keys if desired.
        settings[key] = override[key]
    debug.lv5('Return value = <REDACTED>')
    return settings
