"""Define default values"""

# pylint: disable=line-too-long
import typing as t
from copy import deepcopy
from click import Choice, Path
from six import string_types  # type: ignore
from voluptuous import All, Any, Boolean, Coerce, Optional, Range, Schema

VERSION_MIN: t.Tuple = (8, 0, 0)
"""Minimum compatible Elasticsearch version"""

VERSION_MAX: t.Tuple = (8, 99, 99)
"""Maximum compatible Elasticsearch version"""

KEYS_TO_REDACT: t.Sequence[str] = [
    "password",
    "basic_auth",
    "bearer_auth",
    "api_key",
    "id",
    "opaque_id",
]
"""
When doing configuration Schema validation, redact the value from any listed dictionary
key. This only happens if logging is at DEBUG level.
"""

CLIENT_SETTINGS: t.Sequence[str] = [
    "hosts",
    "cloud_id",
    "api_key",
    "basic_auth",
    "bearer_auth",
    "opaque_id",
    "headers",
    "connections_per_node",
    "http_compress",
    "verify_certs",
    "ca_certs",
    "client_cert",
    "client_key",
    "ssl_assert_hostname",
    "ssl_assert_fingerprint",
    "ssl_version",
    "ssl_context",
    "ssl_show_warn",
    "transport_class",
    "request_timeout",
    "node_class",
    "node_pool_class",
    "randomize_nodes_in_pool",
    "node_selector_class",
    "dead_node_backoff_factor",
    "max_dead_node_backoff",
    "serializer",
    "serializers",
    "default_mimetype",
    "max_retries",
    "retry_on_status",
    "retry_on_timeout",
    "sniff_on_start",
    "sniff_before_requests",
    "sniff_on_node_failures",
    "sniff_timeout",
    "min_delay_between_sniffing",
    "sniffed_node_callback",
    "meta_header",
    "host_info_callback",
    "_transport",
]
"""
Valid argument/option names for :py:class:`~.elasticsearch8.Elasticsearch`. Too large
to show
"""

OTHER_SETTINGS: t.Sequence[str] = [
    "master_only",
    "skip_version_test",
    "username",
    "password",
    "api_key",
]
"""Valid option names for :py:class:`~.es_client.builder.Builder`'s other settings"""

CLICK_SETTINGS: t.Dict[str, t.Dict] = {
    "config": {"help": "Path to configuration file.", "type": Path(exists=True)},
    "hosts": {"help": "Elasticsearch URL to connect to.", "multiple": True},
    "cloud_id": {"help": "Elastic Cloud instance id"},
    "api_token": {"help": "The base64 encoded API Key token", "type": str},
    "id": {"help": 'API Key "id" value', "type": str},
    "api_key": {"help": 'API Key "api_key" value', "type": str},
    "username": {"help": "Elasticsearch username", "type": str},
    "password": {"help": "Elasticsearch password", "type": str},
    "bearer_auth": {"help": "Bearer authentication token", "type": str, "hidden": True},
    "opaque_id": {"help": "X-Opaque-Id HTTP header value", "type": str, "hidden": True},
    "request_timeout": {"help": "Request timeout in seconds", "type": float},
    "http_compress": {
        "help": "Enable HTTP compression",
        "default": None,
        "hidden": True,
    },
    "verify_certs": {"help": "Verify SSL/TLS certificate(s)", "default": None},
    "ca_certs": {"help": "Path to CA certificate file or directory", "type": str},
    "client_cert": {"help": "Path to client certificate file", "type": str},
    "client_key": {"help": "Path to client key file", "type": str},
    "ssl_assert_hostname": {
        "help": "Hostname or IP address to verify on the node's certificate.",
        "type": str,
        "hidden": True,
    },
    "ssl_assert_fingerprint": {
        "help": (
            "SHA-256 fingerprint of the node's certificate. If this value is given "
            "then root-of-trust verification isn't done and only the node's "
            "certificate fingerprint is verified."
        ),
        "type": str,
        "hidden": True,
    },
    "ssl_version": {
        "help": "Minimum acceptable TLS/SSL version",
        "type": str,
        "hidden": True,
    },
    "master-only": {
        "help": "Only run if the single host provided is the elected master",
        "default": None,
        "hidden": True,
    },
    "skip_version_test": {
        "help": "Elasticsearch version compatibility check",
        "default": None,
        "hidden": True,
    },
}
"""Default settings used for building :py:class:`click.Option`. Too large to show."""

