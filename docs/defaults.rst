.. _defaults:

Default Values
--------------

The :class:`Builder <esclient.Builder>` class expects a ``raw_dict`` of
configuration settings.  This ``dict`` should only contain one top
level key: ``elasticsearch``.  This is an example of what the structure looks
like with many keys present (some contradictory, but shown for reference)::

    raw_dict = {
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
                }
            },
        },
    }

The top-level keys are further described below.

    :client: ``dict``: `(Optional)`
    :other_settings: ``dict``: `(Optional)`

The acceptable sub-keys of **other_settings** are listed below. Anything
listed as `(Optional)` will effectively be an empty value by default, rather
than populated with the default value.

    :master_only: ``bool``: `(Optional)` Whether to execute on the elected master node or not.
        This has been used in the past to run a script (ostentibly Elasticsearch
        Curator) on every node in a cluster, but only execute if the node is the
        elected master. Not otherwise particularly useful, but preserved here due
        to its past usefulness.
    :skip_version_test: ``bool``: `(Optional)` ``es_client`` should only connect to versions
        covered. If set to ``True``, this will ignore those limitations and
        attempt to connect regardless.
    :username: ``str``: `(Optional)` If both ``username`` and ``password`` are
      provided, they will be used to create the necessary ``tuple`` for
      ``basic_auth``. An exception will be thrown if only one is provided.
    :password: ``str``: `(Optional)` If both ``username`` and ``password`` are
      provided, they will be used to create the necessary ``tuple`` for
      ``basic_auth``. An exception will be thrown if only one is provided.
    :api_key: ``dict``: `(Optional)` Can only contain the sub-keys ``id`` and
        ``api_key``, and both must be either empty/``None``, or populated with
        the appropriate values for the ``hosts`` or ``cloud_id`` being connected
        to.

The acceptable sub-keys of **client** are described at
https://elasticsearch-py.readthedocs.io/en/v8.3.3/api.html#module-elasticsearch. Anything
listed as `(Optional)` will effectively be an empty value by default, rather
than populated with the default value.

Anything of note regarding other options is mentioned below:

    :hosts: ``list(str)``: `(Optional)` List of hosts to use for connections.
        (default: ``http://127.0.0.1:9200``)
    :cloud_id: ``str``: `(Optional)` Cloud ID as provided by Elastic Cloud or ECE.
        This is mutually exclusive of ``hosts``, and if anything but the default
        value of ``hosts`` is used in conjunction with ``cloud_id`` it will result
        in an exception and will not connect.
    :api_key: ``Tuple[str, str]``: `(Optional)` Can be a ``tuple`` or ``None``. If using the
        ``api_key`` subkeys of ``id`` and ``api_key`` under ``other_settings``,
        this value will be built for you automatically. Regardless, this must be in
        tuple form and not Base64 form. The :class:`Elasticsearch Client <elasticsearch8.Elasticsearch>`
        will automatically convert from the tuple to what Elasticsearch requires.
    :basic_auth: ``Tuple[str, str]``: `(Optional)` Can be a ``tuple`` or ``None``. If using the
        subkeys ``username`` and ``password`` under ``other_settings``, this value
        will be built for you automatically. Replaces ``http_auth`` in older versions.
    :headers: ``Optional Mapping[str, str]``: `(Optional)` This is a ``dict`` type and should be
        mapped as multiple key/value pairs. If using YAML files, these should be each
        on its own line, e.g.: ::

            elasticsearch:
              client:
                headers:
                  key1: value1
                  key2: value2
                  ...
                  keyN: valueN

    :connections_per_node: ``int``: `(Optional)` Number of connections allowed
        per node. Replaces former ``maxsize`` parameter.
    :http_compress: ``bool``: `(Optional)` Whether to compress http traffic or not.
    :verify_certs: ``bool``: `(Optional)` Whether to verify certificates or not.
    :ca_certs: ``str``: `(Optional)` optional path to CA bundle. If using https
        scheme and ``ca_certs`` is not configured, ``es_client`` will automatically
        use ``certifi`` provided certificates.
    :client_cert: ``str``: `(Optional)` path to the file containing the private
        key and the certificate, or cert only if using ``client_key``
    :client_key: ``str``: `(Optional)` path to the file containing the private
        key if using separate cert and key files (``client_cert`` will contain
        only the cert)
    :ssl_assert_hostname: ``str``: `(Optional)` Hostname or IP address to verify
        on the node's certificate. This is useful if the certificate contains a
        different value than the one supplied in ``host``. An example of this
        situation is connecting to an IP address instead of a hostname. Set to
        ``False`` to disable certificate hostname verification.
    :ssl_assert_fingerprint: ``str``: SHA-256 fingerprint of the node's
        certificate. If this value is given then root-of-trust verification
        isn't done and only the node's certificate fingerprint is verified.

        On CPython 3.10+ this also verifies if any certificate in the chain
        including the Root CA matches this fingerprint. However because this
        requires using private APIs support for this is **experimental**.
    :ssl_version: ``int``: Minimum acceptable TLS/SSL version
    :ssl_context: ``:class:ssl.SSLContext``: Pre-configured
        :class:`ssl.SSLContext` OBJECT. If this valueis given then no other
        TLS options (besides ``ssl_assert_fingerprint``) can be set on the
        :class:`elastic_transport.NodeConfig`.
    :ssl_show_warn: ``bool``: `(Optional)`
    :request_timeout: ``float``: `(Optional)` If unset, the default value from
        :class:`Elasticsearch Client <elasticsearch8.Elasticsearch>` is used,
        which is 10.0 seconds.
