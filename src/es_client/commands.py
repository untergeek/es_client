"""
Click commands to follow the top-level
"""

import logging
import click
from es_client.helpers import config as cfg
from es_client.defaults import SHOW_EVERYTHING

# pylint: disable=R0913,R0914,W0613,W0622

# SHOW ALL OPTIONS
#
# Below is the ``show-all-options`` command which overrides the default with the values
# in the OVERRIDE constant (``hidden: False`` and ``show_env_vars: True``) which will
# reveal any hidden by default options in the top-level menu so they are exposed in the
# --help output, as well as show the environment variable name that can be used to set
# the option without a flag/argument.

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
):
    """
    ALL OPTIONS SHOWN

    The full list of options available for configuring a connection at the command-line.
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()


@click.command()
@click.pass_context
def test_connection(ctx):
    """
    Test connection to Elasticsearch
    """
    # Because of `@click.pass_context`, we can access `ctx.obj` here from the `run`
    # function that made it:

    client = cfg.get_client(configdict=ctx.obj["configdict"])

    # If we're here, we'll see the output from GET http(s)://hostname.tld:PORT
    click.secho("\nConnection result: ", bold=True)
    click.secho(f"{client.info()}\n")


@click.command()
@click.pass_context
def test_stderr(ctx):
    """
    Test STDERR logging
    """
    logger = logging.getLogger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    click.secho("\nLogging test complete.\n")
