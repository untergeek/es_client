"""Builder and associated Classes"""
# pylint: disable=protected-access, attribute-defined-outside-init, no-member, import-error
# The import-error here is to avoid false-positives for the local import
from typing import Dict
import logging
import elasticsearch8
from es_client.defaults import VERSION_MIN, VERSION_MAX, client_settings, other_settings
from es_client.exceptions import ConfigurationError, ESClientException, NotMaster
from es_client.helpers.utils import (
    ensure_list, prune_nones, verify_ssl_paths, get_yaml, check_config, get_version,
    verify_url_schema
)

class ClientArgs(Dict):
    """
    Initialize with None values for all accepted client settings
    update_settings and asdict methods
    """
    def __init__(self):
        """Updatable object that will contain client arguments for connecting to Elasticsearch"""

        for setting in client_settings():
            setattr(self, setting, None)

    def update_settings(self, config):
        """Update individual settings from provided config dict"""
        for key in list(config.keys()):
            setattr(self, key, config[key])

    def asdict(self):
        """Return as a dictionary """
        retval = {}
        for setting in client_settings():
            retval[setting] = getattr(self, setting, None)
        return retval

class OtherArgs(Dict):
    """
    Initialize with None values for all 'other' client settings
    Return
    """
    def __init__(self):
        """Updatable object that will contain 'other' client arguments for connecting to Elasticsearch"""

        for setting in other_settings():
            setattr(self, setting, None)

    def update_settings(self, config):
        """Update individual settings from provided config dict"""
        for key in list(config.keys()):
            setattr(self, key, config[key])

    def asdict(self):
        """Return as a dictionary """
        retval = {}
        for setting in other_settings():
            retval[setting] = getattr(self, setting, None)
        return retval