ES_DEFAULT: t.Dict = {"elasticsearch": {"client": {"hosts": ["http://127.0.0.1:9200"]}}}
"""Default settings for :py:class:`~.es_client.builder.Builder`"""

ENV_VAR_PREFIX: str = "ESCLIENT"
"""Environment variable prefix"""

LOGLEVEL: None = None
"""Default loglevel"""

LOGFILE: None = None
"""Default value for logfile"""

LOGFORMAT: None = None
"""Default value for logformat"""

BLACKLIST: None = None
"""Default value for logging blacklist"""

LOGDEFAULTS: t.Dict = {
    "loglevel": LOGLEVEL,
    "logfile": LOGFILE,
    "logformat": LOGFORMAT,
    "blacklist": BLACKLIST,
}
"""All logging defaults in a single combined dictionary"""

LOGGING_SETTINGS: t.Dict[str, t.Dict] = {
    "loglevel": {
        "help": "Log level",
        "type": Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        "default": None,
    },
    "logfile": {"help": "Log file", "type": str},
    "logformat": {
        "help": "Log output format",
        "type": Choice(["default", "json", "ecs"]),
        "default": None,
    },
    "blacklist": {
        "help": "Named entities will not be logged",
        "multiple": True,
        "default": None,
        "hidden": True,
    },
}
"""
Default logging settings used for building :py:class:`click.Option`. Too large to show.
"""

SHOW_OPTION: t.Dict[str, bool] = {"hidden": False}
"""Override value to "unhide" a :py:class:`click.Option`"""

SHOW_ENVVAR: t.Dict[str, bool] = {"show_envvar": True}
"""Override value to make Click's help output show the associated environment variable
"""

OVERRIDE: t.Dict = {**SHOW_OPTION, **SHOW_ENVVAR}
"""Override value to combine these into a single constant"""

ONOFF: t.Dict[str, str] = {"on": "", "off": "no-"}
"""Default values for enable/disable click options"""

OPTION_DEFAULTS: t.Dict[str, t.Dict] = {
    "config": {},
    "hosts": {},
    "cloud_id": {},
    "api_token": {},
    "id": {},
    "api_key": {},
    "username": {},
    "password": {},
    "bearer_auth": {},
    "opaque_id": {},
    "request_timeout": {},
    "http_compress": {"onoff": ONOFF},
    "verify_certs": {"onoff": ONOFF},
    "ca_certs": {},
    "client_cert": {},
    "client_key": {},
    "ssl_assert_hostname": {},
    "ssl_assert_fingerprint": {},
    "ssl_version": {},
    "master-only": {"onoff": ONOFF},
    "skip_version_test": {"onoff": ONOFF},
    "loglevel": {"settings": LOGGING_SETTINGS["loglevel"]},
    "logfile": {"settings": LOGGING_SETTINGS["logfile"]},
    "logformat": {"settings": LOGGING_SETTINGS["logformat"]},
    "blacklist": {"settings": LOGGING_SETTINGS["blacklist"]},
}
"""Default options for iteratively building Click decorators"""


def all_on() -> t.Dict[str, t.Dict]:
    """Return default options with all overrides enabled"""
    options = deepcopy(OPTION_DEFAULTS)
    retval = {}
    # pylint: disable=consider-using-dict-items
    for option in options:
        retval[option] = options[option]
        retval[option]["override"] = OVERRIDE
    return retval


SHOW_EVERYTHING: t.Dict[str, t.Dict] = all_on()
"""Return options for iteratively building Click decorators with all overrides on"""


