import elasticsearch
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

    :attr client: :class:`Elasticsearch Client <elasticsearch.Elasticsearch>`
      object

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
        self.master_only = config['master_only']
        self.is_master = None # Preset, until we populate this later
        self.skip_version_test = config['skip_version_test']
        if 'aws' in config and len(config['aws']) > 0:
            self.aws = config['aws']
            self.use_aws = config['aws']['sign_requests']
        else:
            self.use_aws = False
        self.client_args = config['client']
        # Configuration pre-checks
        self._fix_url_prefix()
        self.client_args['hosts'] = ensure_list(self.client_args['hosts'])
        self._check_http_auth()
        self._check_ssl()
        self._parse_aws()
        if autoconnect:
            # Get the client
            self._get_client()
            # Post checks
            self._check_version()
            self._check_master()

    def _check_config(self, config):
        """
        Ensure that the top-level key ``elasticsearch`` and its sub-keys, ``aws``
        and ``client`` are in ``config`` before passing it to 
        :class:`~es_client.helpers.schemacheck.SchemaCheck` for value validation.
        """
        if not isinstance(config, dict):
            raise ConfigurationError('Must supply dictionary.  You supplied: "{0}" which is "{1}"'.format(config, type(config)))
        if not 'elasticsearch' in config:
            self.logger.warn('No "elasticsearch" setting in supplied configuration.  Using defaults.')
            config['elasticsearch'] = {}
        else:
            config = prune_nones(config)
        for key in ['client', 'aws']:
            if key not in config['elasticsearch']:
                config['elasticsearch'][key] = {}
            else:
                config['elasticsearch'][key] = prune_nones(config['elasticsearch'][key])
        return SchemaCheck(config['elasticsearch'], config_schema(),
            'Elasticsearch Configuration', 'elasticsearch').result()        

    def _fix_url_prefix(self):
        """Convert ``url_prefix`` to an empty string if `None`"""
        if 'url_prefix' in self.client_args:
            if (
                    type(self.client_args['url_prefix']) == type(None) or
                    self.client_args['url_prefix'] == "None"
                ):
                self.client_args['url_prefix'] = ''

    def _check_http_auth(self):
        """Create ``http_auth`` tuple from username and password"""
        if 'username' in self.client_args or 'password' in self.client_args:
            u = self.client_args.pop('username') if 'username' in self.client_args else None
            p = self.client_args.pop('password') if 'password' in self.client_args else None
            if u is None and p is None:
                pass
            elif u is None or p is None:
                raise ConfigurationError('Must populate both username and password, or leave both empty')
            else:
                self.client_args['http_auth'] = (u, p)


    def _check_ssl(self):
        """
        Use `certifi <https://github.com/certifi/python-certifi>`_ if using ssl
        and ``ca_certs`` has not been specified.
        """
        verify_ssl_paths(self.client_args)
        if self.client_args['use_ssl'] and not self.use_aws:
            if 'ca_certs' not in self.client_args or not self.client_args['ca_certs']:
                # Use certifi certificates via certifi.where():
                import certifi
                self.client_args['verify_certs'] = True
                self.client_args['ca_certs'] = certifi.where()
                # This part is only for use with a compiled Curator.  It can still go there.
                    # # Try to use bundled certifi certificates
                    # if getattr(sys, 'frozen', False):
                    #     # The application is frozen (compiled)
                    #     datadir = os.path.dirname(sys.executable)
                    #     self.client_args['verify_certs'] = True
                    #     self.client_args['ca_certs'] = os.path.join(datadir, 'cacert.pem')

    def _parse_aws(self):
        """
        Parse the AWS args and attempt to obtain credentials using
        :class:`boto3.session.Session`, which follows the AWS documentation at
        http://amzn.to/2fRCGCt
        """
        self.logger.debug('self.aws = {}'.format(self.aws))
        self.logger.debug('self.client_args = {}'.format(self.client_args))
        if self.use_aws:
            if not 'aws_region' in self.aws or self.aws['aws_region'] is None:
                raise MissingArgument('Missing "aws_region".')
            from boto3 import session
            from botocore.exceptions import NoCredentialsError
            from requests_aws4auth import AWS4Auth
            try:
                session = session.Session()
                credentials = session.get_credentials()
                self.aws['aws_key'] = credentials.access_key
                self.aws['aws_secret_key'] = credentials.secret_key
                self.aws['aws_token'] = credentials.token
            # If an attribute doesn't exist, we were not able to retrieve credentials as expected so we can't continue
            except AttributeError:
                self.logger.debug('Unable to locate AWS credentials')
                raise NoCredentialsError
            # Override these self.client_args
            self.client_args['use_ssl'] = True
            self.client_args['verify_certs'] = True
            self.client_args['connection_class'] = elasticsearch.RequestsHttpConnection
            self.client_args['http_auth'] = (
                AWS4Auth(
                    self.aws['aws_key'], self.aws['aws_secret_key'],
                    self.aws['aws_region'], 'es', session_token=self.aws['aws_token'])
            )

    def _find_master(self):
        """Find out if we are connected to the elected master node"""
        my_node_id = list(self.client.nodes.info('_local')['nodes'])[0]
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
            self.logger.warn('Skipping Elasticsearch version checks')
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
        :class:`Elasticsearch Client <elasticsearch.Elasticsearch>` object
        and populate :py:attr:`~es_client.Builder.client`
        """
        self.logger.debug('CLIENT ARGS = {}'.format(self.client_args))
        self.client = elasticsearch.Elasticsearch(**self.client_args)

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
        """Connect and execute :meth:`elasticsearch.Elasticsearch.info`"""
        return self.client.info()
        