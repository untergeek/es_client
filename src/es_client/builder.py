"""Builder and associated Classes

This module provides the `Builder` class to construct Elasticsearch client connections
using configuration from dictionaries or YAML files.

Classes:
    Builder: Constructs an Elasticsearch client with validated configuration.
    SecretStore: Securely stores sensitive fields using Fernet encryption.
"""

# pylint: disable=C0415,R0902,R0913,R0917
import typing as t
import logging
import warnings
from dotmap import DotMap  # type: ignore
from cryptography.fernet import Fernet
import tiered_debug as debug
from elastic_transport import ObjectApiResponse
import elasticsearch8
from .debug import debug, begin_end
from .defaults import (
    VERSION_MIN,
    VERSION_MAX,
    CLIENT_SETTINGS,
    OTHER_SETTINGS,
    ES_DEFAULT,
)
from .exceptions import ConfigurationError, ESClientException, NotMaster
from .schemacheck import password_filter
from .utils import (
    check_config,
    ensure_list,
    file_exists,
    get_version,
    get_yaml,
    parse_apikey_token,
    prune_nones,
    verify_ssl_paths,
    verify_url_schema,
)

logger = logging.getLogger(__name__)

# Error message constants
INVALID_HOST_SCHEMA = "Invalid host schema: {host}"
MUST_PROVIDE_BOTH_AUTH = "Must populate both username and password, or neither"
MUST_PROVIDE_BOTH_API_KEY = "Must populate both id and api_key, or neither"
HOSTS_AND_CLOUD_ID_CONFLICT = 'Cannot populate both "hosts" and "cloud_id"'
MULTIPLE_HOSTS_MASTER_ONLY = (
    '"master_only" cannot be True if multiple hosts are specified. Hosts = {hosts}'
)
NOT_MASTER_NODE = (
    "master_only is True, but the client is connected to a non-master node."
)
UNSUPPORTED_VERSION = "Elasticsearch version {version} not supported"
FILE_NOT_FOUND = '"{key}: {path}" File not found!'


class SecretStore:
    """
    Securely stores secrets using Fernet encryption.

    Args:
        key (bytes, optional): Fernet key for encryption. If None, generates a key.

    Example:
        >>> store = SecretStore()
        >>> store.store_secret("api_key", ("id", "key"))
        >>> store.get_secret("api_key")
        ('id', 'key')
    """

    def __init__(self, key: t.Optional[bytes] = None):

        self._fernet = Fernet(key or Fernet.generate_key())
        self._secrets: t.Dict[str, bytes] = {}

    def store_secret(self, name: str, value: t.Any) -> None:
        """Encrypt and store a secret."""
        import json

        serialized = json.dumps(value).encode()
        self._secrets[name] = self._fernet.encrypt(serialized)

    def get_secret(self, name: str) -> t.Any:
        """Decrypt and return a secret, or None if not found."""
        import json

        if name in self._secrets:
            decrypted = self._fernet.decrypt(self._secrets[name]).decode()
            return json.loads(decrypted)
        return None

    def __repr__(self) -> str:
        """Return a safe string representation."""
        return f"<SecretStore with {len(self._secrets)} secrets>"


