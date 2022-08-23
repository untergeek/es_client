import elasticsearch8
import logging
import os
from es_client.defaults import config_schema, version_min, version_max
from es_client.exceptions import ConfigurationError, ESClientException, MissingArgument, NotMaster
from es_client.helpers.schemacheck import SchemaCheck
from es_client.helpers.utils import ensure_list, prune_nones, verify_ssl_paths

class Builder():
    """
    :arg raw_config: See :doc:`defaults </defaults>` to find acceptable values
    :type raw_config: dict
    :arg autoconnect: Connect to client automatically
    :type autoconnect: bool

    :attr client: :class:`Elasticsearch Client <elasticsearch8.Elasticsearch>` object

    :attr master_only: Check if node is elected master.

    :attr is_master: Connected to elected master?

    :attr client_args: Shows what settings were used to connect to Elasticsearch.
    """
    def __init__(self, raw_config, autoconnect=True, version_min=version_min(), version_max=version_max()):
        self.logger = logging.getLogger(__name__)
        config = self._check_config(raw_config)
        self.logger.debug('CONFIG = {}'.format(config))
        self.version_max = version_max
        self.version_min = version_min
        self.other_args = config['other_settings']
        self.master_only = self.other_args['master_only']
        self.is_master = None # Preset, until we populate this later
        self.skip_version_test = self.other_args['skip_version_test']
        self.client_args = config['client']

        # Configuration pre-checks
        self.client_args['hosts'] = ensure_list(self.client_args['hosts'])
        self._check_basic_auth()
        self._check_api_key()
        self._check_cloud_id()
        self._check_ssl()
        # Eliminate any remaining "None" entries from the client arguments before building
        self.client_args = prune_nones(self.client_args)
        if autoconnect:
            # Get the client
            self._get_client()
            # Post checks
            self._check_version()
            self._check_master()

    def _check_config(self, config):
        """
        Ensure that the top-level key ``elasticsearch`` and its sub-keys, ``other_settings`` and
        ``client`` are in ``config`` before passing it to
        :class:`~es_client.helpers.schemacheck.SchemaCheck` for value validation.
        """
        if not isinstance(config, dict):
            raise ConfigurationError('Must supply dictionary.  You supplied: "{0}" which is "{1}"'.format(config, type(config)))
        if not 'elasticsearch' in config:
            self.logger.warning('No "elasticsearch" setting in supplied configuration.  Using defaults.')
            config['elasticsearch'] = {}
        else:
            config = prune_nones(config)
        for key in ['client', 'other_settings']:
            if key not in config['elasticsearch']:
                config['elasticsearch'][key] = {}
            else:
                config['elasticsearch'][key] = prune_nones(config['elasticsearch'][key])
        return SchemaCheck(config['elasticsearch'], config_schema(),
            'Elasticsearch Configuration', 'elasticsearch').result()

    def _check_basic_auth(self):
        """Create ``basic_auth`` tuple from username and password"""
        if 'username' in self.other_args or 'password' in self.other_args:
            usr = self.other_args['username'] if 'username' in self.other_args else None
            pwd = self.other_args['password'] if 'password' in self.other_args else None
            if usr is None and pwd is None:
                pass
            elif usr is None or pwd is None:
                raise ConfigurationError('Must populate both username and password, or leave both empty')
            else:
                self.client_args['basic_auth'] = (usr, pwd)

    def _check_api_key(self):
        """Create ``api_key`` tuple from self.other_args['api_key'] subkeys id and api_key """
        if 'api_key' in self.other_args:
            if 'id' or 'api_key' in self.other_args['api_key']:
                id = self.other_args['api_key']['id'] if 'id' in self.other_args['api_key'] else None
                api_key = self.other_args['api_key']['api_key'] if 'api_key' in self.other_args['api_key'] else None
                if id is None and api_key is None:
                    pass
                elif id is None or api_key is None:
                    raise ConfigurationError('Must populate both id and api_key, or leave both empty')
                else:
                    self.client_args['api_key'] = (id, api_key)

    def _check_cloud_id(self):
        """Remove ``hosts`` key if cloud_id provided"""
        if 'cloud_id' in self.client_args and self.client_args['cloud_id'] is not None:
            # We can remove the default if that's all there is
            if self.client_args['hosts'] == ['http://127.0.0.1:9200'] and len(self.client_args['hosts']) == 1:
                self.client_args.pop('hosts')
            else:
                raise ConfigurationError('Cannot populate both "hosts" and "cloud_id"')

    def _check_ssl(self):
        """
        Use `certifi <https://github.com/certifi/python-certifi>`_ if using ssl
        and ``ca_certs`` has not been specified.
        """
        verify_ssl_paths(self.client_args)
        if 'cloud_id' in self.client_args and self.client_args['cloud_id'] is not None:
            scheme = 'https'
        else:
            scheme = self.client_args['hosts'][0].split(':')[0].lower()
        if scheme == 'https':
            if 'ca_certs' not in self.client_args or not self.client_args['ca_certs']:
                # Use certifi certificates via certifi.where():
                import certifi
                self.client_args['ca_certs'] = certifi.where()
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
            if len(self.client_args['hosts']) > 1:
                raise ConfigurationError(
                    '"master_only" cannot be True if more than one host is '
                    'specified. Hosts = {0}'.format(self.client_args['hosts'])
                )
            if not self.is_master:
                msg = (
                    'The master_only flag is set to True, but the client is  '
                    'currently connected to a non-master node.'
                )
                self.logger.info(msg)
                raise NotMaster(msg)

    def _check_version(self):
        """
        Compare the Elasticsearch cluster version to our acceptable versions
        """
        v = self.get_version()
        if self.skip_version_test:
            self.logger.warning('Skipping Elasticsearch version checks')
        else:
            self.logger.debug(
                'Detected version {0}'.format('.'.join(map(str,v)))
            )
            if v >= self.version_max or v < self.version_min:
                msg = 'Elasticsearch version {0} not supported'.format('.'.join(map(str,v)))
                self.logger.error(msg)
                raise ESClientException(msg)

    def _get_client(self):
        """
        Instantiate the
        :class:`Elasticsearch Client <elasticsearch8.Elasticsearch>` object
        and populate :py:attr:`~es_client.Builder.client`
        """
        self.logger.debug('CLIENT ARGS = {}'.format(self.client_args))
        self.client = elasticsearch8.Elasticsearch(**self.client_args)

    def get_version(self):
        """Get the Elasticsearch version of the connected node"""
        version = self.client.info()['version']['number']
        # Split off any -dev, -beta, or -rc tags
        version = version.split('-')[0]
        # Only take SEMVER (drop any fields over 3)
        if len(version.split('.')) > 3:
            version = version.split('.')[:-1]
        else:
            version = version.split('.')
        return tuple(map(int, version))

    def test_connection(self):
        """Connect and execute :meth:`elasticsearch8.Elasticsearch.info`"""
        return self.client.info()
