"""Command-line configuration parsing and client builder helper functions"""

import typing as t
import logging
from shutil import get_terminal_size
from dotmap import DotMap  # type: ignore
from click import Context, secho, option as clickopt
from elasticsearch8 import Elasticsearch
from es_client.builder import Builder
from es_client.defaults import CLICK_SETTINGS, ENV_VAR_PREFIX, config_settings
from es_client.exceptions import ESClientException, ConfigurationError
from es_client.helpers.utils import (
    check_config,
    get_yaml,
    prune_nones,
    verify_url_schema,
)


def cli_opts(
    value: str,
    settings: t.Union[t.Dict, None] = None,
    onoff: t.Union[t.Dict, None] = None,
    override: t.Union[t.Dict, None] = None,
) -> t.Tuple[t.Tuple[str,], t.Dict]:
    """
    :param value: The command-line :py:class:`option <click.Option>` name. The key must
        be present in `settings`, or in :py:const:`CLICK_SETTINGS
        <es_client.defaults.CLICK_SETTINGS>`
    :param settings: A dictionary consisting of :py:class:`click.Option` names as keys,
        with each key having a dictionary consisting of :py:class:`click.Option`
        parameter names as keys, with their associated settings as the value. If
        `settings` is not provided, it will be populated by :py:const:`CLICK_SETTINGS
        <es_client.defaults.CLICK_SETTINGS>`.
    :param onoff: A dictionary consisting of the keys `on` and `off`, with values used
        to set up a `Click boolean option`_, .e.g. ``{'on': '', 'off': 'no-'}``. See
        below for examples.
    :param override: A dictionary consisting of keys in `settings` with values you wish
        to override.

    :type value: str
    :type settings: dict
    :type onoff: dict
    :type override: dict

    :rtype: Tuple
    :returns: A value suitable to use with the :py:func:`click.option` decorator,
        appearing as a tuple containing a tuple and a dictionary, e.g.

        .. code-block:: python

           (('--OPTION1',),{'key1', 'value1', ...})

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
        raise ConfigurationError(f'"settings" is not a dictionary: {type(settings)}')
    if value not in settings:
        raise ConfigurationError(f"{value} not in settings")
    argval = f"--{value}"
    if isinstance(onoff, dict):
        try:
            argval = f'--{onoff["on"]}{value}/--{onoff["off"]}{value}'
        except KeyError as exc:
            raise ConfigurationError from exc
    return (argval,), override_settings(settings[value], override)


def cloud_id_override(args: t.Dict, ctx: Context) -> t.Dict:
    """
    :param args: A dictionary built from :py:attr:`ctx.params <click.Context.params>`
        keys and values.
    :param ctx: The Click command context

    :type args: dict
    :type ctx: :py:class:`Context <click.Context>`

    :rtype: dict
    :returns: Updated version of `args`

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
    logger = logging.getLogger(__name__)
    if "cloud_id" in ctx.params and ctx.params["cloud_id"]:
        logger.debug(
            "cloud_id from command-line superseding configuration file settings"
        )
        ctx.obj["client_args"].hosts = None
        args.pop("hosts", None)
    return args


def context_settings() -> t.Dict:
    """
    :rtype: dict
    :returns: kwargs suitable to be used as Click :py:class:`Command <click.Command>`
        `context_settings` parameters.

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
    return {**get_width(), **help_options, **objdef, **prefix}


def generate_configdict(ctx: Context) -> None:
    """
    :param ctx: The Click command context

    :type ctx: :py:class:`Context <click.Context>`

    :rtype: None

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


def get_arg_objects(ctx: Context) -> None:
    """
    :param ctx: The Click command context

    :type ctx: :py:class:`Context <click.Context>`

    :rtype: None

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


def get_client(
    configdict: t.Union[t.Dict, None] = None,
    configfile: t.Union[str, None] = None,
    autoconnect: bool = False,
) -> Elasticsearch:
    """
    :param configdict: A configuration dictionary
    :param configfile: A YAML configuration file
    :param autoconnect: Connect to client automatically

    :returns: A client connection object
    :rtype: :py:class:`~.elasticsearch.Elasticsearch`

    Get an Elasticsearch Client using :py:class:`~.es_client.builder.Builder`

    Build a client connection object out of settings from `configfile` or `configdict`.

    If neither `configfile` nor `configdict` is provided, empty defaults will be used.

    If both are provided, `configdict` will be used, and `configfile` ignored.

    Raises :py:exc:`ESClientException <es_client.exceptions.ESClientException>` if
    unable to connect.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Creating client object and testing connection")

    builder = Builder(
        configdict=configdict, configfile=configfile, autoconnect=autoconnect
    )

    try:
        builder.connect()
    except Exception as exc:
        logger.critical("Unable to establish client connection to Elasticsearch!")
        logger.critical("Exception encountered: %s", exc)
        raise ESClientException from exc

    return builder.client


