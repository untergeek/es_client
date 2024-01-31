.. _readme:

es_client
=========

https://es-client.readthedocs.io/

You may wonder why this even exists, as at first glance it doesn't seem to make
anything any easier than just using the elasticsearch8 Python module to
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
                'master_only': false,
                'username': 'joe_user',
                'password': 'password',
            }
        },
        'logging': {
            'loglevel': 'INFO',
            'logfile': '/path/to/file.log',
            'logformat': 'default',
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
        master_only: false
        username: joe_user
        password: password
    logging:
      loglevel: INFO
      logfile: /path/to/file.log
      logformat: default

::

    from es_client import Builder

    builder = Builder(configfile='/path/to/es_client.yml')

    try:
        builder.connect()
    except:
        # Do exception handling here...

    client = builder.client

The same schema validations apply here as well.
