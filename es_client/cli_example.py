"""Sample CLI script that will get a client using both config file and CLI args/options"""
# pylint: disable=broad-except, no-value-for-parameter, invalid-name, redefined-builtin
import click
from es_client.builder import ClientArgs, OtherArgs, Builder
from es_client.helpers import utils as escl

click_opt_wrap = escl.option_wrapper()

@click.command()
@click_opt_wrap(*escl.cli_opts('config'))
@click_opt_wrap(*escl.cli_opts('hosts'))
@click_opt_wrap(*escl.cli_opts('cloud_id'))
@click_opt_wrap(*escl.cli_opts('api_token'))
@click_opt_wrap(*escl.cli_opts('id'))
@click_opt_wrap(*escl.cli_opts('api_key'))
@click_opt_wrap(*escl.cli_opts('username'))
@click_opt_wrap(*escl.cli_opts('password'))
@click_opt_wrap(*escl.cli_opts('bearer_auth'))
@click_opt_wrap(*escl.cli_opts('opaque_id'))
@click_opt_wrap(*escl.cli_opts('request_timeout'))
@click_opt_wrap(*escl.cli_opts('http_compress'))
@click_opt_wrap(*escl.cli_opts('verify_certs'))
@click_opt_wrap(*escl.cli_opts('ca_certs'))
@click_opt_wrap(*escl.cli_opts('client_cert'))
@click_opt_wrap(*escl.cli_opts('client_key'))
@click_opt_wrap(*escl.cli_opts('ssl_assert_hostname'))
@click_opt_wrap(*escl.cli_opts('ssl_assert_fingerprint'))
@click_opt_wrap(*escl.cli_opts('ssl_version'))
@click_opt_wrap(*escl.cli_opts('master-only'))
@click_opt_wrap(*escl.cli_opts('skip_version_test'))
def run(ctx, config, hosts, cloud_id, api_token, id, api_key, username, password, bearer_auth,
    opaque_id, request_timeout, http_compress, verify_certs, ca_certs, client_cert, client_key,
    ssl_assert_hostname, ssl_assert_fingerprint, ssl_version, master_only, skip_version_test
):
    """
    CLI TOOL (anything here will show up in --help)
    
    Be sure to add any other options or arguments either before ``config`` or after
    ``skip_version_test`` for both the decorators and the list of arguments in ``def run()``,
    preserving their order in both locations.  ``ctx`` needs to be the first arg after
    ``def run()`` as a special argument for Click, and does not need a decorator function.
    """
    client_args = ClientArgs()
    other_args = OtherArgs()
    if config:
        from_yaml = escl.get_yaml(config)
        raw_config = escl.check_config(from_yaml)
        client_args.update_settings(raw_config['client'])
        other_args.update_settings(raw_config['other_settings'])

    hostslist = []
    if hosts:
        for host in list(hosts):
            hostslist.append(escl.verify_url_schema(host))
    else:
        hostslist = None

    cli_client = escl.prune_nones({
        'hosts': hostslist,
        'cloud_id': cloud_id,
        'bearer_auth': bearer_auth,
        'opaque_id': opaque_id,
        'request_timeout': request_timeout,
        'http_compress': http_compress,
        'verify_certs': verify_certs,
        'ca_certs': ca_certs,
        'client_cert': client_cert,
        'client_key': client_key,
        'ssl_assert_hostname': ssl_assert_hostname,
        'ssl_assert_fingerprint': ssl_assert_fingerprint,
        'ssl_version': ssl_version
    })

    cli_other = escl.prune_nones({
        'master_only': master_only,
        'skip_version_test': skip_version_test,
        'username': username,
        'password': password,
        'api_key': {
            'id': id,
            'api_key': api_key,
            'token': api_token,
        }
    })
    # Remove `api_key` root key if `id` and `api_key` and `token` are all None
    if id is None and api_key is None and api_token is None:
        del cli_other['api_key']

    # If hosts are in the config file, but cloud_id is specified at the command-line,
    # we need to remove the hosts parameter as cloud_id and hosts are mutually exclusive
    if cloud_id:
        click.echo('cloud_id provided at CLI, superseding any other configured hosts')
        client_args.hosts = None
        cli_client.pop('hosts', None)

    # Likewise, if hosts are provided at the command-line, but cloud_id was in the config file,
    # we need to remove the cloud_id parameter from the config file-based dictionary before merging
    if hosts:
        click.echo('hosts specified manually, superseding any other cloud_id or hosts')
        client_args.hosts = None
        client_args.cloud_id = None
        cli_client.pop('cloud_id', None)

    # Update the objects if we have settings after pruning None values
    if cli_client:
        client_args.update_settings(cli_client)
    if cli_other:
        other_args.update_settings(cli_other)

    # Build a "final_config" that reflects CLI args overriding anything from a config_file
    final_config = {
        'elasticsearch': {
            'client': escl.prune_nones(client_args.asdict()),
            'other_settings': escl.prune_nones(other_args.asdict())
        }
    }

    # click.echo(f'final_config = {final_config}')

    builder = Builder(configdict=final_config)

    try:
        builder.connect()
    except Exception as exc:
        click.echo(f'Exception encountered: {exc}')

    es_client = builder.client

    # If we're here, we'll see the output from GET http(s)://hostname.tld:PORT
    click.echo(f'Connection result: {es_client.info()}')

if __name__ == '__main__':
    run()
