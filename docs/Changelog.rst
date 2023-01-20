.. _changelog:

Changelog
=========

8.6.0.post3 (19 January 2023)
-----------------------------

**Changes**

  * Improve ``helpers.utils`` function ``verify_url_schema`` ability to catch malformed
    URLs. Added tests to verify functionality.
  * Improve Docker test scripts. Now there's only one set of scripts in
    ``docker_test/scripts``. ``create.sh`` requires a semver version of Elasticsearch
    at the command-line, and it will build and launch a docker image based on that
    version. For example, ``./create.sh 8.6.0`` will create a test image. Likewise,
    ``destroy.sh`` will clean it up afterwards, and also remove the ``Dockerfile``
    which is created from the ``Dockerfile.tmpl`` template.


8.6.0.post2 (18 January 2023)
-----------------------------

**Changes**

  * Move the ``get_version`` method to its own function so other programs can also use it.
  * Pylint cleanup of most files

8.6.0.post1 (17 January 2023)
-----------------------------

**Changes**

  * Python prefers its own version to SemVer, so there are no changes but one of nomenclature.

8.6.0+build.2 (17 January 2023)
-------------------------------

**Changes**

  * Improve the client configuration parsing behavior. If absolutely no config is given, then set
    ``hosts`` to ``http://127.0.0.1:9200``, which mirrors the ``elasticsearch8`` client default
    behavior.

8.6.0 (11 Janary 2023)
----------------------

**Changes**

  * Version bump ``elasticsearch8==8.6.0``
  * Add Docker test environment for Elasticsearch 8.6.0

**Fixes**

  * Docker test environment for 8.5.3 was still running Elasticsearch version 8.4.3. This has been corrected.

8.5.0 (11 January 2023)
-----------------------

**Changes**

  * Version bump ``elasticsearch8==8.5.3``
  * Version bump ``certifi>=2022.12.7``
  * Add Docker test env for Elasticsearch 8.5.3

8.1.0 (3 November 2022)
-----------------------

**Breaking Changes**

Yeah. I know. It's not semver, but I don't care. This is a needed improvement, and I'm the only one
using this so far as I know, so it shouldn't affect anyone in a big way.

  * ``Builder`` now will not work unless you provide either a ``configdict`` or ``configfile``. It will
    read and verify a YAML ``configfile`` if provided without needing to do any other steps now.
  * ``Builder.client_args`` is not a dictionary any more, but a subclass with regular attributes.
    Yes, you can get and set attributes however you like now:

    .. code-block:: python

      b = Builder(configdict=mydict, autoconnect=False)
      print('Provided hosts = %s' % b.client_args.hosts)
      b.client_args.hosts = ['https://sub.domain.tld:3456']
      print('Updated hosts = %s' % b.client_args.hosts)
      b.connect()

    Yes, this will effectively change the entry for ``hosts`` and connect to it instead of whatever was provided.
    You can still get a full ``dict`` of the client args with ``Builder.client_args.asdict()``
  * ``Builder.other_args`` (reading in ``other_settings`` from the config) now works the same as
    ``Builder.client_args``. See the above for more info.

**Changes**

  * Add new classes ``ClientArgs`` and ``OtherArgs``. Using classes like these make setting defaults,
    updates, and changes super simple. Now everything is an attribute! And it's still super simple
    to get a ``dict`` of settings back using ``ClientArgs.asdict()`` or ``OtherArgs.asdict()``. This
    change makes it super simple to create this kind of object, override settings from a default or
    command-line options, and then export a ``configdict`` based on these objects to ``Builder``, as
    you can see in the new sample script ``cli_example.py`` for overriding a config file with
    command-line settings.
  * Added *sample* CLI override capacity using ``click``. This will make Curator and other projects
    easier. It's not even required, but a working example helps show the possibilities. You can
    run whatever you like with ``click``, or stick with config files, or whatever floats your boat.
  * The above change also means pulling in ``click`` as a dependency.
  * Moved some methods out of ``Builder`` to be functions in ``es_client.helpers.utils`` instead.
  * Updated tests to work with all of these changes, and added new ones for new functions.

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
