.. _builder:

Client Builder Class
====================

.. autoclass:: es_client.Builder
   :members:
   :undoc-members:
   :private-members:

Builder Attribute Errata
------------------------

:client: The :class:`Elasticsearch Client <elasticsearch.Elasticsearch>`
      object is only created after passing all other tests, and if
      ``autoconnect`` is `True`

:is_master: Initially set to `None`, this value is set automatically if
      ``autoconnect`` is `True`.  It can otherwise be set by calling
      :meth:`~es_client.Builder._find_master` after
      :meth:`~es_client.Builder._get_client` has been called first.


Class Instantiation Flow
------------------------
#. Run :func:`~es_client.helpers.utils.process_config` on ``raw_config``
#. Set instance attributes ``version_max`` and ``version_min`` with the
   provided values.
#. Set instance attribute ``master_only`` to the value from ``raw_config``
#. Initialize instance attribute ``is_master`` with a `None`
#. Set instance attribute ``skip_version_test`` to the value from
   ``raw_config``
#. Set instance attribute ``aws`` to the value of
   ``raw_config['elasticsearch']['aws']`` if ``sign_requests`` is `True`,

     #. Set instance attribute ``use_aws`` to `True` if ``sign_requests`` is
        `True` otherwise set it to `False`.

#. Set instance attribute ``client_args`` to the value of
   ``raw_config['elasticsearch']['client']``
#. Execute :meth:`~es_client.Builder._fix_url_prefix`
#. Ensure that ``client_args['hosts']`` is a :class:`list`
#. Execute :meth:`~es_client.Builder._check_http_auth` to build the
   ``http_auth`` tuple, if ``username`` and ``password`` are not `None`.
#. Execute :meth:`~es_client.Builder._check_ssl` to ensure we have at least the
   `certifi <https://github.com/certifi/python-certifi>`_ signing certificates.
#. Execute :meth:`~es_client.Builder._parse_aws` to extract AWS credentials if
   such has been specified.
#. If ``autoconnect`` is `True`:

    #. Execute :meth:`~es_client.Builder._get_client` to finally build the
       :class:`Elasticsearch Client <elasticsearch.Elasticsearch>` client
       object.
    #. Execute :meth:`~es_client.Builder._check_version` and
       :meth:`~es_client.Builder._check_master` as post-checks.  Nothing will
       happen if these checks are not enabled in ``raw_config``
