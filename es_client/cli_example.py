import click
from es_client.builder import ClientArgs, OtherArgs, Builder
from es_client.helpers.utils import get_yaml, check_config, prune_nones, verify_url_schema

@click.command()
@click.option('--config_file', help='Configuration settings file', type=click.Path(exists=True))
@click.option('--hosts', help='Elasticsearch URL to connect to', multiple=True)
@click.option('--cloud_id', help='Shorthand to connect to Elastic Cloud instance')
@click.option('--id', help='API Key "id" value', type=str)
@click.option('--api_key', help='API Key "api_key" value', type=str)
@click.option('--username', help='Username used to create "basic_auth" tuple')
@click.option('--password', help='Password used to create "basic_auth" tuple')
@click.option('--bearer_auth', type=str)
@click.option('--opaque_id', type=str)
@click.option('--request_timeout', help='Request timeout in seconds', type=float)
@click.option('--http_compress', help='Enable HTTP compression', is_flag=True, default=None)
@click.option('--verify_certs', help='Verify SSL/TLS certificate(s)', is_flag=True, default=None)
@click.option('--ca_certs', help='Path to CA certificate file or directory')
@click.option('--client_cert', help='Path to client certificate file')
@click.option('--client_key', help='Path to client certificate key')
@click.option('--ssl_assert_hostname', help='Hostname or IP address to verify on the node\'s certificate.', type=str)
@click.option('--ssl_assert_fingerprint', help='SHA-256 fingerprint of the node\'s certificate. If this value is given then root-of-trust verification isn\'t done and only the node\'s certificate fingerprint is verified.', type=str)
@click.option('--ssl_version', help='Minimum acceptable TLS/SSL version', type=str)
@click.option('--master-only', help='Only run if the single host provided is the elected master', is_flag=True, default=None)
@click.option('--skip_version_test', help='Do not check the host version', is_flag=True, default=None)
def run(
    config_file, hosts, cloud_id, id, api_key, username, password, bearer_auth,
    opaque_id, request_timeout, http_compress, verify_certs, ca_certs, client_cert, client_key,
    ssl_assert_hostname, ssl_assert_fingerprint, ssl_version, master_only, skip_version_test
):
    """Collect all client options and 'run'"""
    client_args = ClientArgs()
    other_args = OtherArgs()
    if config_file:
        raw_config = check_config(get_yaml(config_file))
        click.echo(f'raw_config = {raw_config}')
        client_args.update_settings(raw_config['client'])
        other_args.update_settings(raw_config['other_settings'])

    hostslist = []
    if hosts:
        for host in list(hosts):
            hostslist.append(verify_url_schema(host))
    else:
        hostslist = None

    cli_client = prune_nones({
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

    cli_other = prune_nones({
        'master_only': master_only,
        'skip_version_test': skip_version_test,
        'username': username,
        'password': password,
        'api_key': {
            'id': id,
            'api_key': api_key
        }
    })
    # Remove `api_key` root key if `id` and `api_key` are both None
    if id == None and api_key == None:
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
            'client': prune_nones(client_args.asdict()),
            'other_settings': prune_nones(other_args.asdict())
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