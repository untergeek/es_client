from six import string_types
from voluptuous import All, Any, Boolean, Coerce, Optional, Range, Schema

VERSION_MIN=(8,0,0)
VERSION_MAX=(8,99,99)

# All elasticsearch client options, with a few additional arguments.
def config_schema():

    # pylint: disable=no-value-for-parameter
    return Schema(
        {
            Optional('other_settings', default={}): {
                Optional('master_only', default=False): Boolean(),
                Optional('skip_version_test', default=False): Boolean(),
                Optional('username', default=None): Any(None, *string_types),
                Optional('password', default=None): Any(None, *string_types),
                Optional('api_key', default={}): {
                    Optional('id'): Any(None, *string_types),
                    Optional('api_key'): Any(None, *string_types),
                }
            },
            Optional('client', default={}): {
                Optional('hosts', default='http://127.0.0.1:9200'): Any(None, list, *string_types),
                Optional('cloud_id', default=None): Any(None, *string_types),
                Optional('api_key'): Any(None, tuple),
                Optional('basic_auth'): Any(None, tuple),
                Optional('bearer_auth'): Any(None, *string_types),
                Optional('opaque_id'): Any(None, *string_types),
                Optional('headers'): Any(None, dict),
                Optional('connections_per_node'): Any(None, All(Coerce(int), Range(min=1, max=100))),
                Optional('http_compress'): Boolean(),
                Optional('verify_certs'): Boolean(),
                Optional('ca_certs'): Any(None, *string_types),
                Optional('client_cert'): Any(None, *string_types),
                Optional('client_key'): Any(None, *string_types),

                #: Hostname or IP address to verify on the node's certificate.
                #: This is useful if the certificate contains a different value
                #: than the one supplied in ``host``. An example of this situation
                #: is connecting to an IP address instead of a hostname.
                #: Set to ``False`` to disable certificate hostname verification.
                Optional('ssl_assert_hostname'): Any(None, *string_types),

                #: SHA-256 fingerprint of the node's certificate. If this value is
                #: given then root-of-trust verification isn't done and only the
                #: node's certificate fingerprint is verified.
                #:
                #: On CPython 3.10+ this also verifies if any certificate in the
                #: chain including the Root CA matches this fingerprint. However
                #: because this requires using private APIs support for this is
                #: **experimental**.
                Optional('ssl_assert_fingerprint'): Any(None, *string_types),

                Optional('ssl_version'): Any(None, *string_types), # Minimum acceptable TLS/SSL version

                #: Pre-configured :class:`ssl.SSLContext` OBJECT. If this value
                #: is given then no other TLS options (besides ``ssl_assert_fingerprint``)
                #: can be set on the :class:`elastic_transport.NodeConfig`.
                ### Keeping this here in case someone APIs it, but otherwise it's not likely to be used.
                Optional('ssl_context'): Any(None, *string_types),

                Optional('ssl_show_warn'): Boolean(),
                Optional('transport_class'): Any(None, *string_types),
                Optional('request_timeout'): Any(None, All(Coerce(float), Range(min=0.1, max=86400.0))),

                # node_class: Union[str, Type[BaseNode]] = Urllib3HttpNode,
                Optional('node_class'): Any(None, *string_types),

                # node_pool_class: Type[NodePool] = NodePool,
                Optional('node_pool_class'): Any(None, *string_types),

                Optional('randomize_nodes_in_pool'): Boolean(),

                # node_selector_class: Optional[Union[str, Type[NodeSelector]]] = None,
                Optional('node_selector_class'): Any(None, *string_types),

                Optional('dead_node_backoff_factor'): Any(None, float),
                Optional('max_dead_node_backoff'): Any(None, float),

                # One of:
                # "Serializer"
                # "JsonSerializer"
                # "TextSerializer"
                # "NdjsonSerializer"
                # "CompatibilityModeJsonSerializer"
                # "CompatibilityModeNdjsonSerializer"
                # "MapboxVectorTileSerializer"
                Optional('serializer'): Any(None, *string_types), # ???

                # :arg serializers: optional dict of serializer instances that will be
                # used for deserializing data coming from the server. (key is the mimetype)
                # e.g.: {'mimetype':'serializer'}
                # "Serializer"
                # "JsonSerializer"
                # "TextSerializer"
                # "NdjsonSerializer"
                # "CompatibilityModeJsonSerializer"
                # "CompatibilityModeNdjsonSerializer"
                # "MapboxVectorTileSerializer"
                Optional('serializers'): Any(None, dict),

                Optional('default_mimetype'): Any(None, *string_types),
                Optional('max_retries'): Any(None, All(Coerce(int), Range(min=1, max=100))),

                # retry_on_status: Collection[int] = (429, 502, 503, 504),
                Optional('retry_on_status'): Any(None, tuple),

                Optional('retry_on_timeout'): Boolean(),
                Optional('sniff_on_start'): Boolean(),
                Optional('sniff_before_requests'): Boolean(),
                Optional('sniff_on_node_failure'): Boolean(),
                Optional('sniff_timeout'): Any(None, All(Coerce(float), Range(min=0.1, max=100.0))),
                Optional('min_delay_between_sniffing'): Any(None, All(Coerce(float), Range(min=1, max=100.0))),

                # Optional[
                #     Callable[
                #         ["Transport", "SniffOptions"],
                #         Union[List[NodeConfig], List[NodeConfig]],
                #     ]
                # ] = None,
                Optional('sniffed_node_callback'): Any(None, *string_types),

                Optional('meta_header'): Boolean(),

                # Cannot specify both 'request_timeout' and 'timeout'
                # Optional('timeout', default=10.0): All(Coerce(float), Range(min=1, max=120)),

                # Cannot specify both 'randomize_hosts' and 'randomize_nodes_in_pool'
                # Optional('randomize_hosts', default=True): Boolean(),

                Optional('host_info_callback'): Any(None, *string_types), # ??? needs the name of a callback function

                # Cannot specify both 'sniffer_timeout' and 'min_delay_between_sniffing'
                # Optional('sniffer_timeout', default=0.5): All(Coerce(float), Range(min=0.1, max=10.0)),

                # Cannot specify both 'sniff_on_connection_fail' and 'sniff_on_node_failure'
                # Optional('sniff_on_connection_fail', default=False): Boolean(),

                # Optional('http_auth'): Any(None, *string_types), # ??? Favor basic_auth instead.w
                Optional('_transport'): Any(None, *string_types) # ???
            }
        }
    )



def version_max():
    return VERSION_MAX

def version_min():
    return VERSION_MIN