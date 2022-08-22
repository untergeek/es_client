.. es_client documentation master file, created by
   sphinx-quickstart on Wed Apr 11 15:16:40 2018.

``es_client`` Documentation
===========================

You may wonder why this even exists, as at first glance it doesn't seem to make
anything any easier than just using :class:`elasticsearch8.Elasticsearch` to
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

Contents
--------

.. toctree::
   builder.rst
   defaults.rst
   helpers.rst
   exceptions.rst
   Changelog.rst
   :maxdepth: 2

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
        }
    }

    try:
        client = Builder(config).client
    except:
        # Do exception handling here...

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

::

    from es_client import Builder
    from es_client.exceptions import ConfigurationError
    from es_client.helpers.utils import get_yaml

    try:
        client = Builder(get_yaml('/path/to/es_client.yml').client
    except:
        # Do exception handling here...

The same schema validations apply here as well.

License
-------

Copyright (c) 2022 Aaron Mildenstein

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
