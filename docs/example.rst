.. _example:

Example Script
##############


This example command-line script file is part of the es_client source code and is at
``./es_client/cli_example.py``. The wrapper script ``run_script.py`` is at the root-level of the
code at ``./run_script.py`` and will automatically target the ``cli_example.py`` script.


``es_client`` in Action
=======================

Whether you have a running version of Elasticsearch or not, you can execute this script as outlined
so long as the Python dependencies are installed. If you've cloned the github repository, this can
be done by running the following command:

Install Prerequisites
---------------------

.. warning::
   I highly recommend setting up a Python virtualenv of some kind before running ``pip``

.. code-block:: shell
   
   pip install -U '.[doc,test]'

Run the Script with ``--help`` or ``-h``
----------------------------------------

With the dependencies installed, the script should just run:

.. code-block:: shell
   
   python run_script.py --help

Running the command will show the command-line help/usage output:

Output
^^^^^^

.. code-block:: shell-session

   Usage: run_script.py [OPTIONS] COMMAND [ARGS]...
   
     CLI Example
   
     Any text added to a docstring will show up in the --help/usage output.
   
     Set short_help='' in @func.command() definitions for each command for terse descriptions in the main help/usage output, as
     with show_all_options() in this example.
   
   Options:
     --config PATH                   Path to configuration file.
     --hosts TEXT                    Elasticsearch URL to connect to.
     --cloud_id TEXT                 Elastic Cloud instance id
     --api_token TEXT                The base64 encoded API Key token
     --id TEXT                       API Key "id" value
     --api_key TEXT                  API Key "api_key" value
     --username TEXT                 Elasticsearch username
     --password TEXT                 Elasticsearch password
     --request_timeout FLOAT         Request timeout in seconds
     --verify_certs / --no-verify_certs
                                     Verify SSL/TLS certificate(s)  [default: verify_certs]
     --ca_certs TEXT                 Path to CA certificate file or directory
     --client_cert TEXT              Path to client certificate file
     --client_key TEXT               Path to client key file
     --loglevel [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                     Log level
     --logfile TEXT                  Log file
     --logformat [default|json|ecs]  Log output format
     -v, --version                   Show the version and exit.
     -h, --help                      Show this message and exit.
   
   Commands:
     show-all-options  Show all configuration options
     test-connection   Test connection to Elasticsearch

Run the Script with a Command
-----------------------------

At the bottom of the usage/help output, you should see ``show-all-options`` and ``test-connection``.

Let's re-run the script with ``show-all-options``:

.. code-block:: shell
   
   python run_script.py show-all-options

Perhaps you're confused to see another help/usage output. But there's a difference:

Output
^^^^^^

.. code-block:: shell-session

   Usage: run_script.py show-all-options [OPTIONS]
   
     ALL OPTIONS SHOWN
   
     The full list of options available for configuring a connection at the command-line.
   
   Options:
     --config PATH                   Path to configuration file.  [env var: ESCLIENT_CONFIG]
     --hosts TEXT                    Elasticsearch URL to connect to.  [env var: ESCLIENT_HOSTS]
     --cloud_id TEXT                 Elastic Cloud instance id  [env var: ESCLIENT_CLOUD_ID]
     --api_token TEXT                The base64 encoded API Key token  [env var: ESCLIENT_API_TOKEN]
     --id TEXT                       API Key "id" value  [env var: ESCLIENT_ID]
     --api_key TEXT                  API Key "api_key" value  [env var: ESCLIENT_API_KEY]
     --username TEXT                 Elasticsearch username  [env var: ESCLIENT_USERNAME]
     --password TEXT                 Elasticsearch password  [env var: ESCLIENT_PASSWORD]
     --bearer_auth TEXT              Bearer authentication token  [env var: ESCLIENT_BEARER_AUTH]
     --opaque_id TEXT                X-Opaque-Id HTTP header value  [env var: ESCLIENT_OPAQUE_ID]
     --request_timeout FLOAT         Request timeout in seconds  [env var: ESCLIENT_REQUEST_TIMEOUT]
     --http_compress / --no-http_compress
                                     Enable HTTP compression  [env var: ESCLIENT_HTTP_COMPRESS]
     --verify_certs / --no-verify_certs
                                     Verify SSL/TLS certificate(s)  [env var: ESCLIENT_VERIFY_CERTS]
     --ca_certs TEXT                 Path to CA certificate file or directory  [env var: ESCLIENT_CA_CERTS]
     --client_cert TEXT              Path to client certificate file  [env var: ESCLIENT_CLIENT_CERT]
     --client_key TEXT               Path to client key file  [env var: ESCLIENT_CLIENT_KEY]
     --ssl_assert_hostname TEXT      Hostname or IP address to verify on the node's certificate.  [env var:
                                     ESCLIENT_SSL_ASSERT_HOSTNAME]
     --ssl_assert_fingerprint TEXT   SHA-256 fingerprint of the node's certificate. If this value is given then root-of-trust
                                     verification isn't done and only the node's certificate fingerprint is verified.  [env var:
                                     ESCLIENT_SSL_ASSERT_FINGERPRINT]
     --ssl_version TEXT              Minimum acceptable TLS/SSL version  [env var: ESCLIENT_SSL_VERSION]
     --master-only / --no-master-only
                                     Only run if the single host provided is the elected master  [env var: ESCLIENT_MASTER_ONLY]
     --skip_version_test / --no-skip_version_test
                                     Elasticsearch version compatibility check  [env var: ESCLIENT_SKIP_VERSION_TEST]
     --loglevel [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                     Log level  [env var: ESCLIENT_LOGLEVEL]
     --logfile TEXT                  Log file  [env var: ESCLIENT_LOGFILE]
     --logformat [default|json|ecs]  Log output format  [env var: ESCLIENT_LOGFORMAT]
     --blacklist TEXT                Named entities will not be logged  [env var: ESCLIENT_BLACKLIST]
     -v, --version                   Show the version and exit.
     -h, --help                      Show this message and exit.

Run the Script with a Command (continued)
-----------------------------------------

A closer look will show that this help output is slightly different, and shows options that the
first run did not. This is on purpose. This is to show how you can use Click to show or hide options
at the command line. This can be done for multiple reasons, including hiding sensitive information.
In this case, however, it's mostly to keep things clean and as terse as possible by showing only the
most frequently used options.

Run the Script with a live host
-------------------------------

Now that we've come this far, it's time to run against a live instance of Elasticsearch!

Let's re-run the script with the command ``test-connection``. This time, unless we're using a local
instance of Elasticsearch running on the default URL of http://127.0.0.1:9200, we will need to
specify a few options. Your options may vary, but let's assume you have an Elasticsearch instance in
`Elastic Cloud <https://cloud.elastic.co>`_ and you have a cloud_id and an API key to use:

If my cloud_id were ``example:REDACTED``, and my API key was also ``apikey:REDACTED``, I could run:

.. code-block:: shell
   
   python run_script.py --cloud_id example:REDACTED --api_token apikey:REDACTED test-connection

If your API key came in two pieces rather than the base64 encoded single token, that's okay! You
can make that work, too:

.. code-block:: shell
   
   python run_script.py --cloud_id example:REDACTED --api_key KEYVALUE --id IDVALUE test-connection

Or maybe you don't have a cloud_id, but you have a URL, and a username and a password:

.. code-block:: shell
   
   python run_script.py --hosts URL --username USER --password PASS test-connection

Maybe you have a YAML configuration file with all the options you need to use:

.. code-block:: shell
   
   python run_script.py --config /path/to/config.yaml test-connection

There are so many ways you can slice and dice this! 

Output
^^^^^^

If all went well, you should see something like this:

.. code-block:: shell-session

    Connection result:
    {'name': 'NODENAME', 'cluster_name': 'CLUSTERNAME', 'cluster_uuid': 'UUID', 'version': 
    {'number': '8.12.0', 'build_flavor': 'default', 'build_type': 'docker', 'build_hash': 
    'HASH', 'build_date': '2024-01-11T10:05:27.953830042Z', 'build_snapshot': False, 
    'lucene_version': '9.9.1', 'minimum_wire_compatibility_version': '7.17.0', 
    'minimum_index_compatibility_version': '7.0.0'}, 'tagline': 'You Know, for Search'}

Option Errata
=============

Most of the options should be straightforward, but a few should be explained.

Multiples
---------

The command-line options ``--hosts`` and ``--blacklist`` can be used multiple times in the same
command-line, e.g.

.. code-block:: shell

  python run_script.py --hosts http://127.0.0.1:9200 --hosts http://127.0.0.2:9200 ...

This is especially nice for reducing log volume with log blacklisting! See one you don't want or
need? Run it again with another ``--blacklist`` entry!

Configuration File Override
---------------------------

You can use a YAML configuration file for all options. But you can also mix configuration file
settings with command-line options. The thing to know is that command-line options will *always*
supersede settings in a configuration file.

ENVIRONMENT VARIABLES
---------------------

Click makes it easy to use environment variables to pass values to options. In fact, it's now built
in to ``es_client``! Any option can have an environment variable. All you need to do is prefix the
uppercase name of the option with ``ESCLIENT_`` and replace any hyphens in the option name with
underscores.  You may have noticed that the environment variables were shown in the
``show-all-options`` output above and wondered what that meant.  Well, now you know!

.. code-block:: shell

  ESCLIENT_LOGLEVEL=DEBUG python run_script.py --hosts http://127.0.0.1:9200

Congratulations, you've now set loglevel to DEBUG with an environment variable!

Multiples?
^^^^^^^^^^

How do environment variables work for parameters that can have multiple values?

Great question! For the options ``es_client`` has that can do multiples, namely ``hosts`` and
``blacklist``, you need to put all values into a single environment variable and separate them with
whitespace:

.. code-block:: shell

  ESCLIENT_HOSTS='http://127.0.0.1:9200 http://localhost:9200' python run_script.py test-connection

A quick look at the DEBUG log shows the following (redacted for brevity):

.. code-block:: shell

   ... "Elasticsearch Configuration" config: {'hosts': ['http://127.0.0.1:9200', 'http://localhost:9200'], ...

Yup! Multiple values from a single environment variable is possible!

Flags, or boolean options?
^^^^^^^^^^^^^^^^^^^^^^^^^^

A quick look at the ``show-all-options`` output reveals that our boolean options (i.e., those with
an on and off switch) show the defaults as the flag and not as True or False:

.. code-block:: shell

   --http_compress / --no-http_compress
      Enable HTTP compression  [env var: ESCLIENT_HTTP_COMPRESS; default: no-http_compress]

Does this mean you have to set ``ES_CLIENT_COMPRESS`` to ``http_compress`` or ``no-http_compress``?

No. In fact, don't do that. Click is very smart and can interpret most boolean-esque settings.

True values: 1, True, true, TRUE (pretty sure it's case-insensitive)
False values: 0, False, false, FALSE

So here's the real-world example:

.. code-block:: shell

   ESCLIENT_HTTP_COMPRESS=1 python run_script.py test-connection

And in the debug log output (redacted for brevity):

.. code-block:: shell

   "Elasticsearch Configuration" config: {'client': {'hosts': ..., 'http_compress': True,

You can take my word for it, or you can test it for yourself. It works.

.. _my_own_app:

Next Step: Make Your Own App Using ``es_client``
================================================

Visit the :ref:`tutorial` for the next step!

.. _example_file:

File Source Code
================

This file is part of the source code and is at ``./es_client/cli_example.py``.

.. literalinclude:: ../src/es_client/cli_example.py
  :language: python

.. _included_commands:

Included Commands
=================

This module is referenced by ``./es_client/cli_example.py`` and includes the
``show-all-options`` and ``test-connection`` functions/commands available when
running from the CLI.

.. literalinclude:: ../src/es_client/commands.py
  :language: python
