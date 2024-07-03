"""Builder and associated Classes"""

import typing as t
import logging
from dotmap import DotMap  # type: ignore
from elastic_transport import ObjectApiResponse
import elasticsearch8
from es_client.helpers.schemacheck import password_filter
from es_client.defaults import VERSION_MIN, VERSION_MAX, CLIENT_SETTINGS, OTHER_SETTINGS
from es_client.exceptions import ConfigurationError, ESClientException, NotMaster
from es_client.helpers.utils import (
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

# pylint: disable=R0902


class Builder:
    """
    :param configdict: A configuration dictionary
    :param configfile: A YAML configuration file
    :param autoconnect: Connect to client automatically

    Build a client connection object out of settings from `configfile` or `configdict`.

    If neither `configfile` nor `configdict` is provided, empty defaults will be used.

    If both are provided, `configdict` will be used, and `configfile` ignored.
    """

    def __init__(
        self,
        configdict: t.Union[t.Dict, None] = None,
        configfile: t.Union[str, None] = None,
        autoconnect: bool = False,
    ):
        #: The DotMap storage for attributes and settings
        self.attributes = DotMap()
        self.set_client_defaults()
        self.set_other_defaults()
        #: The :py:class:`~.elasticsearch.Elasticsearch` client connection object
        self.client = elasticsearch8.Elasticsearch(hosts="http://127.0.0.1:9200")
        self.process_config_opts(configdict, configfile)
        self.version_max = VERSION_MAX
        self.version_min = VERSION_MIN
        self.update_config()
        self.validate()
        if autoconnect:
            self.connect()
            self.test_connection()

    @property
    def master_only(self) -> bool:
        """Only allow connection to the elected master, if ``True``

        :getter: Get the "Only use the elected master?" state
        :setter: Set the "Only use the elected master?" state
        :type: bool
        """
        return self.attributes.master_only

    @master_only.setter
    def master_only(self, value) -> None:
        self.attributes.master_only = value

    @property
    def is_master(self) -> bool:
        """Is the node we connected to the elected master?

        :getter: Get the "Are we the elected master?" state
        :setter: Set the "Are we the elected master?" state
        :type: bool
        """
        return self.attributes.is_master

    @is_master.setter
    def is_master(self, value) -> None:
        self.attributes.is_master = value

    @property
    def config(self) -> DotMap:
        """Configuration settings extracted from ``configfile`` or ``configdict``


        :getter: Get the configuration settings
        :setter: Set the configuration settings
        :type: DotMap
        """
        return self.attributes.config

    @config.setter
    def config(self, value) -> None:
        self.attributes.config = DotMap(value)

    @property
    def client_args(self) -> DotMap:
        """The storage and workspace for ``client`` settings

        :getter: Get ``client`` values
        :setter: Set ``client`` values
        :type: DotMap
        """
        return self.attributes.client_args

    @client_args.setter
    def client_args(self, value) -> None:
        self.attributes.client_args = DotMap(value)

    @property
    def other_args(self) -> DotMap:
        """The storage and workspace for ``other_settings``

        :getter: Get ``other_args`` values
        :setter: Set ``other_args`` values
        :type: DotMap
        """
        return self.attributes.other_args

    @other_args.setter
    def other_args(self, value) -> None:
        self.attributes.other_args = DotMap(value)

    @property
    def skip_version_test(self) -> bool:
        """
        :getter: Get the ``skip_version_test`` value
        :setter: Set the ``skip_version_test`` value
        :type: bool
        """
        return self.attributes.skip_version_test

    @skip_version_test.setter
    def skip_version_test(self, value: bool) -> None:
        self.attributes.skip_version_test = value

    @property
    def version_min(self) -> t.Tuple:
        """
        :getter: Get the minimum acceptable Elasticsearch version
        :setter: Set the minimum acceptable Elasticsearch version
        :type: t.Tuple
        """
        return self.attributes.version_min

    @version_min.setter
    def version_min(self, value) -> None:
        self.attributes.version_min = value

    @property
    def version_max(self) -> t.Tuple:
        """
        :getter: Get the maximum acceptable Elasticsearch version
        :setter: Set the maximum acceptable Elasticsearch version
        :type: t.Tuple
        """
        return self.attributes.version_max

    @version_max.setter
    def version_max(self, value) -> None:
        self.attributes.version_max = value

    def set_client_defaults(self) -> None:
        """Set defaults for the client_args property"""
        self.client_args = DotMap()
        for key in CLIENT_SETTINGS:
            self.client_args[key] = None

    def set_other_defaults(self) -> None:
        """Set defaults for the other_args property"""
        self.other_args = DotMap()
        for key in OTHER_SETTINGS:
            self.other_args[key] = None

    def process_config_opts(
        self, configdict: t.Union[t.Dict, None], configfile: t.Union[str, None]
    ) -> None:
        """Process whether to use a configdict or configfile"""
        if configfile:
            logger.debug("Using values from configfile: %s", configfile)
            self.config = check_config(get_yaml(configfile))
        if configdict:
            logger.debug("Using configdict values: %s", password_filter(configdict))
            self.config = check_config(configdict)
        if not configfile and not configdict:
            # Empty/Default config.
            logger.debug(
                "No configuration file or dictionary provided. Using defaults."
            )
            self.config = check_config({"client": {}, "other_settings": {}})

    def update_config(self) -> None:
        """Update object with values provided"""
        self.client_args.update(self.config.client)
        self.other_args.update(self.config.other_settings)
        self.master_only = self.other_args.master_only
        self.is_master = None  # Preset, until we populate this later
        if "skip_version_test" in self.other_args:
            self.skip_version_test = self.other_args.skip_version_test
        else:
            self.skip_version_test = False

    def validate(self) -> None:
        """Validate that what has been supplied is acceptable to attempt a connection"""
        # Configuration pre-checks
        if self.client_args.hosts is not None:
            verified_hosts = []
            self.client_args.hosts = ensure_list(self.client_args.hosts)
            for host in self.client_args.hosts:
                try:
                    verified_hosts.append(verify_url_schema(host))
                except ConfigurationError as exc:
                    logger.critical("Invalid host schema detected: %s -- %s", host, exc)
                    raise ConfigurationError(
                        f"Invalid host schema detected: {host}"
                    ) from exc
            self.client_args.hosts = verified_hosts
        self._check_basic_auth()
        self._check_api_key()
        self._check_cloud_id()
        self._check_ssl()

    def connect(self) -> None:
        """Attempt connection and do post-connection checks"""
        # Get the client
        self._get_client()
        # Post checks
        self._check_version()
        self._check_master()

    def _check_basic_auth(self) -> None:
        """Create ``basic_auth`` tuple from username and password"""
        if "username" in self.other_args or "password" in self.other_args:
            usr = self.other_args.username if "username" in self.other_args else None
            pwd = self.other_args.password if "password" in self.other_args else None
            if usr is None and pwd is None:
                pass
            elif usr is None or pwd is None:
                msg = "Must populate both username and password, or leave both empty"
                raise ConfigurationError(msg)
            else:
                self.client_args.basic_auth = (usr, pwd)

    def _check_api_key(self) -> None:
        """
        Create ``api_key`` tuple from :py:attr:`other_args` ``['api_key']`` subkeys
        ``id`` and ``api_key``

        Or if ``api_key`` subkey ``token`` is present, derive ``id`` and ``api_key``
        from ``token``
        """
        if "api_key" in self.other_args:
            # If present, token will override any value in 'id' or 'api_key'
            # pylint: disable=no-member
            if "token" in self.other_args.api_key:
                if self.other_args.api_key.token is not None:
                    (self.other_args.api_key.id, self.other_args.api_key.api_key) = (
                        parse_apikey_token(self.other_args.api_key.token)
                    )
            if "id" in self.other_args.api_key or "api_key" in self.other_args.api_key:
                api_id = (
                    self.other_args.api_key.id
                    if "id" in self.other_args.api_key
                    else None
                )
                api_key = (
                    self.other_args.api_key.api_key
                    if "api_key" in self.other_args.api_key
                    else None
                )
                if api_id is None and api_key is None:
                    self.client_args.api_key = (
                        None  # Setting this here because of DotMap
                    )
                elif api_id is None or api_key is None:
                    msg = "Must populate both id and api_key, or leave both empty"
                    raise ConfigurationError(msg)
                else:
                    self.client_args.api_key = (api_id, api_key)

    def _check_cloud_id(self) -> None:
        """Remove ``hosts`` key if ``cloud_id`` provided"""
        if "cloud_id" in self.client_args and self.client_args.cloud_id is not None:
            # We can remove the default if that's all there is
            if (
                self.client_args.hosts == ["http://127.0.0.1:9200"]
                and len(self.client_args.hosts) == 1
            ):
                self.client_args.hosts = None
            if self.client_args.hosts is not None:
                raise ConfigurationError('Cannot populate both "hosts" and "cloud_id"')

    def _check_ssl(self) -> None:
        """
        Use `certifi <https://github.com/certifi/python-certifi>`_ if using ssl
        and ``ca_certs`` has not been specified.
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
                # pylint: disable=import-outside-toplevel
                import certifi

                # Use certifi certificates via certifi.where():
                self.client_args.ca_certs = certifi.where()
            else:
                keylist = ["ca_certs", "client_cert", "client_key"]
                for key in keylist:
                    if key in self.client_args and self.client_args[key]:
                        if not file_exists(self.client_args[key]):
                            msg = f'"{key}: {self.client_args[key]}" File not found!'
                            logger.critical(msg)
                            raise ConfigurationError(msg)

    def _find_master(self) -> None:
        """Find out if we are connected to the elected master node"""
        my_node_id = list(self.client.nodes.info(node_id="_local")["nodes"])[0]
        master_node_id = self.client.cluster.state(metric="master_node")["master_node"]
        self.is_master = my_node_id == master_node_id

    def _check_master(self) -> None:
        """
        If :py:attr:`master_only` is ``True`` and we are not connected to the elected
        master node, raise :py:exc:`~es_client.exceptions.NotMaster`
        """
        if self.is_master is None:
            self._find_master()
        if self.master_only:
            msg = (
                "The master_only flag is set to True, but the client is  "
                "currently connected to a non-master node."
            )
            if "hosts" in self.client_args and isinstance(self.client_args.hosts, list):
                if len(self.client_args.hosts) > 1:
                    raise ConfigurationError(
                        f'"master_only" cannot be True if more than one host is '
                        f"specified. Hosts = {self.client_args.hosts}"
                    )
                if not self.is_master:
                    logger.info(msg)
                    raise NotMaster(msg)

    def _check_version(self) -> None:
        """
        Compare the Elasticsearch cluster version to :py:attr:`min_version` and
        :py:attr:`max_version`
        """
        v = get_version(self.client)
        if self.skip_version_test:
            logger.warning("Skipping Elasticsearch version checks")
        else:
            logger.debug("Detected version %s", ".".join(map(str, v)))
            if v >= self.version_max or v < self.version_min:
                msg = f"Elasticsearch version {'.'.join(map(str, v))} not supported"
                logger.error(msg)
                raise ESClientException(msg)

    def _get_client(self) -> None:
        """
        Instantiate the
        :py:class:`~.elasticsearch.Elasticsearch` object and populate
        :py:attr:`client`
        """
        # Eliminate any remaining "None" entries from the client arguments
        client_args = prune_nones(self.client_args.toDict())
        self.client = elasticsearch8.Elasticsearch(**client_args)

    def test_connection(self) -> ObjectApiResponse[t.Any]:
        """
        Connect and execute :meth:`Elasticsearch.info()
        <elasticsearch8.Elasticsearch.info>`
        """
        return self.client.info()
