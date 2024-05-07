"""
Sample CLI script that will get a client using both config file and CLI args/options
"""

import click
from elasticsearch8.exceptions import BadRequestError, NotFoundError
from es_client.helpers import config as cfg
from es_client.defaults import OPTION_DEFAULTS, SHOW_EVERYTHING
from es_client.helpers.logging import configure_logging

# Since this file will not be imported, we use this to squash the F401 error
__all__ = ["BadRequestError", "NotFoundError"]

# pylint: disable=E1120

# The following default options are all automatically added by the decorator:
#
# ``@cfg.options_from_dict(OPTION_DEFAULTS)``
#
# Be sure to add any other options or arguments either before or after this decorator,
# and add any added arguments in ``def run()``, preserving their order in both
# locations.  ``ctx`` needs to be the first arg after ``def run()`` as a special
# argument for Click, and does not need a decorator function.

# These options require the following other includes:
#
# from es_client.defaults import LOGGING_SETTINGS, ONOFF
# from es_client.helpers.utils import option_wrapper
# click_opt_wrap = option_wrapper()
#
# @click_opt_wrap(*cli_opts('config'))
# @click_opt_wrap(*cli_opts('hosts'))
# @click_opt_wrap(*cli_opts('cloud_id'))
# @click_opt_wrap(*cli_opts('api_token'))
# @click_opt_wrap(*cli_opts('id'))
# @click_opt_wrap(*cli_opts('api_key'))
# @click_opt_wrap(*cli_opts('username'))
# @click_opt_wrap(*cli_opts('password'))
# @click_opt_wrap(*cli_opts('bearer_auth'))
# @click_opt_wrap(*cli_opts('opaque_id'))
# @click_opt_wrap(*cli_opts('request_timeout'))
# @click_opt_wrap(*cli_opts('http_compress', onoff=ONOFF))
# @click_opt_wrap(*cli_opts('verify_certs', onoff=ONOFF))
# @click_opt_wrap(*cli_opts('ca_certs'))
# @click_opt_wrap(*cli_opts('client_cert'))
# @click_opt_wrap(*cli_opts('client_key'))
# @click_opt_wrap(*cli_opts('ssl_assert_hostname'))
# @click_opt_wrap(*cli_opts('ssl_assert_fingerprint'))
# @click_opt_wrap(*cli_opts('ssl_version'))
# @click_opt_wrap(*cli_opts('master-only', onoff=ONOFF))
# @click_opt_wrap(*cli_opts('skip_version_test', onoff=ONOFF))
# @click_opt_wrap(*cli_opts('loglevel', settings=LOGGING_SETTINGS))
# @click_opt_wrap(*cli_opts('logfile', settings=LOGGING_SETTINGS))
# @click_opt_wrap(*cli_opts('logformat', settings=LOGGING_SETTINGS))
# @click_opt_wrap(*cli_opts('blacklist', settings=LOGGING_SETTINGS))


# pylint: disable=R0913,R0914,W0613,W0622


@click.group(context_settings=cfg.context_settings())
@cfg.options_from_dict(OPTION_DEFAULTS)
@click.version_option(None, "-v", "--version", prog_name="cli_example")
@click.pass_context
def run(
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
    CLI Example

    Any text added to a docstring will show up in the --help/usage output.

    Set short_help='' in @func.command() definitions for each command for terse
    descriptions in the main help/usage output, as with show_all_options() in this
    example.
    """
    # If there's a default file location for client configuration, e.g.
    # $HOME/.curator/curator.yml, then specify it here. ctx.obj is now instantiated in
    # ``helpers.config.cfg.context_settings()``
    ctx.obj["default_config"] = None

    # The ``cfg.get_config`` function will grab the configuration derived from a YAML
    # config file specified in command-line parameters, or if that is unspecified but
    # ctx.obj['default_config'] is provided, use that. If quiet=True, suppress the line
    # written to STDOUT that indicates the file at ctx.obj['default_config'] is being
    # used.
    # If neither ctx.params['config'] nor ctx.obj['default_config'] reference a YAML
    # configuration file, then a config dict with empty/default configured is
    # generated. The result is stored in ctx.obj['draftcfg']
    cfg.get_config(ctx, quiet=False)

    # Configure logging. This will use the values from command line parameters, or
    # what's now been stored in ctx.obj['draftcfg']
    configure_logging(ctx)

    # The ``cfg.generate_configdict`` function does all of the overriding of YAML
    # config file options by command-line specified ones and stores the ready-to-be-
    # used by Builder configuration in ctx.obj['configdict']
    cfg.generate_configdict(ctx)


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


@run.command(
    context_settings=cfg.context_settings(), short_help="Show all configuration options"
)
@cfg.options_from_dict(SHOW_EVERYTHING)
@click.version_option(None, "-v", "--version", prog_name="cli_example")
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


#
# Below is a way to run a command from the main command-line page. The Tutorial in the
# documentation shows how to take this example, copy it, and run your own code.
#


@run.command()
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


if __name__ == "__main__":
    run()
