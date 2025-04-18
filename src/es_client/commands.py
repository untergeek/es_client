"""
Click commands for es_client CLI

This module defines command-line interface commands for es_client, using
:mod:`click` to handle options and integrate with
:class:`~es_client.builder.Builder`, :mod:`~es_client.logging`,
:mod:`~es_client.config`, and :mod:`~es_client.exceptions`. Commands include
displaying all configuration options, testing Elasticsearch connections, and
testing logging output.

Functions:
    show_all_options: Display all client configuration options and env vars.
    test_connection: Test connection to Elasticsearch.
    test_stderr: Test logging output to stderr.

.. note::
    The ``show_all_options`` command overrides default settings to reveal hidden
    options and show environment variable names, using
    :data:`~es_client.defaults.SHOW_EVERYTHING`.
"""

# pylint: disable=R0913,R0914,R0917,W0613,W0622
import logging
import click
from . import config as cfg
from .defaults import SHOW_EVERYTHING

# SHOW ALL OPTIONS
#
# Below is the ``show-all-options`` command which overrides the default with the values
# in the OVERRIDE constant (``hidden: False`` and ``show_env_vars: True``) which will
# reveal any hidden by default options in the top-level menu so they are exposed in the
# --help output, as well as show the environment variable name that can be used to set
# the option without a flag/argument.
#
# The below options are all included automatically by the decorator:
#
# ``@cfg.options_from_dict(SHOW_EVERYTHING)``
#
# These options require the following other includes:
#
# from es_client.defaults import LOGGING_SETTINGS, ONOFF, OVERRIDE
# from es_client.helpers.utils import option_wrapper
# click_opt_wrap = option_wrapper()
#
# @click_opt_wrap(*cli_opts('config', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('hosts', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('cloud_id', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('api_token', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('id', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('api_key', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('username', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('password', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('bearer_auth', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('opaque_id', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('request_timeout', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('http_compress', onoff=ONOFF, override=OVERRIDE))
# @click_opt_wrap(*cli_opts('verify_certs', onoff=ONOFF, override=OVERRIDE))
# @click_opt_wrap(*cli_opts('ca_certs', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('client_cert', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('client_key', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('ssl_assert_hostname', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('ssl_assert_fingerprint', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('ssl_version', override=OVERRIDE))
# @click_opt_wrap(*cli_opts('master-only', onoff=ONOFF, override=OVERRIDE))
# @click_opt_wrap(*cli_opts('skip_version_test', onoff=ONOFF, override=OVERRIDE))
# @click_opt_wrap(*cli_opts('loglevel', settings=LOGGING_SETTINGS, override=OVERRIDE))
# @click_opt_wrap(*cli_opts('logfile', settings=LOGGING_SETTINGS, override=OVERRIDE))
# @click_opt_wrap(*cli_opts('logformat', settings=LOGGING_SETTINGS, override=OVERRIDE))
# @click_opt_wrap(*cli_opts('blacklist', settings=LOGGING_SETTINGS, override=OVERRIDE))

# NOTE: Different procedure for show_all_options than other sub-commands
# Normally, for a sub-command, you would not reset the `cfg.context_settings` as we've
# done here because it also resets the context (ctx). We normally want to pass this
# along from the top level command. In this case, we want it to look like the
# root-level command for the sake of the environment variables being shown for the
# root-level and not a sub-level command.


