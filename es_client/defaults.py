from six import string_types
from voluptuous import All, Any, Boolean, Coerce, Optional, Range, Schema

VERSION_MIN=(5,0,0)
VERSION_MAX=(6,99,99)

# All elasticsearch client options, with a few additional arguments.
def config_schema():
 
    # pylint: disable=no-value-for-parameter
    return Schema(
        {
            Optional('master_only', default=False): Boolean(),
            Optional('skip_version_test', default=False): Boolean(),
            Optional('client', default={}): {
                Optional('hosts', default='127.0.0.1'): Any(None, list, *string_types),
                Optional('port', default=9200): Any(None, All(Coerce(int), Range(min=1, max=65535))),
                Optional('url_prefix'): Any(None, *string_types),
                Optional('use_ssl', default=False): Boolean(),
                Optional('ca_certs'): Any(None, *string_types),
                Optional('client_cert'): Any(None, *string_types),
                Optional('client_key'): Any(None, *string_types),
                Optional('ssl_version'): Any(None, *string_types),
                Optional('ssl_assert_hostname'): Any(None, *string_types),
                Optional('ssl_assert_fingerprint'): Any(None, *string_types),
                Optional('verify_certs', default=False): Boolean(),
                Optional('username', default=None): Any(None, *string_types),
                Optional('password', default=None): Any(None, *string_types),
                Optional('timeout', default=30): All(Coerce(int), Range(min=1, max=86400)),
                Optional('maxsize'): All(Coerce(int), Range(min=1, max=86400)),
                Optional('headers'): Any(None, *string_types),
                Optional('http_compress'): Boolean(),
            },
            Optional('aws', default={}): {
                Optional('sign_requests', default=False): Boolean(),
                Optional('aws_region'): Any(None, *string_types),
            }
        }
    )

def version_max():
    return VERSION_MAX

def version_min():
    return VERSION_MIN