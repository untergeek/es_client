.. _api:

ES Client API reference
#######################

.. _builder:

Builder Class
=============

.. autoclass:: es_client.builder.Builder
   :members:

Builder Attribute Errata
------------------------

:client: The :py:class:`~.elasticsearch.Elasticsearch` object is only created after passing all
   other tests, and if ``autoconnect`` is ``True``, or
   :py:meth:`~.es_client.builder.Builder.connect` has been called.

:is_master: Initially set to ``None``, this value is set automatically if ``autoconnect`` is
   ``True``.  It can otherwise be set by calling
   :py:meth:`~.es_client.builder.Builder._find_master` after
   :py:meth:`~.es_client.builder.Builder._get_client` has been called first.


Class Instantiation Flow
------------------------
#. Check to see if ``elasticsearch`` key is in the supplied ``raw_config``
   dictionary.  Log a warning about using defaults if it is not.
#. Run :py:meth:`~.es_client.builder.Builder._check_config` on ``raw_config``
#. Set instance attributes ``version_max`` and ``version_min`` with the
   provided values.
#. Set instance attribute ``master_only`` to the value from ``raw_config``
#. Initialize instance attribute ``is_master`` with a ``None``
#. Set instance attribute ``skip_version_test`` to the value from
   ``raw_config``
#. Set instance attribute ``client_args`` to the value of
   ``raw_config['elasticsearch']['client']``
#. Execute :py:meth:`~.es_client.builder.Builder._check_basic_auth` to build the ``basic_auth``
   tuple, if ``username`` and ``password`` are not ``None``.
#. Execute :py:meth:`~.es_client.builder.Builder._check_api_key` to build the
   ``api_key`` tuple, if the ``id`` and ``api_key`` sub-keys are not ``None``.
#. Execute :py:meth:`~.es_client.builder.Builder._check_cloud_id` to ensure the client
   connects to the defined ``cloud_id`` rather than anything in ``hosts``.
#. Execute :py:meth:`~.es_client.builder.Builder._check_ssl` to ensure we have at least the
   `certifi <https://github.com/certifi/python-certifi>`_ signing certificates.
#. If ``autoconnect`` is `True`:

    #. Execute :py:meth:`~.es_client.builder.Builder._get_client` to finally build the
       :py:class:`~.elasticsearch.Elasticsearch` client object.
    #. Execute :py:meth:`~.es_client.builder.Builder._check_version` and
       :py:meth:`~.es_client.builder.Builder._check_master` as post-checks.  Nothing will
       happen if these checks are not enabled in ``raw_config``
