.. _changelog:

Changelog
=========

1.1.1 (19 April 2018)
---------------------

**Changes**

  * Disregard root-level keys other than ``elasticsearch`` in the supplied
    configuration dictionary.  This makes it much easier to pass in a complete
    configuration and only extract the `elasticsearch` part.
  * Validate that a dictionary was passed, as opposed to other types.

1.1.0 (19 April 2018)
---------------------

**New Features**

  * Add YAML configuration file reading capability so that part is included
    here, rather than having to be bolted on by the user later on.

**Changes**

  * Moved some of the utility functions to the ``Builder`` class as they were
    not needed outside the class.  While this would be a semver breaking
    change, the library is young enough that I think it will be okay, and it
    doesn't break anything else.
  * Put the default Elasticsearch version min and max values in ``default.py``

1.0.1 (12 April 2018)
---------------------

**Bug Fixes**

* It was late, and I forgot to update ``MANIFEST.in`` to include subdirectories
  of ``es_client``.  This has been addressed in this release.

1.0.0 (11 April 2018)
---------------------

**Initial Release**
