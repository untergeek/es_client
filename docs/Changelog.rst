.. _changelog:

Changelog
=========

8.0.5 (28 October 2022)
-----------------------

**Changes**

  * Version bumped `elasticsearch8` module to 8.4.3
  * Version bumped `certifi` module to 2022.9.24
  * Added Docker tests for Elasticsearch 8.4.3

8.0.4 (23 August 2022)
----------------------

**Changes**

  * Hopefully the last niggling detail. Removed erroneous reference to AWS ES
    and ``boto3`` compatibility from the description sent to PyPi.

8.0.3 (23 August 2022)
----------------------

**Changes**

  * Added ``setup_requires`` section to ``setup.cfg``. ``es_client`` doesn't
    _need_ to have ``setuptools`` to install.
  * Unpinned from top-level version of ``setuptools`` to allow anything
    greater than ``setuptools>=59.0.1`` to fit with Curator's need for
    ``cx_Freeze``, which can't currently use ``setuptools>60.10.0``

8.0.2 (23 August 2022)
----------------------

**Changes**

  * Several more doc fixes to make things work on ReadTheDocs.io

8.0.1 (23 August 2022)
----------------------

**Changes**

  * Update test platform from ancient ``nose`` and ``UnitTest`` framework to use
    ``pytest``. This also allows the client to run on Python 3.10.
  * Update ``README.rst`` so both GitHub and PyPi reflects what's in the documentation.

8.0.0 (22 August 2022)
----------------------

**New Features**

  * Use ``elasticsearch8==8.3.3`` library with this release.
  * Updated all APIs to reflect updated library usage patterns as many APIs
    have changed.
  * Native support for API keys
  * Native support for Cloud ID URL types
  * Updated tests for better coverage
  * Removed all AWS authentication as the ``elasticsearch8`` library no longer
    connects to AWS ES instances.


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