@click.command(
    context_settings=cfg.context_settings(),
    short_help="Show all client configuration options",
)
@cfg.options_from_dict(SHOW_EVERYTHING)
@click.pass_context
def show_all_options(
    ctx,
    config,
    hosts,
    cloud_id,
    api_token,
    id,
    api_key,
    username,
    password,
    bearer_auth,
    opaque_id,
    request_timeout,
    http_compress,
    verify_certs,
    ca_certs,
    client_cert,
    client_key,
    ssl_assert_hostname,
    ssl_assert_fingerprint,
    ssl_version,
    master_only,
    skip_version_test,
    loglevel,
    logfile,
    logformat,
    blacklist,
) -> None:
    """
    Display all client configuration options and environment variables.

    Overrides defaults using :data:`~es_client.defaults.SHOW_EVERYTHING` to reveal
    hidden options and show environment variable names in the --help output.

    Args:
        ctx (:class:`click.Context`): Click context for command execution.
        config (str): Path to YAML configuration file.
        hosts (tuple): Elasticsearch host URLs.
        cloud_id (str): Elastic Cloud ID.
        api_token (str): Base64-encoded API key token.
        id (str): API key ID.
        api_key (str): API key value.
        username (str): Username for basic authentication.
        password (str): Password for basic authentication.
        bearer_auth (str): Bearer authentication token.
        opaque_id (str): Opaque ID for request tracking.
        request_timeout (float): Request timeout in seconds.
        http_compress (bool): Enable HTTP compression.
        verify_certs (bool): Verify SSL certificates.
        ca_certs (str): Path to CA certificates.
        client_cert (str): Path to client certificate.
        client_key (str): Path to client key.
        ssl_assert_hostname (str): SSL hostname to verify.
        ssl_assert_fingerprint (str): SSL certificate fingerprint.
        ssl_version (str): SSL version to use.
        master_only (bool): Connect only to the master node.
        skip_version_test (bool): Skip Elasticsearch version check.
        loglevel (str): Logging level (e.g., DEBUG, INFO).
        logfile (str): Path to log file.
        logformat (str): Log format (e.g., default, json).
        blacklist (tuple): Logger names to exclude.

    Returns:
        None: Outputs help text and exits.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('show_all_options'), obj={})
        >>> show_all_options(ctx, None, (), None, None, None, None, None, None,
        None, None, None, False, True, None, None, None, None, None, None, False,
        False, None, None, None, ())
        ... # Outputs help text and exits
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()


@click.command()
@click.pass_context
def test_connection(ctx: click.Context) -> None:
    """
    Test connection to Elasticsearch.

    Uses :func:`~es_client.config.get_client` to create a client from
    :attr:`ctx.obj['configdict'] <click.Context.obj>` and calls
    :meth:`client.info() <elasticsearch8.Elasticsearch.info>` to verify connectivity.

    Args:
        ctx (:class:`click.Context`): Click context with configuration.

    Returns:
        None: Outputs connection result to stdout.

    Raises:
        :exc:`~es_client.exceptions.ESClientException`: If connection fails.

    Example:
        >>> from click import Context, Command
        >>> from unittest.mock import Mock
        >>> ctx = Context(Command('test_connection'), obj={'configdict':
        {'elasticsearch': {'client': {'hosts': ['http://localhost:9200']},
        'other_settings': {}}}})
        >>> client = Mock()
        >>> client.info.return_value = {'version': {'number': '8.0.0'}}
        >>> cfg.get_client = Mock(return_value=client)
        >>> test_connection(ctx)
        Connection result:
        {'version': {'number': '8.0.0'}}
    """
    client = cfg.get_client(configdict=ctx.obj["configdict"])
    click.secho("\nConnection result: ", bold=True)
    click.secho(f"{client.info()}\n")


@click.command()
@click.pass_context
def test_stderr(ctx: click.Context) -> None:
    """
    Test logging output to stderr.

    Logs messages at DEBUG, INFO, WARNING, ERROR, and CRITICAL levels using
    :mod:`logging` to test stderr output configuration.

    Args:
        ctx (:class:`click.Context`): Click context (unused).

    Returns:
        None: Outputs completion message to stdout.

    Example:
        >>> from click import Context, Command
        >>> ctx = Context(Command('test_stderr'), obj={})
        >>> test_stderr(ctx)
        <BLANKLINE>
        Logging test complete.
        <BLANKLINE>
    """
    logger = logging.getLogger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    click.secho("\nLogging test complete.\n")


if __name__ == '__main__':
    click.echo("This module is not meant to be run directly.")
