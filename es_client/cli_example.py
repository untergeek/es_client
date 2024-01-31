"""Sample CLI script that will get a client using both config file and CLI args/options"""
# pylint: disable=broad-except, no-value-for-parameter, invalid-name, redefined-builtin
import click
from es_client.helpers.config import cli_opts, context_settings, get_args, get_client, get_config
from es_client.defaults import LOGGING_SETTINGS, SHOW_OPTION
from es_client.helpers.logging import configure_logging
from es_client.helpers.utils import option_wrapper, prune_nones
from es_client.version import __version__

ONOFF = {'on': '', 'off': 'no-'}
click_opt_wrap = option_wrapper()

# Be sure to add any other options or arguments either before ``config`` or after
# ``skip_version_test`` for both the decorators and the list of arguments in ``def run()``,
# preserving their order in both locations.  ``ctx`` needs to be the first arg after
# ``def run()`` as a special argument for Click, and does not need a decorator function.

# pylint: disable=unused-argument, redefined-builtin, too-many-arguments, too-many-locals, line-too-long
@click.group(context_settings=context_settings())
@click_opt_wrap(*cli_opts('config'))
@click_opt_wrap(*cli_opts('hosts'))
@click_opt_wrap(*cli_opts('cloud_id'))
@click_opt_wrap(*cli_opts('api_token'))
@click_opt_wrap(*cli_opts('id'))
@click_opt_wrap(*cli_opts('api_key'))
@click_opt_wrap(*cli_opts('username'))
@click_opt_wrap(*cli_opts('password'))
@click_opt_wrap(*cli_opts('bearer_auth'))
@click_opt_wrap(*cli_opts('opaque_id'))
@click_opt_wrap(*cli_opts('request_timeout'))
@click_opt_wrap(*cli_opts('http_compress', onoff=ONOFF))
@click_opt_wrap(*cli_opts('verify_certs', onoff=ONOFF))
@click_opt_wrap(*cli_opts('ca_certs'))
@click_opt_wrap(*cli_opts('client_cert'))
@click_opt_wrap(*cli_opts('client_key'))
@click_opt_wrap(*cli_opts('ssl_assert_hostname'))
@click_opt_wrap(*cli_opts('ssl_assert_fingerprint'))
@click_opt_wrap(*cli_opts('ssl_version'))
@click_opt_wrap(*cli_opts('master-only', onoff=ONOFF))
@click_opt_wrap(*cli_opts('skip_version_test', onoff=ONOFF))
@click_opt_wrap(*cli_opts('loglevel', settings=LOGGING_SETTINGS))
@click_opt_wrap(*cli_opts('logfile', settings=LOGGING_SETTINGS))
@click_opt_wrap(*cli_opts('logformat', settings=LOGGING_SETTINGS))
@click.version_option(__version__, '-v', '--version', prog_name="cli_example")
@click.pass_context
def run(ctx, config, hosts, cloud_id, api_token, id, api_key, username, password, bearer_auth,
    opaque_id, request_timeout, http_compress, verify_certs, ca_certs, client_cert, client_key,
    ssl_assert_hostname, ssl_assert_fingerprint, ssl_version, master_only, skip_version_test,
    loglevel, logfile, logformat
):
    """
    CLI Example (anything here will show up in --help)
    """
    # Specifying ctx.obj as an empty dictionary is useful for passing things to [sub]commands
    # as you'll see below
    ctx.obj = {}

    # If there's a default file location for client configuration, e.g. $HOME/.curator/curator.yml,
    # then you can specify it via default_config. The ``get_config`` function will return the
    # configuration derived from a YAML config file specified in command-line parameters, or if that
    # is unspecified and a default_config is provided, then use that. If neither, then a config
    # dict with no options configured is returned (assuming defaults + command-line options).
    config = get_config(ctx.params, default_config=None)

    # This is the place to configure logging, if you want to do so here.
    configure_logging(config, ctx.params)

    # The ``get_args`` function starts the chain that does all of the overriding of YAML config
    # file options by command-line specified ones.
    client_args, other_args = get_args(ctx.params, config)

    # Put the "final config" into ctx.obj, which is just a dict structure
    ctx.obj['final_config'] = {
        'elasticsearch': {
            'client': prune_nones(client_args.asdict()),
            'other_settings': prune_nones(other_args.asdict())
        }
    }

# Below is the ``show-all-options`` command, which does nothing more than set ``hidden: False`` for
# the hidden options (using the SHOW_OPTION constant) in the top-level menu so they are exposed in
# the --help output.

# pylint: disable=unused-argument, redefined-builtin, too-many-arguments, too-many-locals, line-too-long
@run.command(context_settings=context_settings(), short_help='Show all configuration options')
@click_opt_wrap(*cli_opts('config'))
@click_opt_wrap(*cli_opts('hosts'))
@click_opt_wrap(*cli_opts('cloud_id'))
@click_opt_wrap(*cli_opts('api_token'))
@click_opt_wrap(*cli_opts('id'))
@click_opt_wrap(*cli_opts('api_key'))
@click_opt_wrap(*cli_opts('username'))
@click_opt_wrap(*cli_opts('password'))
@click_opt_wrap(*cli_opts('bearer_auth', override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('opaque_id', override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('request_timeout'))
@click_opt_wrap(*cli_opts('http_compress', onoff=ONOFF, override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('verify_certs', onoff=ONOFF))
@click_opt_wrap(*cli_opts('ca_certs'))
@click_opt_wrap(*cli_opts('client_cert'))
@click_opt_wrap(*cli_opts('client_key'))
@click_opt_wrap(*cli_opts('ssl_assert_hostname', override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('ssl_assert_fingerprint', override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('ssl_version', override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('master-only', onoff=ONOFF, override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('skip_version_test', onoff=ONOFF, override=SHOW_OPTION))
@click_opt_wrap(*cli_opts('loglevel', settings=LOGGING_SETTINGS))
@click_opt_wrap(*cli_opts('logfile', settings=LOGGING_SETTINGS))
@click_opt_wrap(*cli_opts('logformat', settings=LOGGING_SETTINGS))
@click.version_option(__version__, '-v', '--version', prog_name="cli_example")
@click.pass_context
def show_all_options(ctx, config, hosts, cloud_id, api_token, id, api_key, username, password, bearer_auth,
    opaque_id, request_timeout, http_compress, verify_certs, ca_certs, client_cert, client_key,
    ssl_assert_hostname, ssl_assert_fingerprint, ssl_version, master_only, skip_version_test,
    loglevel, logfile, logformat
):
    """
    ALL OPTIONS SHOWN
    
    The full list of options available for configuring a connection at the command-line.
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()

###
### Below is a way to run a command from the main command-line page.
###

@run.command(context_settings=context_settings(), short_help='Test connection to Elasticsearch')
@click.pass_context
def test_connection(ctx):
    """
    Test connection to Elasticsearch
    """
    # Because of `@click.pass_context`, we can access `ctx.obj` here from the `run` function
    # that made it:
    es_client = get_client(configdict=ctx.obj['final_config'])

    # If we're here, we'll see the output from GET http(s)://hostname.tld:PORT
    click.secho('\nConnection result: ', bold=True)
    click.secho(f'{es_client.info()}\n')

if __name__ == '__main__':
    run()
