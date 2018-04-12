.. es_client documentation master file, created by
   sphinx-quickstart on Wed Apr 11 15:16:40 2018.

``es_client`` Documentation
===========================

You may wonder why this even exists, as at first glance it doesn't seem to make
anything any easier than just using :class:`elasticsearch.Elasticsearch` to
build a client connection.  I needed to be able to reuse the more complex
schema validation bits I was employing, namely:

* ``master_only`` detection
* AWS IAM credential collection via :class:`boto3.session.Session`
* Elasticsearch version checking and validation, and the option to skip this.
* Configuration value validation, including file paths for SSL certificates,
  meaning:

  * No unknown keys or unacceptable parameter values are accepted
  * Acceptable values and ranges are established--and easy to amend, if
    necessary.

So, if you don't need these, then this library probably isn't what you're
looking for.  If you want these features, then you've come to the right place.

Contents
--------

.. toctree::
   :maxdepth: 2

   builder
   helpers
   exceptions
   defaults
   Changelog

Example Usage
-------------

::

    from es_client import Builder

    config = {
        'elasticsearch': {
            'master_only': True,
            'client': {
                'hosts': '10.0.0.123',
                'use_ssl': True,
                'ca_certs': '/etc/elasticsearch/certs/ca.crt',
                'username': 'joe_user',
                'password': 'password',
                'timeout': 60,
            }
        }
    }

    client = Builder(config).client


License
-------

Copyright (c) 2018 Aaron Mildenstein

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
