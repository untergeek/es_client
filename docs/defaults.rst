.. _defaults:

Default Values
--------------

.. _client_configuration:

Client Configuration
====================

The :py:class:`~.esclient.Builder` class expects either a ``dict`` (`configdict`) or a YAML file
(`configfile`) of configuration settings.  Whichever is used, both must contain the top level key:
``elasticsearch``. The top level key ``logging`` is also acceptable as outlined.

This is an example of what the structure looks like with many keys present (some
contradictory, but shown for reference)::

    {
        'elasticsearch': {
            'client': {
                'hosts': ...,
                'request_timeout': ...,
                'verify_certs': ...,
                'ca_certs': ...,
                'client_cert': ...,
                'client_key': ...,
                'ssl_version': ...,
                'ssl_assert_hostname': ...,
                'ssl_assert_fingerprint': ...,
                'headers': {
                    'key1': ...,
                },
                'http_compress': ...,
            },
            'other_settings': {
                'master_only': ...,
                'skip_version_test': ...,
                'username': ...,
                'password': ...,
                'api_key': {
                    'id': ...,
                    'api_key': ...
                    'token': ...
                }
            },
        },
        'logging': {
            'loglevel': 'INFO',
            'logfile': ...,
            'logformat': 'default',
            'blacklist': ['elastic_transport', 'urllib3']
        },
    }

The next level keys are further described below.

    :client: :py:class:`dict`: `(Optional)`
    :other_settings: :py:class:`dict`: `(Optional)`

The acceptable sub-keys of **other_settings** are listed below. Anything
listed as `(Optional)` will effectively be an empty value by default, rather
than populated with the default value.

    :master_only: :py:class:`bool`: `(Optional)` Whether to execute on the elected master node or not.
        This has been used in the past to run a script (ostentibly Elasticsearch
        Curator) on every node in a cluster, but only execute if the node is the
        elected master. Not otherwise particularly useful, but preserved here due
        to its past usefulness.
    :skip_version_test: :py:class:`bool`: `(Optional)` ``es_client`` should only connect to versions
        covered. If set to ``True``, this will ignore those limitations and
        attempt to connect regardless.
    :username: :py:class:`int`: `(Optional)` If both ``username`` and ``password`` are
      provided, they will be used to create the necessary ``tuple`` for
      ``basic_auth``. An exception will be thrown if only one is provided.
    :password: :py:class:`int`: `(Optional)` If both ``username`` and ``password`` are
      provided, they will be used to create the necessary ``tuple`` for
      ``basic_auth``. An exception will be thrown if only one is provided.
    :api_key: :py:class:`dict`: `(Optional)` Can only contain the sub-keys ``token``, ``id``,
        and ``api_key``. ``token`` is the base64 encoded representation of ``id:api_key``. As
        such, if ``token`` is provided, it will override anything provided in ``id``
        and ``api_key``. If ``token`` is not provided, both ``id`` and ``api_key`` must be either
        empty/``None``, or populated with the appropriate values for the ``hosts`` or ``cloud_id``
        being connected to.

The acceptable sub-keys of **client** are described at
https://elasticsearch-py.readthedocs.io/en/latest/api.html#module-elasticsearch. Anything
listed as `(Optional)` will effectively be an empty value by default, rather
than populated with the default value.