class Builder():
    """
    Build a client out of settings from `configfile` or `configdict`
    If neither `configfile` nor `configdict` is provided, empty defaults will be used.
    If both are provided, `configdict` will be used, and `configfile` ignored.

    :arg configdict: See :doc:`defaults </defaults>` to find acceptable values
    :type configdict: dict
    :arg configfile: See :doc:`defaults </defaults>` to find acceptable values
    :type configfile: str
    :arg autoconnect: Connect to client automatically
    :type autoconnect: bool

    :attr client: :class:`Elasticsearch Client <elasticsearch8.Elasticsearch>` object

    :attr master_only: Check if node is elected master.

    :attr is_master: Connected to elected master?

    :attr client_args: Settings used to connect to Elasticsearch.
    :attr other_args: Settings apart from client_args (though some are used to build client_args)
    """
    def __init__(self, configdict=None, configfile=None, autoconnect=False, version_min=VERSION_MIN, version_max=VERSION_MAX):
        self.logger = logging.getLogger(__name__)
        if configfile:
            self.config = check_config(get_yaml(configfile))
        if configdict:
            self.config = check_config(configdict)
        if not configfile and not configdict:
            # Empty/Default config.
            self.config = check_config({'client': {}, 'other_settings': {}})
        self.client_args = ClientArgs()
        self.other_args = OtherArgs()
        self.version_max = version_max
        self.version_min = version_min
        self.update_config()
        self.validate()
        if autoconnect:
            self.connect()
            self.test_connection()

    def update_config(self):
        """Update object with values provided"""
        self.client_args.update_settings(self.config['client'])
        self.other_args.update_settings(self.config['other_settings'])
        self.master_only = self.other_args.master_only
        self.is_master = None # Preset, until we populate this later
        self.skip_version_test = self.other_args.skip_version_test

    def validate(self):
        """Validate that what has been supplied is acceptable to attempt a connection"""
        # Configuration pre-checks
        if self.client_args.hosts is not None:
            verified_hosts = []
            self.client_args.hosts = ensure_list(self.client_args.hosts)
            for host in self.client_args.hosts:
                try:
                    verified_hosts.append(verify_url_schema(host))
                except ConfigurationError as exc:
                    self.logger.critical('Invalid host schema detected: %s -- %s', host, exc)
                    raise ConfigurationError(f'Invalid host schema detected: {host}') from exc
            self.client_args.hosts = verified_hosts
        self._check_basic_auth()
        self._check_api_key()
        self._check_cloud_id()
        self._check_ssl()

    def connect(self):
        """Attempt connection and do post-connection checks"""
        # Get the client
        self._get_client()
        # Post checks
        self._check_version()
        self._check_master()

    def _check_basic_auth(self):
        """Create ``basic_auth`` tuple from username and password"""
        other_args = self.other_args.asdict()
        if 'username' in other_args or 'password' in other_args:
            usr = other_args['username'] if 'username' in other_args else None
            pwd = other_args['password'] if 'password' in other_args else None
            if usr is None and pwd is None:
                pass
            elif usr is None or pwd is None:
                raise ConfigurationError('Must populate both username and password, or leave both empty')
            else:
                self.client_args.basic_auth = (usr, pwd)

    def _check_api_key(self):
        """Create ``api_key`` tuple from self.other_args['api_key'] subkeys id and api_key """
        other_args = self.other_args.asdict()
        if 'api_key' in other_args:
            if 'id' or 'api_key' in other_args['api_key']:
                api_id = other_args['api_key']['id'] if 'id' in other_args['api_key'] else None
                api_key = other_args['api_key']['api_key'] if 'api_key' in other_args['api_key'] else None
                if api_id is None and api_key is None:
                    pass
                elif api_id is None or api_key is None:
                    raise ConfigurationError('Must populate both id and api_key, or leave both empty')
                else:
                    self.client_args.api_key = (api_id, api_key)

    def _check_cloud_id(self):
        """Remove ``hosts`` key if cloud_id provided"""
        if 'cloud_id' in self.client_args.asdict() and self.client_args.cloud_id is not None:
            # We can remove the default if that's all there is
            if self.client_args.hosts == ['http://127.0.0.1:9200'] and len(self.client_args.hosts) == 1:
                self.client_args.hosts = None
            else:
                raise ConfigurationError('Cannot populate both "hosts" and "cloud_id"')

    def _check_ssl(self):
        """
        Use `certifi <https://github.com/certifi/python-certifi>`_ if using ssl
        and ``ca_certs`` has not been specified.
        """
        verify_ssl_paths(self.client_args)
        client_args = self.client_args.asdict()
        if 'cloud_id' in client_args and client_args['cloud_id'] is not None:
            scheme = 'https'
        elif client_args['hosts'] == None:
            scheme = None
        else:
            scheme = client_args['hosts'][0].split(':')[0].lower()
        if scheme == 'https':
            if 'ca_certs' not in client_args or not client_args['ca_certs']:
                # Use certifi certificates via certifi.where():
                import certifi
                self.client_args.ca_certs = certifi.where()
                # This part is only for use with a compiled Curator.  It can still go there.
                    # # Try to use bundled certifi certificates
                    # if getattr(sys, 'frozen', False):
                    #     # The application is frozen (compiled)
                    #     datadir = os.path.dirname(sys.executable)
                    #     self.client_args['verify_certs'] = True
                    #     self.client_args['ca_certs'] = os.path.join(datadir, 'cacert.pem')


    def _find_master(self):
        """Find out if we are connected to the elected master node"""
        my_node_id = list(self.client.nodes.info(node_id='_local')['nodes'])[0]
        master_node_id = self.client.cluster.state(metric='master_node')['master_node']
        self.is_master = my_node_id == master_node_id

    def _check_master(self):
        """
        If ``master_only`` is `True` and we are not connected to the elected
        master node, raise :py:exc:`~es_client.exceptions.NotMaster`
        """
        if self.is_master is None:
            self._find_master()
        if self.master_only:
            msg = (
                'The master_only flag is set to True, but the client is  '
                'currently connected to a non-master node.'
            )
            if 'hosts' in self.client_args.asdict() and isinstance(self.client_args.hosts, list):
                if len(self.client_args.hosts) > 1:
                    raise ConfigurationError(
                        f'"master_only" cannot be True if more than one host is '
                        f'specified. Hosts = {self.client_args.hosts}'
                    )
                if not self.is_master:
                    self.logger.info(msg)
                    raise NotMaster(msg)

    def _check_version(self):
        """
        Compare the Elasticsearch cluster version to our acceptable versions
        """
        v = get_version(self.client)
        if self.skip_version_test:
            self.logger.warning('Skipping Elasticsearch version checks')
        else:
            self.logger.debug("Detected version %s", '.'.join(map(str,v)))
            if v >= self.version_max or v < self.version_min:
                msg = f"Elasticsearch version {'.'.join(map(str,v))} not supported"
                self.logger.error(msg)
                raise ESClientException(msg)

    def _get_client(self):
        """
        Instantiate the
        :class:`Elasticsearch Client <elasticsearch8.Elasticsearch>` object
        and populate :py:attr:`~es_client.Builder.client`
        """
        # Eliminate any remaining "None" entries from the client arguments before building
        client_args = prune_nones(self.client_args.asdict())
        self.client = elasticsearch8.Elasticsearch(**client_args)

    def test_connection(self):
        """Connect and execute :meth:`elasticsearch8.Elasticsearch.info`"""
        return self.client.info()