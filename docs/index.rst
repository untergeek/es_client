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

So, if you don't need these, then this library probably isn't what you're
looking for.  If you want these features, then you've come to the right place.

Example Usage
-------------

::

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

::

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

::

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
   defaults
   helpers
   exceptions
   Changelog
   :maxdepth: 2

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