Anything of note regarding other options is mentioned below:

    :hosts: ``list(str)``: `(Optional)` List of hosts to use for connections.
        (default: ``http://127.0.0.1:9200``)
    :cloud_id: :py:class:`int`: `(Optional)` Cloud ID as provided by Elastic Cloud or ECE.
        This is mutually exclusive of ``hosts``, and if anything but the default
        value of ``hosts`` is used in conjunction with ``cloud_id`` it will result
        in an exception and will not connect.
    :api_key: ``Tuple[str, str]``: `(Optional)` Can be a ``tuple`` or ``None``. If using the
        ``token``, or ``api_key`` subkeys of ``id`` and ``api_key`` under ``other_settings``,
        this value will be built for you automatically. Regardless, this value must be in
        ``(id, api_key)`` tuple form and not Base64 form.
    :basic_auth: ``Tuple[str, str]``: `(Optional)` Can be a ``tuple`` or ``None``. If using the
        subkeys ``username`` and ``password`` under ``other_settings``, this value
        will be built for you automatically. Replaces ``http_auth`` in older versions.
    :headers: ``Mapping[str, str]``: `(Optional)` This is a :py:class:`dict` type and should be
        mapped as multiple key/value pairs. If using YAML files, these should be each
        on its own line, e.g.: ::

            elasticsearch:
              client:
                headers:
                  key1: value1
                  key2: value2
                  ...
                  keyN: valueN

    :connections_per_node: :py:class:`int`: `(Optional)` Number of connections allowed
        per node. Replaces former ``maxsize`` parameter.
    :http_compress: :py:class:`bool`: `(Optional)` Whether to compress http traffic or not.
    :verify_certs: :py:class:`bool`: `(Optional)` Whether to verify certificates or not.
    :ca_certs: :py:class:`int`: `(Optional)` optional path to CA bundle. If using https
        scheme and ``ca_certs`` is not configured, ``es_client`` will automatically
        use ``certifi`` provided certificates.
    :client_cert: :py:class:`int`: `(Optional)` path to the file containing the private
        key and the certificate, or cert only if using ``client_key``
    :client_key: :py:class:`int`: `(Optional)` path to the file containing the private
        key if using separate cert and key files (``client_cert`` will contain
        only the cert)
    :ssl_assert_hostname: :py:class:`int`: `(Optional)` Hostname or IP address to verify
        on the node's certificate. This is useful if the certificate contains a
        different value than the one supplied in ``host``. An example of this
        situation is connecting to an IP address instead of a hostname. Set to
        ``False`` to disable certificate hostname verification.
    :ssl_assert_fingerprint: :py:class:`int`: SHA-256 fingerprint of the node's
        certificate. If this value is given then root-of-trust verification
        isn't done and only the node's certificate fingerprint is verified.

        On CPython 3.10+ this also verifies if any certificate in the chain
        including the Root CA matches this fingerprint. However because this
        requires using private APIs support for this is **experimental**.
    :ssl_version: :py:class:`int`: Minimum acceptable TLS/SSL version
    :ssl_context: :py:class:`ssl.SSLContext`: Pre-configured
        :py:class:`ssl.SSLContext` OBJECT. If this valueis given then no other
        TLS options (besides ``ssl_assert_fingerprint``) can be set on the
        :py:class:`~.elastic_transport.NodeConfig`.
    :ssl_show_warn: :py:class:`bool`: `(Optional)`
    :request_timeout: :py:class:`float`: `(Optional)` If unset, the default value from
        :py:class:`~.elasticsearch.Elasticsearch` is used,
        which is 10.0 seconds.

.. _default_values:

Constants and Settings
======================

Default values and constants shown here are used throughought the code.

.. autodata:: es_client.defaults.VERSION_MIN

.. autodata:: es_client.defaults.VERSION_MAX

.. autodata:: es_client.defaults.KEYS_TO_REDACT

.. autodata:: es_client.defaults.CLIENT_SETTINGS
   :annotation:

.. autodata:: es_client.defaults.OTHER_SETTINGS

.. autodata:: es_client.defaults.CLICK_SETTINGS
   :annotation:

.. autodata:: es_client.defaults.ES_DEFAULT

.. autodata:: es_client.defaults.ENV_VAR_PREFIX

.. autodata:: es_client.defaults.LOGLEVEL

.. autodata:: es_client.defaults.LOGFILE

.. autodata:: es_client.defaults.LOGFORMAT

.. autodata:: es_client.defaults.BLACKLIST

.. autodata:: es_client.defaults.LOGDEFAULTS

.. autodata:: es_client.defaults.LOGGING_SETTINGS
   :annotation:

.. autodata:: es_client.defaults.SHOW_OPTION

.. autodata:: es_client.defaults.SHOW_ENVVAR

.. autofunction:: es_client.defaults.config_logging

.. autofunction:: es_client.defaults.config_schema