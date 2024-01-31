.. _helpers:

Helpers
#######

.. _helpers_config:

Config
======

.. py:module:: es_client.helpers.config

.. autofunction:: cli_opts

.. autofunction:: cloud_id_override

.. autofunction:: context_settings

.. autofunction:: get_arg_objects

.. autofunction:: get_args

.. autofunction:: get_client

.. autofunction:: get_config

.. autofunction:: get_hosts

.. autofunction:: get_width

.. autofunction:: hosts_override

.. autofunction:: override_client_args

.. autofunction:: override_other_args

.. autofunction:: override_settings


.. _helpers_logging:

Logging
=======

.. py:module:: es_client.helpers.logging

.. autofunction:: check_logging_config

.. autofunction:: configure_logging

.. autofunction:: de_dot

.. autofunction:: deepmerge

.. autofunction:: is_docker

.. autofunction:: override_logging

.. autofunction:: set_logging

.. autoclass:: es_client.helpers.logging.Whitelist
   :members:

.. autoclass:: es_client.helpers.logging.Blacklist
   :members:

.. autoclass:: es_client.helpers.logging.LogInfo
   :members:

.. autoclass:: es_client.helpers.logging.JSONFormatter
   :members:


.. _helpers_schemacheck:

SchemaCheck
===========

.. py:module:: es_client.helpers.schemacheck

.. autofunction:: password_filter

.. autoclass:: es_client.helpers.schemacheck.SchemaCheck
   :members:


.. _helpers_utils:

Utils
=====

.. py:module:: es_client.helpers.utils

.. autofunction:: check_config

.. autofunction:: ensure_list

.. autofunction:: file_exists

.. autofunction:: get_version

.. autofunction:: get_yaml

.. autofunction:: option_wrapper

.. autofunction:: parse_apikey_token

.. autofunction:: passthrough

.. autofunction:: prune_nones

.. autofunction:: read_file

.. autofunction:: verify_ssl_paths

.. autofunction:: verify_url_schema