class Builder:
    """
    Constructs an Elasticsearch client connection from configuration.

    The `Builder` class processes configuration from a dictionary or YAML file,
    validates it, and creates an :class:`~elasticsearch8.Elasticsearch` client.
    It supports automatic connection and version checking, with options for
    master-only connections. Sensitive fields are stored securely in a
    :class:`SecretStore`.

    Parameters:
        configdict (dict, optional): Configuration dictionary with an 'elasticsearch'
            key containing 'client' and 'other_settings' subkeys. Defaults to None.
        configfile (str, optional): Path to a YAML file with the same structure as
            configdict. Defaults to None.
        autoconnect (bool, optional): Connect to client automatically. Defaults
            to False.
        version_min (tuple, optional): Minimum Elasticsearch version as (major, minor,
            patch). Defaults to :const:`~es_client.defaults.VERSION_MIN`.
        version_max (tuple, optional): Maximum Elasticsearch version as
            (major, minor, patch). Defaults to :const:`~es_client.defaults.VERSION_MAX`.

    Attributes:
        attributes (DotMap): Storage for configuration and settings.
        client (:class:`~elasticsearch8.Elasticsearch`): The Elasticsearch client
            connection.
        version_min (tuple): Minimum acceptable Elasticsearch version.
        version_max (tuple): Maximum acceptable Elasticsearch version.
        _secrets (:class:`SecretStore`): Secure storage for sensitive fields.

    Raises:
        :exc:`~es_client.exceptions.ConfigurationError`: If configuration is invalid,
            such as an invalid host schema (checked during initialization).
        :exc:`~es_client.exceptions.ESClientException`: If connection to Elasticsearch
            fails.
        :exc:`~es_client.exceptions.NotMaster`: If `master_only` is True and connected
            node is not the master.

    Examples:
        >>> config = {'elasticsearch': {'client': {'hosts': ['http://localhost:9200']}}}
        >>> builder = Builder(configdict=config)
        >>> builder.client_args.hosts
        ['http://localhost:9200']
        >>> builder.master_only = True
        >>> builder.master_only
        True
        >>> cfg = {'elasticsearch': {'client': {'hosts': ['ftp://invalid']}}})
        >>> Builder(configdict=cfg)
        Traceback (most recent call last):
            ...
        es_client.exceptions.ConfigurationError: Invalid host schema: ftp://invalid
    """

    def __init__(
        self,
        configdict: t.Union[t.Dict, None] = None,
        configfile: t.Union[str, None] = None,
        autoconnect: bool = False,
        version_min: t.Tuple = VERSION_MIN,
        version_max: t.Tuple = VERSION_MAX,
    ):
        debug.lv2('Initializing Builder object...')
        self.attributes = DotMap()
        self._secrets = SecretStore()
        self.set_client_defaults()
        self.set_other_defaults()
        self.client = elasticsearch8.Elasticsearch(hosts="http://127.0.0.1:9200")
        self.process_config_opts(configdict, configfile)
        # Validate host schemas immediately
        if self.config.client.get("hosts"):
            verified_hosts = []
            for host in ensure_list(self.config.client["hosts"]):
                try:
                    debug.lv4(f'TRY: validate host {host}')
                    verified_hosts.append(verify_url_schema(host))
                except ConfigurationError as exc:
                    logger.critical(INVALID_HOST_SCHEMA.format(host=host))
                    debug.lv3('Exiting method, raising exception')
                    debug.lv5(f'Exception = "{exc}"')
                    raise ConfigurationError(
                        INVALID_HOST_SCHEMA.format(host=host)
                    ) from exc
            self.config.client["hosts"] = verified_hosts
        self.version_max = version_max
        self.version_min = version_min
        self.update_config()
        self.validate()
        if autoconnect:
            self.connect()
            self.test_connection()
        debug.lv3('Builder object initialized')

    def __repr__(self) -> str:
        """
        Return a string representation of the Builder instance.

        Returns:
            str: A string describing the Builder's configuration and client status.

        Example:
            >>> config = {
            ...     'elasticsearch': {
            ...         'client': {
            ...             'hosts': ['http://localhost:9200'],
            ...             'cloud_id': 'my_cloud_id'
            ...         }
            ...     }
            ... }
            >>> builder = Builder(configdict=config)
            >>> repr(builder)  # doctest: +ELLIPSIS
            "Builder(hosts=['http://localhost:9200'], master_only=False,
            version_min=(8, 0, 0), cloud_id='my_cloud_id', ...)"
            >>> config = {
                'elasticsearch': {
                    'client': {'hosts': ['http://localhost:9200']}
                }
            }
            >>> builder = Builder(configdict=config)
            >>> repr(builder)  # doctest: +ELLIPSIS
            "Builder(hosts=['http://localhost:9200'], master_only=False,
            version_min=(8, 0, 0), ...)"
        """
        hosts = self.client_args.hosts or ['None']
        base = (
            f"Builder(hosts={hosts}, master_only={self.master_only}, "
            f"version_min={self.version_min}"
        )
        if self.client_args.cloud_id:
            base += f", cloud_id='{self.client_args.cloud_id}'"
        base += f", client={self.client})"
        return base

    @property
    def master_only(self) -> bool:
        """
        Get or set whether to connect only to the elected master node.

        Returns:
            bool: True if only the master node is allowed, False otherwise.

        Example:
            >>> builder = Builder()
            >>> builder.master_only = True
            >>> builder.master_only
            True
        """
        return self.attributes.master_only

    @master_only.setter
    def master_only(self, value: bool) -> None:
        self.attributes.master_only = value

    @property
    def is_master(self) -> bool:
        """
        Get or set whether the connected node is the elected master.

        Returns:
            bool: True if the connected node is the master, False otherwise.

        Example:
            >>> builder = Builder()
            >>> builder.is_master = False
            >>> builder.is_master
            False
        """
        return self.attributes.is_master

    @is_master.setter
    def is_master(self, value: bool) -> None:
        self.attributes.is_master = value

    @property
    def config(self) -> DotMap:
        """
        Get or set the configuration settings from configfile or configdict.

        Returns:
            DotMap: Configuration settings.

        Example:
            >>> config = {
            ...     'elasticsearch': {
            ...         'client': {'hosts': ['http://localhost:9200']}
            ...     }
            ... }
            >>> builder = Builder(configdict=config)
            >>> builder.config.client.hosts
            ['http://localhost:9200']
        """
        return self.attributes.config

    @config.setter
    def config(self, value: t.Dict) -> None:
        self.attributes.config = DotMap(value)

    @property
    def client_args(self) -> DotMap:
        """
        Get or set the client settings.

        Returns:
            DotMap: Client configuration settings.

        Example:
            >>> builder = Builder()
            >>> builder.client_args.hosts = ['http://localhost:9200']
            >>> builder.client_args.hosts
            ['http://localhost:9200']
        """
        return self.attributes.client_args

    @client_args.setter
    def client_args(self, value: t.Dict) -> None:
        self.attributes.client_args = DotMap(value)

    @property
    def other_args(self) -> DotMap:
        """
        Get or set the other settings.

        Returns:
            DotMap: Other configuration settings.

        Example:
            >>> builder = Builder()
            >>> builder.other_args.master_only = True
            >>> builder.other_args.master_only
            True
        """
        return self.attributes.other_args

    @other_args.setter
    def other_args(self, value: t.Dict) -> None:
        self.attributes.other_args = DotMap(value)

    @property
    def skip_version_test(self) -> bool:
        """
        Get or set whether to skip version compatibility tests.

        Returns:
            bool: True if version tests are skipped, False otherwise.

        Example:
            >>> builder = Builder()
            >>> builder.skip_version_test = True
            >>> builder.skip_version_test
            True
        """
        return self.attributes.skip_version_test

    @skip_version_test.setter
    def skip_version_test(self, value: bool) -> None:
        self.attributes.skip_version_test = value

    @property
    def version_min(self) -> t.Tuple:
        """
        Get or set the minimum acceptable Elasticsearch version.

        Returns:
            tuple: Minimum version as (major, minor, patch).

        Example:
            >>> builder = Builder()
            >>> builder.version_min
            (8, 0, 0)
        """
        return self.attributes.version_min

    @version_min.setter
    def version_min(self, value: t.Tuple) -> None:
        self.attributes.version_min = value

    @property
    def version_max(self) -> t.Tuple:
        """
        Get or set the maximum acceptable Elasticsearch version.

        Returns:
            tuple: Maximum version as (major, minor, patch).

        Example:
            >>> builder = Builder()
            >>> builder.version_max
            (8, 99, 99)
        """
        return self.attributes.version_max

    @version_max.setter
    def version_max(self, value: t.Tuple) -> None:
        self.attributes.version_max = value

    @begin_end()
    def set_client_defaults(self) -> None:
        """
        Set default values for client_args.

        Initializes client_args with None for all keys in
        :const:`~es_client.defaults.CLIENT_SETTINGS`.
        """
        self.client_args = DotMap()
        for key in CLIENT_SETTINGS:
            self.client_args[key] = None

    @begin_end()
    def set_other_defaults(self) -> None:
        """
        Set default values for other_args.

        Initializes other_args with None for all keys in
        :const:`~es_client.defaults.OTHER_SETTINGS`.
        """
        self.other_args = DotMap()
        for key in OTHER_SETTINGS:
            self.other_args[key] = None

    @begin_end()
    def process_config_opts(
        self, configdict: t.Union[t.Dict, None], configfile: t.Union[str, None]
    ) -> None:
        """
        Process configuration from configdict or configfile.

        Args:
            configdict (dict, optional): Configuration dictionary with an
                'elasticsearch' key containing 'client' and 'other_settings' subkeys.
            configfile (str, optional): Path to a YAML file with the same structure as
                configdict.

        Prioritizes configdict over configfile. If neither is provided, uses
        :const:`~es_client.defaults.ES_DEFAULT`, which sets hosts to
        'http://127.0.0.1:9200'.

        Example:
            >>> builder = Builder()
            >>> builder.config.client.hosts
            ['http://127.0.0.1:9200']
        """
        if configfile:
            debug.lv2(f'Using values from file: {configfile}')
            self.config = check_config(get_yaml(configfile))
        elif configdict:
            debug.lv2(f'Using values from dict: {password_filter(configdict)}')
            self.config = check_config(configdict)
        else:
            debug.lv2("No configuration provided. Using ES_DEFAULT.")
            self.config = check_config(ES_DEFAULT["elasticsearch"])

    @begin_end()
    def update_config(self) -> None:
        """
        Update object with configuration values.

        Applies settings from config to client_args and other_args, moves sensitive
        fields to a secure store, and sets master_only and skip_version_test.
        """
        self.client_args.update(self.config.client)
        self.other_args.update(self.config.other_settings)
        # Move sensitive fields to SecretStore
        sensitive_fields = ['basic_auth', 'api_key', 'bearer_auth']
        for field in sensitive_fields:
            # We are checking in client_args in case someone has manually passed
            # something. We build basic_auth from user/pass, and api_key comes
            # from self.other_args. In other words, this is a failsafe.
            if field in self.client_args and self.client_args[field] is not None:
                self._secrets.store_secret(field, self.client_args[field])
                self.client_args[field] = None
                self.config.client[field] = None
        if 'password' in self.other_args and self.other_args.password is not None:
            self._secrets.store_secret('password', self.other_args.password)
            self.other_args.password = None
            self.config.other_settings.password = None
        self.master_only = self.other_args.master_only
        self.is_master = False
        if "skip_version_test" in self.other_args:
            self.skip_version_test = self.other_args.skip_version_test
        else:
            self.skip_version_test = False

    @begin_end()
    def validate(self) -> None:
        """
        Validate configuration settings.

        Checks basic auth, API key, cloud ID, and SSL settings. Host schemas are
        validated in :meth:`__init__` using :func:`~es_client.utils.verify_url_schema`.
        Issues warnings for experimental options like ssl_version.

        Raises:
            :exc:`~es_client.exceptions.ConfigurationError`: If validation fails, such
                as missing authentication credentials or invalid cloud ID.

        Example:
            >>> config = {'elasticsearch': {'client': {'ssl_version': 'TLSv1'}}}
            >>> builder = Builder(configdict=config)  # doctest: +ELLIPSIS
            ... # Warning: ssl_version is experimental; use ssl_context instead
        """
        if self.client_args.ssl_version:
            warnings.warn(
                "ssl_version is experimental; use ssl_context instead",
                DeprecationWarning,
                stacklevel=2,
            )
        if self.client_args.ssl_assert_fingerprint:
            warnings.warn(
                "ssl_assert_fingerprint is experimental on CPython 3.10+; "
                "use ssl_context instead",
                DeprecationWarning,
                stacklevel=2,
            )
        self._check_basic_auth()
        self._check_api_key()
        self._check_cloud_id()
        self._check_ssl()

    @begin_end()
    def connect(self) -> None:
        """
        Establish connection to Elasticsearch.

        Performs post-connection checks for version and master status using
        :meth:`~Builder._check_version` and :meth:`~Builder._find_master`.

        Raises:
            :exc:`~es_client.exceptions.NotMaster`: If master_only is True and node is
                not master.
            :exc:`~es_client.exceptions.ESClientException`: If version is incompatible.
        """
        self._get_client()
        self._check_version()
        if self.master_only:
            self._check_multiple_hosts()
            self._find_master()
            self._check_if_master()

    @begin_end()
    def _check_basic_auth(self) -> None:
        """
        Validate and set basic authentication credentials.

        Creates basic_auth tuple from username and password if both are provided.

        Raises:
            :exc:`~es_client.exceptions.ConfigurationError`: If only one of username or
                password is provided.
        """
        if "username" in self.other_args or "password" in self.other_args:
            usr = self.other_args.username if "username" in self.other_args else None
            pwd = self._secrets.get_secret('password')
            if usr is None and pwd is None:
                pass
            elif usr is None or pwd is None:
                debug.lv3('Exiting method, raising exception')
                debug.lv5(f'Exception = "{MUST_PROVIDE_BOTH_AUTH}"')
                raise ConfigurationError(MUST_PROVIDE_BOTH_AUTH)
            else:
                self._secrets.store_secret('basic_auth', (usr, pwd))

    @begin_end()
    def _check_api_key(self) -> None:
        """
        Validate and set API key credentials.

        Processes API key from a token or id/api_key pair in other_args.api_key.
        Token takes precedence over id and api_key.

        Raises:
            :exc:`~es_client.exceptions.ConfigurationError`: If id or api_key is
                missing when required.

        Example:
            >>> builder = Builder()
            >>> builder.other_args.api_key = {'id': 'test_id', 'api_key': 'test_key'}
            >>> builder._check_api_key()
            >>> builder._secrets.get_secret('api_key')
            ('test_id', 'test_key')
        """
        if "api_key" not in self.other_args:
            return
        api_key_config = DotMap(self.other_args.api_key)
        if api_key_config.get("token"):
            api_id, api_key = parse_apikey_token(api_key_config.token)
            self._secrets.store_secret('api_key', (api_id, api_key))
            # Clean up sensitive fields from places they could still exist
            self.other_args.api_key.token = None
            self.config.other_settings.api_key.token = None
            return
        api_id = api_key_config.get("id")
        api_key = api_key_config.get("api_key")
        if api_id is None and api_key is None:
            self._secrets.store_secret('api_key', None)
        elif api_id is None or api_key is None:
            raise ConfigurationError(MUST_PROVIDE_BOTH_API_KEY)
        else:
            self._secrets.store_secret('api_key', (api_id, api_key))
            # Clean up sensitive fields from places they could still exist
            self.other_args.api_key.id = None
            self.config.other_settings.api_key.id = None
            self.other_args.api_key.api_key = None
            self.config.other_settings.api_key.api_key = None

    @begin_end()
    def _check_cloud_id(self) -> None:
        """
        Validate cloud_id configuration.

        Removes hosts if cloud_id is provided, as they are mutually exclusive.

        Raises:
            :exc:`~es_client.exceptions.ConfigurationError`: If both hosts and cloud_id
                are specified.
        """
        if "cloud_id" in self.client_args and self.client_args.cloud_id is not None:
            if (
                self.client_args.hosts == ["http://127.0.0.1:9200"]
                and len(self.client_args.hosts) == 1
            ):
                self.client_args.hosts = None
            if self.client_args.hosts is not None:
                debug.lv3('Exiting method, raising exception')
                logger.error(HOSTS_AND_CLOUD_ID_CONFLICT)
                raise ConfigurationError(HOSTS_AND_CLOUD_ID_CONFLICT)

    @begin_end()
    def _check_ssl(self) -> None:
        """
        Validate SSL configuration.

        Uses certifi for HTTPS if ca_certs is not specified. Checks file existence with
        :func:`~es_client.utils.file_exists`.

        Raises:
            :exc:`~es_client.exceptions.ConfigurationError`: If SSL certificate or key
                files are not found.
        """
        verify_ssl_paths(self.client_args)
        if "cloud_id" in self.client_args and self.client_args.cloud_id is not None:
            scheme = "https"
        elif self.client_args.hosts is None:
            scheme = None
        else:
            scheme = self.client_args.hosts[0].split(":")[0].lower()
        if scheme == "https":
            if "ca_certs" not in self.client_args or not self.client_args.ca_certs:
                import certifi

                self.client_args.ca_certs = certifi.where()
            else:
                keylist = ["ca_certs", "client_cert", "client_key"]
                for key in keylist:
                    if key in self.client_args and self.client_args[key]:
                        if not file_exists(self.client_args[key]):
                            msg = FILE_NOT_FOUND.format(
                                key=key, path=self.client_args[key]
                            )
                            logger.critical(msg)
                            debug.lv3('Exiting method, raising exception')
                            debug.lv5(f'Exception = "{msg}"')
                            raise ConfigurationError(msg)

    @begin_end()
    def _find_master(self) -> None:
        """
        Check if the connected node is the elected master.

        Sets is_master based on node ID comparison using
        :meth:`~elasticsearch8.Elasticsearch.nodes.info`.
        """
        my_node_id = list(self.client.nodes.info(node_id="_local")["nodes"])[0]
        master_node_id = self.client.cluster.state(metric="master_node")["master_node"]
        self.is_master = my_node_id == master_node_id

    @begin_end()
    def _check_multiple_hosts(self) -> None:
        """
        Validate host count for master_only setting.

        Raises:
            :exc:`~es_client.exceptions.ConfigurationError`: If master_only is True and
                multiple hosts are specified.
        """
        if "hosts" in self.client_args and isinstance(self.client_args.hosts, list):
            if len(self.client_args.hosts) > 1:
                debug.lv3('Exiting method, raising exception')
                hosts = self.client_args.hosts
                msg = MULTIPLE_HOSTS_MASTER_ONLY.format(hosts=hosts)
                logger.error(msg)
                raise ConfigurationError(msg)

    @begin_end()
    def _check_if_master(self) -> None:
        """
        Verify if connected node is the master when master_only is True.

        Raises:
            :exc:`~es_client.exceptions.NotMaster`: If connected node is not the master.
        """
        if not self.is_master:
            debug.lv3('Exiting method, raising exception')
            logger.error(NOT_MASTER_NODE)
            raise NotMaster(NOT_MASTER_NODE)

    @begin_end()
    def _check_version(self) -> None:
        """
        Verify Elasticsearch version compatibility.

        Compares cluster version against version_min and version_max using
        :func:`~es_client.utils.get_version`.

        Raises:
            :exc:`~es_client.exceptions.ESClientException`: If version is outside
                acceptable range.
        """
        v = get_version(self.client)
        if self.skip_version_test:
            logger.warning("Skipping Elasticsearch version checks")
        else:
            debug.lv2(f'Version detected: {".".join(map(str, v))}')
            if v >= self.version_max or v < self.version_min:
                msg = UNSUPPORTED_VERSION.format(version='.'.join(map(str, v)))
                debug.lv3('Exiting method, raising exception')
                logger.error(msg)
                raise ESClientException(msg)

    @begin_end()
    def _get_client(self) -> None:
        """
        Instantiate the :class:`~elasticsearch8.Elasticsearch` client.

        Creates client with pruned configuration arguments using
        :func:`~es_client.utils.prune_nones`, including sensitive fields from
        the secure store.
        """
        client_args = prune_nones(self.client_args.toDict())
        # Add sensitive fields from SecretStore
        for field in ['basic_auth', 'api_key', 'bearer_auth']:
            secret = self._secrets.get_secret(field)
            if secret is not None and field == 'basic_auth':
                client_args[field] = tuple(secret)
            elif secret is not None:
                client_args[field] = secret
        self.client = elasticsearch8.Elasticsearch(**client_args)

    @begin_end()
    def test_connection(self) -> ObjectApiResponse[t.Any]:
        """
        Test the Elasticsearch connection.

        Executes :meth:`~elasticsearch8.Elasticsearch.info` to verify connectivity.

        Returns:
            :class:`~elastic_transport.ObjectApiResponse`: Response from Elasticsearch
                info API.
        """
        retval = self.client.info()
        debug.lv5(f'Return value = "{retval}"')
        return retval