def get_config(ctx: Context, quiet: bool = True) -> Context:
    """
    :param ctx: The Click command context
    :param quiet: If the default configuration file is being used, suppress the
        ``STDOUT`` message indicating that.

    :type ctx: :py:class:`Context <click.Context>`
    :type quiet: bool

    :rtype: None

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


def get_hosts(ctx: Context) -> t.Union[t.Sequence[str], None]:
    """
    :param ctx: The Click command context

    :type ctx: :py:class:`Context <click.Context>`

    :returns: A list of hosts
    :rtype: list

    Return a list of hosts suitable for :py:attr:`ClientArgs.hosts
    <es_client.builder.ClientArgs>` from :py:attr:`ctx.params['hosts']
    <click.Context.params>`, validating the url schema for Elasticsearch compliance for
    each host provided.

    Raises a :py:exc:`ConfigurationError <es_client.exceptions.ConfigurationError>` if
    schema validation fails.
    """
    logger = logging.getLogger(__name__)
    hostslist = []
    if "hosts" in ctx.params and ctx.params["hosts"]:
        for host in list(ctx.params["hosts"]):
            try:
                hostslist.append(verify_url_schema(host))
            except ConfigurationError as err:
                logger.error("Incorrect URL Schema: %s", err)
                raise ConfigurationError from err
    else:
        return None
    return hostslist


def get_width() -> t.Dict:
    """
    :rtype: dict
    :returns: A dictionary suitable for use by itself as the Click
        :py:class:`Command <click.Command>` `context_settings` parameter.

    Determine terminal width by calling :py:func:`shutil.get_terminal_size`

    Return value takes the form of ``{"max_content_width": get_terminal_size()[0]}``
    """
    return {"max_content_width": get_terminal_size()[0]}


def hosts_override(args: t.Dict, ctx: Context) -> t.Dict:
    """
    :param args: A dictionary built from :py:attr:`ctx.params <click.Context.params>`
        keys and values.
    :param ctx: The Click command context

    :type args: dict
    :type ctx: :py:class:`Context <click.Context>`

    :rtype: dict
    :returns: Updated version of `args`

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
    logger = logging.getLogger(__name__)
    if "hosts" in ctx.params and ctx.params["hosts"]:
        logger.debug("hosts from command-line superseding configuration file settings")
        ctx.obj["client_args"].hosts = None
        ctx.obj["client_args"].cloud_id = None
        args.pop("cloud_id", None)
    return args


def options_from_dict(options_dict) -> t.Callable:
    """Build Click options decorators programmatically"""

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
                    raise ConfigurationError from exc
            param_decls = (argval, option.replace("-", "_"))
            attrs = override_settings(settings, override) if override else settings
            clickopt(*param_decls, **attrs)(func)
        return func

    return decorator


def override_client_args(ctx: Context) -> None:
    """
    :param ctx: The Click command context

    :type ctx: :py:class:`Context <click.Context>`

    :rtype: None

    Override :py:attr:`ctx.obj['client_args'] <click.Context.obj>` settings with any
        values found in :py:attr:`ctx.params <click.Context.params>`

    Update :py:attr:`ctx.obj['client_args'] <click.Context.obj>` with the results.

    In the event that there are neither ``hosts`` nor a ``cloud_id`` after the updates,
    log to debug that this is the case, and that the default value for ``hosts`` of
    ``http://127.0.0.1:9200`` will be used.
    """
    logger = logging.getLogger(__name__)
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
            logger.debug("Using value for %s provided as a command-line option", arg)
        ctx.obj["client_args"].update(DotMap(args))
    # Use a default hosts value of localhost:9200 if there is no host and no cloud_id
    if ctx.obj["client_args"].hosts is None and ctx.obj["client_args"].cloud_id is None:
        logger.debug(
            "No hosts or cloud_id set! Setting default host to http://127.0.0.1:9200"
        )
        ctx.obj["client_args"].hosts = ["http://127.0.0.1:9200"]


def override_other_args(ctx: Context) -> None:
    """
    :param ctx: The Click command context

    :type ctx: :py:class:`Context <click.Context>`

    :rtype: None

    Override :py:attr:`ctx.obj['other_args'] <click.Context.obj>` settings with any
    values found in :py:attr:`ctx.params <click.Context.params>`

    Update :py:attr:`ctx.obj['other_args'] <click.Context.obj>` with the results.
    """
    logger = logging.getLogger(__name__)
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
            logger.debug("Using value for %s provided as a command-line option", arg)
        ctx.obj["other_args"].update(DotMap(args))


def override_settings(settings: t.Dict, override: t.Dict) -> t.Dict:
    """
    :param settings: The source data
    :param override: The data which will override `settings`

    :type settings: dict
    :type override: dict

    :rtype: dict
    :returns: An dictionary based on `settings` updated with values from `override`

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
        raise ConfigurationError(f"override must be of type dict: {type(override)}")
    for key in list(override.keys()):
        # This formerly checked for the presence of key in settings, but override
        # should add non-existing keys if desired.
        settings[key] = override[key]
    return settings