# Logging schema
def config_logging() -> Schema:
    """
    :returns: A validation schema of all acceptable logging configuration parameter
        names and values with defaults for unset parameters.
    :rtype: :py:class:`~.voluptuous.schema_builder.Schema`

    Logging schema with defaults:

    .. code-block:: yaml

        logging:
          loglevel: INFO
          logfile: None
          logformat: default
          blacklist: ['elastic_transport', 'urllib3']

    """
    return Schema(
        {
            Optional("loglevel", default="INFO"): Any(
                None,
                "NOTSET",
                "DEBUG",
                "INFO",
                "WARNING",
                "ERROR",
                "CRITICAL",
                All(Coerce(int), Any(0, 10, 20, 30, 40, 50)),
            ),
            Optional("logfile", default=None): Any(None, *string_types),
            Optional("logformat", default="default"): Any(
                None, All(Any(*string_types), Any("default", "json", "ecs"))
            ),
            Optional("blacklist", default=["elastic_transport", "urllib3"]): Any(
                None, list
            ),
        }
    )


# All elasticsearch client options, with a few additional arguments.
def config_schema() -> Schema:
    """
    :returns: A validation schema of all acceptable client configuration parameter
        names and values with defaults for unset parameters.
    :rtype: :py:class:`~.voluptuous.schema_builder.Schema`

    The validation schema for an :py:class:`~.elasticsearch8.Elasticsearch` client
    object with defaults
    """
    # pylint: disable=no-value-for-parameter
    return Schema(
        {
            Optional("other_settings", default={}): {
                Optional("master_only", default=False): Boolean(),
                Optional("skip_version_test", default=False): Boolean(),
                Optional("username", default=None): Any(None, *string_types),
                Optional("password", default=None): Any(None, *string_types),
                Optional("api_key", default={}): {
                    Optional("id"): Any(None, *string_types),
                    Optional("api_key"): Any(None, *string_types),
                    Optional("token"): Any(None, *string_types),
                },
            },
            Optional("client", default={}): {
                Optional("hosts", default=None): Any(None, list, *string_types),
                Optional("cloud_id", default=None): Any(None, *string_types),
                Optional("api_key"): Any(None, tuple),
                Optional("basic_auth"): Any(None, tuple),
                Optional("bearer_auth"): Any(None, *string_types),
                Optional("opaque_id"): Any(None, *string_types),
                Optional("headers"): Any(None, dict),
                Optional("connections_per_node"): Any(
                    None, All(Coerce(int), Range(min=1, max=100))
                ),
                Optional("http_compress"): Boolean(),
                Optional("verify_certs"): Boolean(),
                Optional("ca_certs"): Any(None, *string_types),
                Optional("client_cert"): Any(None, *string_types),
                Optional("client_key"): Any(None, *string_types),
                #: Hostname or IP address to verify on the node's certificate.
                #: This is useful if the certificate contains a different value
                #: than the one supplied in ``host``. An example of this situation
                #: is connecting to an IP address instead of a hostname.
                #: Set to ``False`` to disable certificate hostname verification.
                Optional("ssl_assert_hostname"): Any(None, *string_types),
                #: SHA-256 fingerprint of the node's certificate. If this value is
                #: given then root-of-trust verification isn't done and only the
                #: node's certificate fingerprint is verified.
                #:
                #: On CPython 3.10+ this also verifies if any certificate in the
                #: chain including the Root CA matches this fingerprint. However
                #: because this requires using private APIs support for this is
                #: **experimental**.
                Optional("ssl_assert_fingerprint"): Any(None, *string_types),
                Optional("ssl_version"): Any(
                    None, *string_types
                ),  # Minimum acceptable TLS/SSL version
                #: Pre-configured :class:`ssl.SSLContext` OBJECT. If this value
                #: is given then no other TLS options (besides
                #: ``ssl_assert_fingerprint``) can be set on the
                #: :class:`elastic_transport.NodeConfig`.
                Optional("ssl_context"): Any(None, *string_types),
                # Keeping this here in case someone APIs it, but otherwise it's not
                # likely to be used.
                Optional("ssl_show_warn"): Boolean(),
                Optional("transport_class"): Any(None, *string_types),
                Optional("request_timeout"): Any(
                    None, All(Coerce(float), Range(min=0.1, max=86400.0))
                ),
                # node_class: Union[str, Type[BaseNode]] = Urllib3HttpNode,
                Optional("node_class"): Any(None, *string_types),
                # node_pool_class: Type[NodePool] = NodePool,
                Optional("node_pool_class"): Any(None, *string_types),
                Optional("randomize_nodes_in_pool"): Boolean(),
                # node_selector_class: Optional[Union[str, Type[NodeSelector]]] = None,
                Optional("node_selector_class"): Any(None, *string_types),
                Optional("dead_node_backoff_factor"): Any(None, float),
                Optional("max_dead_node_backoff"): Any(None, float),
                # One of:
                # "Serializer"
                # "JsonSerializer"
                # "TextSerializer"
                # "NdjsonSerializer"
                # "CompatibilityModeJsonSerializer"
                # "CompatibilityModeNdjsonSerializer"
                # "MapboxVectorTileSerializer"
                Optional("serializer"): Any(None, *string_types),  # ???
                # :arg serializers: optional dict of serializer instances that will be
                # used for deserializing data coming from the server. (key is the
                # mimetype), e.g.: {'mimetype':'serializer'}
                # "Serializer"
                # "JsonSerializer"
                # "TextSerializer"
                # "NdjsonSerializer"
                # "CompatibilityModeJsonSerializer"
                # "CompatibilityModeNdjsonSerializer"
                # "MapboxVectorTileSerializer"
                Optional("serializers"): Any(None, dict),
                Optional("default_mimetype"): Any(None, *string_types),
                Optional("max_retries"): Any(
                    None, All(Coerce(int), Range(min=1, max=100))
                ),
                # retry_on_status: Collection[int] = (429, 502, 503, 504),
                Optional("retry_on_status"): Any(None, tuple),
                Optional("retry_on_timeout"): Boolean(),
                Optional("sniff_on_start"): Boolean(),
                Optional("sniff_before_requests"): Boolean(),
                Optional("sniff_on_node_failure"): Boolean(),
                Optional("sniff_timeout"): Any(
                    None, All(Coerce(float), Range(min=0.1, max=100.0))
                ),
                Optional("min_delay_between_sniffing"): Any(
                    None, All(Coerce(float), Range(min=1, max=100.0))
                ),
                # Optional[
                #     Callable[
                #         ["Transport", "SniffOptions"],
                #         Union[List[NodeConfig], List[NodeConfig]],
                #     ]
                # ] = None,
                Optional("sniffed_node_callback"): Any(None, *string_types),
                Optional("meta_header"): Boolean(),
                # Cannot specify both 'request_timeout' and 'timeout'
                # Optional('timeout', default=10.0): All(Coerce(float),
                #     Range(min=1, max=120)),
                # Cannot specify both 'randomize_hosts' and 'randomize_nodes_in_pool'
                # Optional('randomize_hosts', default=True): Boolean(),
                Optional("host_info_callback"): Any(
                    None, *string_types
                ),  # ??? needs the name of a callback function
                # Cannot specify both 'sniffer_timeout' and 'min_delay_between_sniffing'
                # Optional('sniffer_timeout', default=0.5): All(Coerce(float),
                #     Range(min=0.1, max=10.0)),
                # Cannot specify both 'sniff_on_connection_fail' and
                #     'sniff_on_node_failure'
                # Optional('sniff_on_connection_fail', default=False): Boolean(),
                # Optional('http_auth'): Any(None, *string_types),
                #     Favor basic_auth instead
                Optional("_transport"): Any(None, *string_types),  # ???
            },
        }
    )


def version_max() -> t.Tuple:
    """Return the max version"""
    return VERSION_MAX


def version_min() -> t.Tuple:
    """Return the min version"""
    return VERSION_MIN


def client_settings() -> t.Sequence[str]:
    """Return the client settings"""
    return CLIENT_SETTINGS


def config_settings() -> t.Sequence[str]:
    """
    Return only the client settings likely to be used in a config file or at the
    command-line.

    This means ignoring some that are valid in
    :py:class:`~.elasticsearch8.Elasticsearch` but are handled different locally.
    Namely, ``api_key`` is handled by :py:class:`~.es_client.builder.OtherArgs`.
    """
    ignore = ["api_key"]
    settings = []
    for setting in CLIENT_SETTINGS:
        if setting not in ignore:
            settings.append(setting)
    return settings


def other_settings() -> t.Sequence[str]:
    """Return the other settings"""
    return OTHER_SETTINGS
