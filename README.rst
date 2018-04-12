.. _readme:

es_client
=========

You may wonder why this even exists, as at first glance it doesn't seem to make
anything any easier than just using ``elasticsearch.Elasticsearch()`` to
build a client connection.  I needed to be able to reuse the more complex
schema validation bits I was employing, namely:

* ``master_only`` detection
* AWS IAM credential collection via ``boto3.session.Session``
* Elasticsearch version checking and validation, and the option to skip this.
* Configuration value validation, including file paths for SSL certificates,
  meaning:

  * No unknown keys or unacceptable parameter values are accepted
  * Acceptable values and ranges are established--and easy to amend, if
    necessary.

So, if you don't need these, then this library probably isn't what you're
looking for.  If you want these features, then you've come to the right place.

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
