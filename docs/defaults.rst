.. _defaults:

Default Values and Data Expectations
====================================

The :class:`Builder <esclient.Builder>` class expects a raw_dict of
configuration settings.  This ``dict`` should only contain one top
level key: ``elasticsearch``.  This is an example of what the structure would
look like with all accepted keys present::

    raw_dict = {
        'elasticsearch': {
            'master_only': ...,
            'skip_version_test': ...,
            'client': {
                'hosts': ...,
                'port': ...,
                'url_prefix': ...,
                'timeout': ...,
                'username': ...,
                'password': ...,
                'use_ssl': ...,
                'verify_certs': ...,
                'ca_certs': ...,
                'client_cert': ...,
                'client_key': ...,
                'ssl_version': ...,
                'ssl_assert_hostname': ...,
                'ssl_assert_fingerprint': ...,
                'maxsize': ...,
                'headers': ...,
                'http_compress': ...,
            },
            'aws': {
                'sign_requests': ...,
                'aws_region': ...,
            },
        },
    }

The top-level keys are further described below.

    :master_only: ``bool``: `(Optional)` whether the client should connect to
        only the elected master.
    :skip_version_test: ``bool``: `(Optional)` whether the client should skip
        checking for acceptable versions of Elasticsearch.
    :client: ``dict``: `(Optional)`
    :aws: ``dict``: `(Optional)`

The acceptable sub-keys of **client** are:

    :hosts: ``list(str)``: `(Optional)` List of hosts to use for connections.
        (default: ``localhost``)
    :port: ``int``: `(Optional)`  port to use (default: ``9200``)
    :url_prefix: ``str``: `(Optional)` optional url prefix for elasticsearch
    :timeout: ``int``: `(Optional)` default timeout in seconds
        (default: ``30``)
    :username: ``str``: `(Optional)` username to connect with
    :password: ``str``: `(Optional)` password to connect with
    :use_ssl: ``bool``: `(Optional)` use ssl for the connection if `True`
    :verify_certs: ``str``: `(Optional)` whether to verify SSL certificates
    :ca_certs: ``str``: `(Optional)` optional path to CA bundle. See https://urllib3.readthedocs.io/en/latest/security.html#using-certifi-with-urllib3
        for instructions how to get default set
    :client_cert: ``str``: `(Optional)` path to the file containing the private
        key and the certificate, or cert only if using ``client_key``
    :client_key: ``str``: `(Optional)` path to the file containing the private
        key if using separate cert and key files (``client_cert`` will contain
        only the cert)
    :ssl_version: ``str``: `(Optional)`  version of the SSL protocol to use.
        Choices are: ``SSLv23`` (default) ``SSLv2`` ``SSLv3`` ``TLSv1`` (see
        ``PROTOCOL_*`` constants in the `ssl` module for exact options for your
        environment).
    :ssl_assert_hostname: ``str``: `(Optional)` use hostname verification if
        not `False`
    :ssl_assert_fingerprint: ``str``: `(Optional)` verify the supplied
        certificate fingerprint if not `None`
    :maxsize: ``int``: `(Optional)` the number of connections which will be
        kept open to this host. See https://urllib3.readthedocs.io/en/1.4/pools.html#api
        for more information.
    :headers: ``str``: `(Optional)` any custom http headers to be added to
        requests
    :http_compress: ``bool``: `(Optional)` use gzip compression

The acceptable sub-keys of **aws** are:

    :sign_requests: ``bool``: `(Optional)` will connect using IAM credentials
        to connect to Elasticsearch if `True`
    :aws_region: ``str``: `(Optional)` required if ``sign_requests`` is `True`.
        Set to the ``aws_region`` your cluster is in.


