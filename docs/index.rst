.. es_client documentation master file

``es_client`` Documentation
===========================

You may wonder why this even exists, as at first glance it doesn't seem to make
anything any easier than just using :py:class:`~.elasticsearch.Elasticsearch` to
build a client connection.  I needed to be able to reuse the more complex
schema validation bits I was employing, namely:

* ``master_only`` detection
* Elasticsearch version checking and validation, and the option to skip this.
* Configuration value validation, including file paths for SSL certificates,
  meaning:

  * No unknown keys or unacceptable parameter values are accepted
  * Acceptable values and ranges are established (where known)--and easy to
    amend, if necessary.

But that's just the tip of the iceberg. That's only the :ref:`builder`!

In addition to a Builder class, there's an entire set of :ref:`helpers` and a :ref:`tutorial` to
show you how to build your own command-line interface like :ref:`this one <example_file>`:

.. code-block:: shell

    Usage: run_script.py [OPTIONS] COMMAND [ARGS]...

      CLI Example

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

So, if you don't need these, then this library probably isn't what you're looking for.  If you do
want features like these, then you've come to the right place.

Example Builder Class Usage
---------------------------

.. code-block:: python

    from es_client import Builder

    config = {
        'elasticsearch': {
            'client': {
                'hosts': 'https://10.0.0.123:9200',
                'ca_certs': '/etc/elasticsearch/certs/ca.crt',
                'request_timeout': 60,
            },
            'other_settings': {
                'master_only': True,
                'username': 'joe_user',
                'password': 'password',
            }
        },
        'logging': {
            'loglevel': 'INFO',
            'logfile': '/path/to/file.log',
            'logformat': 'default',
            'blacklist': ['elastic_transport', 'urllib3']
        }
    }

    builder = Builder(configdict=config)

    try:
        builder.connect()
    except:
        # Do exception handling here...

    client = builder.client

Additionally, you can read from a YAML configuration file:

.. code-block:: yaml

    ---
    elasticsearch:
      client:
        hosts: https://10.0.0.123:9200
        ca_certs: /etc/elasticsearch/certs/ca.crt
        request_timeout: 60
      other_settings:
        master_only: true
        username: joe_user
        password: password
    logging:
      loglevel: INFO
      logfile: /path/to/file.log
      logformat: default
      blacklist: ['elastic_transport', 'urllib3']

.. code-block:: python

    from es_client import Builder

    builder = Builder(configfile='/path/to/es_client.yml')

    try:
        builder.connect()
    except:
        # Do exception handling here...

    client = builder.client

The same schema validations apply here as well.

License
-------

Copyright (c) 2022-2024 Aaron Mildenstein

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contents
--------

.. toctree::
   api
   example
   tutorial
   advanced
   defaults
   helpers
   exceptions
   Changelog
   :maxdepth: 5

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
