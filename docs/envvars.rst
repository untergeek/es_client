.. _envvars:

#####################
Environment Variables
#####################

Beginning in version 8.12, es_client allows you to use environment variables to configure settings
*without* needing to specify a command-line option or a configuration file option.

This should prove exceptionally useful in containerized applications like Kubernetes or Docker.

Usage
-----

A configuration file example:

.. code-block:: yaml

   elasticsearch:
     client:
       hosts: http://127.0.0.1:9200
     other_settings:
       username: user
       password: pass

Which would be run as follows:

.. code-block:: shell

   myapp.py --config /path/to/config.yml

or a command-line example:

.. code-block:: shell

   myapp.py --hosts http://127.0.0.1:9200 --username user --password pass

Can *both* be executed with *no* configuration file and *no* command-line options as follows:

.. code-block:: shell
   
   ESCLIENT_HOSTS=http://127.0.0.1:9200 ESCLIENT_USERNAME=user ESCLIENT_PASSWORD=pass myapp.py

In Kubernetes or Docker based applications, these environment variables can be set in advance,
making the program call exceptionally clean. Of course, you're still welcome to use a configuration
file, but identify it with an environment variable:

.. code-block:: shell
   
   ESCLIENT_CONFIG=/path/to/config.yml myapp.py


List of Environment Variables
-----------------------------

.. list-table:: Commonly Used Environment Variables
   :widths: 33 33 34
   :header-rows: 1

   * - Configuration File
     - Command-Line
     - Environment Variable
   * - 
     - ``--config``
     - ESCLIENT_CONFIG
   * - hosts
     - ``--hosts``
     - :ref:`ESCLIENT_HOSTS <envvars_multiple>`
   * - cloud_id
     - ``--cloud_id``
     - ESCLIENT_CLOUD_ID
   * - token
     - ``--api_token``
     - ESCLIENT_API_TOKEN
   * - id
     - ``--id``
     - ESCLIENT_ID
   * - api_key
     - ``--api_key``
     - ESCLIENT_API_KEY
   * - username
     - ``--username``
     - ESCLIENT_USERNAME
   * - password
     - ``--password``
     - ESCLIENT_PASSWORD
   * - request_timeout
     - ``--request_timeout``
     - ESCLIENT_REQUEST_TIMEOUT
   * - verify_certs
     - ``--verify_certs``
     - :ref:`ESCLIENT_VERIFY_CERTS <envvars_bool>`
   * - ca_certs
     - ``--ca_certs``
     - ESCLIENT_CA_CERTS
   * - client_cert
     - ``--client_cert``
     - ESCLIENT_CLIENT_CERT
   * - client_key
     - ``--client_key``
     - ESCLIENT_CLIENT_KEY
   * - loglevel
     - ``--loglevel``
     - ESCLIENT_LOGLEVEL
   * - logfile
     - ``--logfile``
     - ESCLIENT_LOGFILE
   * - logformat
     - ``--logformat``
     - ESCLIENT_LOGFORMAT

.. list-table:: Uncommon Environment Variables
   :widths: 33 33 34
   :header-rows: 1

   * - Configuration File
     - Command-Line
     - Environment Variable
   * - blacklist
     - ``--blacklist``
     - :ref:`ESCLIENT_BLACKLIST <envvars_multiple>`
   * - master_only
     - ``--master-only``
     - :ref:`ESCLIENT_MASTER_ONLY <envvars_bool>`
   * - skip_version_test
     - ``--skip_version_test``
     - :ref:`ESCLIENT_SKIP_VERSION_TEST <envvars_bool>`
   * - bearer_auth
     - ``--bearer_auth``
     - ESCLIENT_BEARER_AUTH
   * - opaque_id
     - ``--opaque_id``
     - ESCLIENT_OPAQUE_ID
   * - http_compress
     - ``--http_compress``
     - :ref:`ESCLIENT_HTTP_COMPRESS <envvars_bool>`
   * - ssl_version
     - ``--ssl_version``
     - ESCLIENT_SSL_VERSION
   * - ssl_assert_hostname
     - ``--ssl_assert_hostname``
     - ESCLIENT_SSL_ASSERT_HOSTNAME
   * - ssl_assert_fingerprint
     - ``--ssl_assert_fingerprint``
     - ESCLIENT_SSL_ASSERT_FINGERPRINT

.. _envvars_multiple:

Settings With Multiple Values
-----------------------------

.. list-table:: Settings With Multiple Values
   :widths: 33 33 34
   :header-rows: 1

   * - Configuration File
     - Command-Line
     - Environment Variable
   * - hosts
     - ``--hosts``
     - ESCLIENT_HOSTS
   * - blacklist
     - ``--blacklist``
     - ESCLIENT_BLACKLIST

Where multiple values are permitted, as with the ``hosts`` and ``blacklist`` settings, this is done
by simply specifying multiple values within quotes, e.g.

.. code-block:: shell
   
   ESCLIENT_HOSTS="http://127.0.0.1:9200 http://localhost:9200"

This will automatically expand into an array of values:

.. code-block:: shell
   
   config: {'client': {'hosts': ['http://127.0.0.1:9200', 'http://localhost:9200']}}...

.. _envvars_bool:

Settings With Boolean Values
----------------------------

.. list-table:: Settings With Boolean Values
   :widths: 33 33 34
   :header-rows: 1

   * - Configuration File
     - Command-Line
     - Environment Variable
   * - verify_certs
     - ``--verify_certs``
     - ESCLIENT_VERIFY_CERTS
   * - master_only
     - ``--master-only``
     - ESCLIENT_MASTER_ONLY
   * - skip_version_test
     - ``--skip_version_test``
     - ESCLIENT_SKIP_VERSION_TEST
   * - http_compress
     - ``--http_compress``
     - ESCLIENT_HTTP_COMPRESS
    
Where boolean values are accepted, as with the verify_certs setting, this is done with any
acceptable boolean-eque value, e.g. 0, F, False for false values, or 1, T, True for true values:

.. code-block:: shell
   
   ESCLIENT_MASTER_ONLY=true
   ESCLIENT_MASTER_ONLY=T
   ESCLIENT_MASTER_ONLY=1

Results in:

.. code-block:: shell
   
   'other_settings': {'master_only': True,...

While:

.. code-block:: shell
   
   ESCLIENT_MASTER_ONLY=false
   ESCLIENT_MASTER_ONLY=F
   ESCLIENT_MASTER_ONLY=0

Results in:

.. code-block:: shell
   
   'other_settings': {'master_only': False,...

**NOTE: All string-based booleans are case-insensitive.**

.. list-table:: Acceptable Boolean Values
   :widths: 50 50
   :header-rows: 1

   * - True
     - False
   * - 1
     - 0
   * - True, TRUE, true
     - False, FALSE, false
   * - T, t
     - F, f
