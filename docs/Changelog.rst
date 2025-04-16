.. _changelog:

Changelog
=========

8.18.0 (15 April 2025)
----------------------

**Announcement**

Release of 8.18.0

**Changes**

  * Version bumped to ``8.18.0``.
  * Dependencies bumped:
     * ``elasticsearch8==8.18.0``
     * ``tiered_debug==1.1.0``
  * Updated code to take advantage of ``tiered_debug``. Use the new local ``debug.py``
    module to get the ``debug`` logging object for the entire module.
  * To shorten module names when logging, the ``helpers`` subdirector/submodule
    was deprecated. A DeprecationWarning will be raised if you try to import from
    ``es_client.helpers``, but it will still work. The modules that were formerly
    in ``helpers``, namely

     * ``config``
     * ``logging``
     * ``schemacheck``
     * ``utils``

    are now at the root level under ``es_client``. 
    
  * All tests passing.

8.17.5 (31 March 2025)
----------------------

**Announcement**

  * Adapted to use the ``tiered_debug`` logging helper module.
     * Lots of replacements added to use tiered debug logging instead of logger.debug
     * With the tiered debug logging options, more verbose logging was added that
       will not be seen unless set to show more. See the ``tiered_debug`` module
       for more information.
  * Version bumped to ``8.17.5``.
  * Updated tests to catch the new tiered debug logging.
  * All tests passing.

8.17.4 (18 March 2025)
----------------------

**Bugfix**

  * Fixed a logging configuration bug to only assign a file handler if a log file
    is specified. Also fixed to ensure configuration goes to the root logger.

**Changes**

  * Dependency version bumps in this release:
      * ``elasticsearch8==8.17.2``
      * ``certifi>=2025.3.31``

8.17.3 (6 March 2025)
---------------------

**Announcement**

Logging changes
***************

If you specify a log file in your configuration, it will now be used, and nothing
should appear different for you. If, however, you do not specify a log file, the
default behavior is to log to both STDOUT `and` STDERR, with the streams split.
This is the new behavior. If you do not want this, you must specify a log file
in your configuration.

.. code-block:: shell

    $ python run_script.py --loglevel DEBUG test-stderr 1>stdout.log 2>stderr.log

This will log all output to ``stdout.log`` and all errors to ``stderr.log``. 

.. code-block:: shell

    $ cat stdout.log                                                                                                                                                         ─╯
    DEBUG: Overriding configuration file setting loglevel=INFO with command-line option loglevel=DEBUG
    2025-03-06 17:53:01,038 DEBUG         es_client.commands            test_stderr:131  This is a debug message
    2025-03-06 17:53:01,038 INFO          es_client.commands            test_stderr:132  This is an info message

    Logging test complete.

    $ cat stderr.log
    2025-03-06 17:53:01,038 WARNING       es_client.commands            test_stderr:133  This is a warning message
    2025-03-06 17:53:01,038 ERROR         es_client.commands            test_stderr:134  This is an error message
    2025-03-06 17:53:01,038 CRITICAL      es_client.commands            test_stderr:135  This is a critical message


**Changes**

  * Changes in the ``logging.py`` file to handle the new logging behavior. Also added
    ``test-stderr`` to ``commands.py`` and ``cli_example.py`` to demonstrate the new
    behavior.
  * Updated ``defaults.py`` to have a default ``LOGFORMAT`` of ``default``.


8.17.2 (26 February 2025)
-------------------------

**Announcement**

  * Attempting to allow the 8.x client to work with 7.x Elasticsearch servers by
    making ``min_version`` and ``max_version`` configurable at the time of
    ``Builder`` instantiation.
    The default values are still limited to 8.x versions, but preliminary testing
    shows that the 8.x client works just fine for Curator against 7.14.x through
    7.17.x servers with these changes.
    
**Changes**

  * The ``Builder`` class can now override the default minimum and/or maximum version:
    ``Builder(config, min_version=7.0.0, max_version=8.99.99)``.
  * The ``helpers.config.get_client()`` function can also take these arguments:
    ``helpers.config.get_client(config, min_version=7.0.0, max_version=8.99.99)``.
  * Updated the date and copyright holder in ``LICENSE``.


8.17.1 (24 Janary 2025)
-----------------------

**Announcements**

  * Python 3.13 support...but with a caveat.
     * HUGE (potential) caveat, though. The Python 3.13 SSL implementation now has
       ``X509_V_FLAG_X509_STRICT`` set by default. This unfortunately means that
       self-signed certificates created by Elasticsearch's ``certutil`` will not
       work with Python 3.13 as they do not yet include the key usage extension.
       If you are using ``es_client`` in any way with one of these certificates,
       I highly recommend that you not use Python 3.13 until this is resolved.
     * 3.13 is excluded from the Hatch test matrix for this reason.
     * 3.13 will still be tested manually with each release.
  
**Changes**

  * Python module version bumps:
    * ``elasticsearch8==8.17.1``
    * ``click==8.1.8``
    * ``certifi>=2024.12.14``
  * Refactored ``master_only`` functions and tests. I discovered some loopholes
    in my code when I was testing Python 3.13 against an Elastic Cloud instance,
    so I fixed them. This also necessitated a change in the integration tests.

8.15.2 (30 September 2024)
--------------------------

**Changes**

  * Python module version bumps:
    * ``elasticsearch8==8.15.1``
    * ``pyyaml==6.0.2``
    * ``certifi>=2024.8.30``


8.15.1 (23 August 2024)
-----------------------

**Changes**

  * Added ``commands.py`` as both a cleaner location for the ``show_all_options``
    function, as well as a place it could be imported and re-used.
  * Updated ``docs/example.rst`` and ``docs/tutorial.rst`` to reflect these
    location changes.
  * Updated ``pytest.ini`` to automatically look for and use ``.env`` for
    environment variables for testing.
  * Using versioned ``docker_test`` scripts now from
    https://github.com/untergeek/es-docker-test-scripts

8.15.0 (13 August 2024)
-----------------------

**Changes**

  * Python module version bumps:
    * ``elasticsearch8==8.15.0``
  * Make execution scripts more consistent and PEP compliant.

8.14.2 (6 August 2024)
----------------------

**Changes**
 
  * Missed one instance of ``six`` module.

8.14.1 (6 August 2024)
----------------------

**Changes**

  * ``six`` module removed.
  * Rolled back ``voluptuous`` to be ``>=0.14.2`` to work with Python 3.8

8.14.0 (3 July 2024)
--------------------

**Changes**

  * Python module version bumps:
      * ``elasticsearch8==8.14.0``
      * ``ecs-logging==2.2.0``
      * ``voluptuous>=0.15.2``
      * ``certifi>=2024.6.2``
  * Updated remaining tests to Pytest-style formatting.
  * Updated ``docker_test`` scripts to most recent updates.

**Bugfix**

  * Fixed an error reported at https://github.com/elastic/curator/issues/1713
    where providing an empty API ``token`` key would still result in the Builder
    class method ``_check_api_key`` trying to extract data. Locally tracked at
    https://github.com/untergeek/es_client/issues/66 

8.13.5 (7 May 2024)
-------------------

**Changes**

  * Version bump for ``elasticsearch8==8.13.1``
  * Code formatting changes (cleanup of lines over 88 chars, mostly).
  * Added ``.coveragerc``
  * Improved ``docker_test`` scripts and env var importing in tests.

**Bugfix**

  * Discovered an instance where passwords were being logged. This has been corrected.


8.13.4 (30 April 2024)
----------------------

**Changes**

  * Updated ``docker_test`` scripts to enable TLS testing and better integration with pytest.
    TEST_USER and TEST_PASS and TEST_ES_SERVER, etc. are all populated and put into ``.env``
    Even the CA certificate is copied to TEST_PATH, so it's easy for the tests to pick it up.
    Not incidentally, the scripts were moved from ``docker_test/scripts`` to just ``docker_test``.
    The tutorial in the documentation has been updated to reflect these changes.
  * Added ``pytest-dotenv`` as a test dependency to take advantage of the ``.env``
  * Minor code formatting in most files as I've switched to using ``black`` with VS Code, and
    flake8, and mypy.

**Bugfix**

  * Found 1 stray instance of ``update_settings`` from before the DotMap switch. Fixed.

8.13.3 (26 April 2024)
----------------------

**Changes**

  * After all that work to ensure proper typing, I forgot to include the ``py.typed`` marker file.

8.13.2 (25 April 2024)
----------------------

**Changes**

  * Added typing hints, everywhere. Trying to make the module play nicer with others.
  * Moved all code under ``src/es_client`` to be more package compliant.
  * Moved ``__version__`` to ``__init__.py``
  * Updated the ``pyproject.toml`` file to reflect these changes.
  * Updated tests and documentation as needed.

**Potentially Breaking Changes**

  * Migrated away from custom ``dict``-to-attribute class ``Args`` to ``DotMap``. It's the best of
    both worlds as it gives full dotted notation access to a dictionary, making it appear like
    class attributes. But it also still affords you the ability to treat each nested field just like
    a dictionary, still. ``Builder.client_args`` and ``Builder.other_args`` should look and feel the
    exact same as before, with one noted difference, and that is the ``.asdict()`` method has been
    replaced by the ``.toDict()`` method. This is the one change that might mess you up. If you
    are using that anywhere, please replace those calls. Also, if you were manually building these
    objects before, rather than supplying a config file or dict, you can create these now as
    follows:

      .. code-block:: python

        from es_client import Builder
        from dotmap import DotMap

        client_settings = {}  # Filled with your client settings
        client_args = DotMap(client_settings)

        builder = Builder()
        builder.client_args = client_args
        # Or directly assign:
        builder.client_args = DotMap(client_settings)
    
    Updating a single key is simple:

      .. code-block:: python

        other_args = DotMap(other_settings)
        other_args.username = 'nobody'
        other_args['password'] = 'The Spanish Inquisition'
    
    As noted, both dotted and dict formats are acceptable, as demonstrated above.
    Updating with a dictionary of root level keys is simple:

      .. code-block:: python

        other_settings = {
            'master_only': False,
            'username': 'original',
            'password': 'oldpasswd',
        }
        other_args = DotMap(other_settings)
        # DotMap(master_only=False, username='original', password='oldpasswd')
        changes = {
            'master_only': True,
            'username': 'newuser',
            'password': 'newpasswd',
        }
        other_args.update(changes)
        # DotMap(master_only=True, username='newuser', password='newpasswd')
    
    If putting a nested dictionary in place, you should convert it to a DotMap first:

      .. code-block:: python

        d = {'a':'A', 'b':{'c':'C', 'd':{'e':'E'}}}
        dm = DotMap(d)
        # DotMap(a='A', b=DotMap(c='C', d=DotMap(e='E')))
        b = {'b':{'g':'G', 'h':{'i':'I'}}}
        dm.update(b)
        # DotMap(a='A', b={'g': 'G', 'h': {'i': 'I'}})
        #                 ^^^
        #              Not a DotMap
        dm.update(DotMap(b))
        DotMap(a='A', b=DotMap(g='G', h=DotMap(i='I')))
    
    It's always safest to update with a DotMap rather than a bare dict.
    That's about it.

8.13.1 (10 April 2024)
----------------------

**Bugfix**

  * Reported in #60. Newer code changes do not work properly with Python versions < 3.10 due to
    changes to dictionary annotations. The offending code has been patched to work around this.

**Announcement**

  * Added infrastructure to test multiple versions of Python against the code base. This requires
    you to run ``pip install -U hatch hatchling``, and then ``hatch run test:test``. integration
    tests will fail if you do not have a local Elasticsearch running (see the
    ``docker_test/scripts`` directory for some help with that).

8.13.0 (2 April 2024)
---------------------

**Changes**

  * Version bump: ``elasticsearch8==8.13.0``

8.12.9 (26 March 2024)
----------------------

**Bugfix**

  * Reported in #1708. Default values (rather than None values) were overriding what was in config
    files. As a result, these default values from command-line settings were overriding important
    settings which were set properly in the configuration file. Hat tip to @rgaduput for reporting
    this.

**Changes**

  * Updated cli_example.py to make the ``show_all_options`` sub-command show the proper environment
    variables. This entailed resetting the context_settings. A note explaining the why is now in
    the comments above that function.
  * Updates to reflect the default values in the command-line were made in the tutorial and example
    documentation pages.
  * A new documentation page was created specific to environment variables.
  * Version bump ``voluptuous==0.14.2`` from ``0.14.1``

8.12.8 (20 March 2024)
----------------------

**Bugfix**

  * Really batting 1000 today. Missed some version bumps.

8.12.7 (20 March 2024)
----------------------

**Bugfix**

  * Erroneously removed ``six`` dependency. It's back at ``1.16.0``.

8.12.6 (20 March 2024)
----------------------

**Changes**

  * After reading and re-reading through the tutorial, I made a few doc changes.
  * ``ctx.obj`` is instantiated in ``helpers.config.context_settings`` now, saving yet another
    line of code from being needed in a functional command-line script.
  * Decided it was actually time to programmatically approach the huge list of decorators necessary
    to make ``es_client`` work in the example. Now there's a single decorator,
    ``@options_from_dict()`` in ``helpers.config``, and it takes a dictionary as an argument. The
    form of this dictionary should be:

    .. code-block:: python

      {
        "option1": {"onoff": {}, "override": {}, "settings": {}},
        "option2": {"onoff": {}, "override": {}, "settings": {}},
        # ...
        "optionN": {"onoff": {}, "override": {}, "settings": {}},
      }
    
    The defaults are provided in ``helpers.defaults`` as constants ``OPTION_DEFAULTS`` and
    ``SHOW_EVERYTHING``. These can be overridden programmatically or very tediously manually.
  * Dependency version bumps:

    .. code-block:: python

      elasticsearch8==8.12.1
      certifi==2024.2.2

8.12.5 (4 February 2024)
------------------------

**Changes**

After some usage, it seems wise to remove redundancy in calling params and config in the functions
in ``helpers.config``. This is especially true since ``ctx`` already has all of the params, and
``ctx.params['config']`` has the config file (if specified).

It necessitated a more irritating revamp of the tests to make it work (why, Click? Why can't a
Context be provided and just work?), but it does work cleanly now, with those clean looking
function calls.

New standards include:

  * ENVIRONMENT VARIABLE SUPPORT.  Very big. Suffice to say that all command-line options can now
    be set by an environment variable by putting the prefix ``ESCLIENT_`` in front of the uppercase
    option name, and replace any hyphens with underscores. ``--http-compress True`` is settable by
    having ``ESCLIENT_HTTP_COMPRESS=1``. Boolean values are 1, 0, True, or False (case-insensitive).
    Options like ``hosts`` which can have multiple values just need to have whitespace between the
    values:

    .. code-block:: shell

       ESCLIENT_HOSTS='http://127.0.0.1:9200 http://localhost:9200'
    
    It splits perfectly. This is big news for the containerization/k8s community. You won't have to
    have all of the options spilled out any more. Just have the environment variables assigned.
  * ``ctx.obj['default_config']`` will be the place to insert a default configuration file
    _before_ calling ``helpers.config.get_config()``.
  * ``helpers.config.get_arg_objects()`` will now set ``ctx.obj['client_args'] = ClientArgs()``
    and ``ctx.obj['other_args'] = OtherArgs()``, where they become part of ``ctx.obj`` and are
    accessible thereby.
  * ``helpers.config.generate_configdict`` will now populate ``ctx.obj['configdict']``
  * ``Builder(configdict=ctx.obj['configdict'])`` will work, as will 
    ``helpers.config.get_client(configdict=ctx.obj['configdict'])``

In fact, this has been so simplified now that the flow of a command-line app is as simple as:

  .. code-block:: python

      def myapp(ctx, *args):
          ctx.obj = {}
          ctx.obj['default_config'] = '/path/to/cfg.yaml'
          get_config(ctx)
          configure_logging(ctx)
          generate_configdict(ctx)
          es_client = get_client(configdict=ctx.obj['configdict'])
          # Your other code...

Additionally, the log blacklist functionality has been added to the command-line, the default
settings, the ``helpers.logging`` module, and the ``cli_example``, which should be welcome news to
the containerized world.

Major work to standardize the documentation has also been undertaken. In fact, there is now a
tutorial on how to make a command-line app in the documentation.

8.12.4 (1 February 2024)
------------------------

**Fixes**

The try/except block for Docker logging needed to be out one level farther.

This should fix the permissions error issues at last.


8.12.3 (31 January 2024)
------------------------

**Change**

Since I'm doing Schema validation here now, I think it appropriate to have a
dedicated exception for SchemaCheck failures.

This will be FailedValidation.

8.12.2 (31 January 2024)
------------------------

**Fixes**

In trying to make ``SchemaCheck`` reusable, I discovered that it _always_,
was unconditionally attempting apply the ``password_filter`` on every
``config`` coming through. An empty filter shows up as ``None``, causing
an AttributeError exception. Going to only do ``password_filter`` when
``config`` is a ``dict``.

8.12.1 (31 January 2024)
------------------------

**Announcement**

**TL;DR —** I got sick of coding the same lines over and over again, and
copy/pasting between projects. I put that code here to make it easier to reuse.

You can now make CLI/Click-related functionality more portable for your apps
using ``es_client``.

There is not really any change to the base ``Builder`` class, nor the
``ClientArgs`` or ``OtherArgs`` classes, so this is more a function of support
tools and tooling for handling the overriding of config file options with those
supplied at a command-line.

The improvements are visible in ``cli_example.py``.

Some of these changes include:

  * Functions that simplify overriding configuration file options with ones
    from the command-line. Reduces dozens of lines of code to a single
    function call: ``get_args(ctx.params, config)``, which overrides the values
    from ``config`` with the command-line parameters from Click.
  * Re-usable ``cli_opts`` Click option wrapper function, complete with overrides.
    This is demonstrated with the hidden options vs. ``show-all-options`` in
    ``cli_example.py``.
  * Support basic logging configuration with ``default``, ``json``, and ``ecs``
  * New modules in ``es_client.helpers``:
      * ``config``
      * ``logging``
  * Lots and lots of tests, both unit and integration.
  * Updated all documentation for modules, functions, and classes accordingly.


8.12.0 (29 January 2024)
------------------------

**Changes**

  * Dependency version bumps in this release:
      * ``elasticsearch8==8.12.0``
      * ``voluptuous>=0.14.1``
      * ``certifi>=2023.11.17``
  
8.11.0 (15 November 2023)
-------------------------

**Changes**

  * Dependency version bumps in this version:
      * ``elasticsearch8==8.11.0``
  * Replace ``Mock`` with ``unittest.Mock`` in unit tests.
  * Add Python 3.12 as a supported version (tested).

8.10.3 (2 October 2023)
-----------------------

**Fixes**

Missed a few of the hidden options, and found a way to force the help output to
show for ``show-all-options`` without needing to add ``--help`` afterwards.

8.10.2 (2 October 2023)
-----------------------

**Announcement**

Again, no change in functionality. Changing some of the CLI options to be
hidden by default (but still usable). These options include:

  * ``bearer_auth``
  * ``opaque_id``
  * ``http_compress``
  * ``ssl_assert_hostname``
  * ``ssl_assert_fingerprint``
  * ``ssl_version``
  * ``master-only``
  * ``skip_version_test``

This will hopefully not surprise anyone too badly. I haven't heard of anyone
using these options yet. The CLI examle has been configured with a
``show-all-options`` command that will show all of the hidden options.

8.10.1 (29 September 2023)
--------------------------

**Announcement**

No change in functionality. Adding some ways to have CLI building via Click
easier for end users by making the basic arguments part of the ``es_client``
code. This is shown in the Example in the docs and in the code in 
file ``example_cli.py``.

8.10.0 (25 September 2023)
--------------------------

**Announcement**

The only changes in this release are dependency version bumps:

  * ``elasticsearch8==8.10.0``
  * ``click==8.1.7``

8.9.0 (31 July 2023)
--------------------

**Announcement**

The only changes in this release are dependency version bumps:

  * ``elasticsearch8==8.9.0``
  * ``click==8.1.6``
  * ``certifi==2023.7.22``

8.8.2.post1 (18 July 2023)
--------------------------

**Breakfix**

  * PyYAML 6.0.1 was released to address Cython 3 compile issues.

8.8.2 (12 July 2023)
--------------------

**Announcement**

Apologies for another delayed release. Weddings and funerals and graduations
have kept me from releasing anything in the interim.

**Changes**

  * Bring up to date with Elasticsearch 8.8.2 Python client
  * Other updated Python modules:
      * ``certifi>=2023.5.7``
      * ``click==8.1.4``

8.7.0 (12 April 2023)
---------------------

**Announcement**

Apologies for the delayed release. I have had some personal matters that had me
out of office for several weeks.

**Changes**

  * Bring up to date with Elasticsearch 8.7.0 Python client.
  * Add ``mock`` to the list of modules for testing

8.6.2.post1 (23 March 2023)
---------------------------

**Announcement**

  Late 8.6.2 post-release.

**Changes**

  * Fix certificate detection. See #33.
  * Add one-line API Key support (the Base64 encoded one).
  * Update docs to reflect base64 token API Key functionality.

8.6.2 (19 February 2023)
------------------------

**Announcement**

Version sync with released Elasticsearch Python module.

**Changes**

  * Fix ``cloud_id`` and ``hosts`` collision detection and add test to cover this case.
  * Code readability improvements (primarily for documentation).
  * Documentation readability improvements, and improved cross-linking.
  * Add example cli script to docs.

8.6.1.post1 (30 January 2023)
-----------------------------

**Announcement**

Even though I had a test in place for catching and fixing the absence of a port with ``https``,
it didn't work in the field. Fix included.

**Changes**

  * Fixed unverified URL schema issue.
  * Found and corrected another place where passwords were being logged inappropriately.

8.6.1 (30 January 2023)
-----------------------

**Announcement**

With all of these changes, I kept this in-house and did local builds and ``pip`` imports until
I worked it all out.

**Changes**

  * Circular imports between ``es_client.helpers.utils`` and ``es_client.helpers.schemacheck``
    broke things. Since ``password_filter`` is not presently being used by anything else,
    I moved it to ``schemacheck.py``.
  * Use ``hatch`` and ``hatchling`` for package building instead of ``flit``.
  * Update ``elasticsearch8`` dependency to ``8.6.1``
  * Removed the ``requirements.txt`` file as this is now handled by ``pyproject.toml`` and
    doing ``pip install .`` to grab dependencies and install them. YAY! Only one place to
    track dependencies now!!!
  * Removed the ``MANIFEST.in`` file as this is now handled by ``pyproject.toml`` as well.
  * Update the docs build settings to use Python 3.11 and ``elasticsearch8==8.6.1``

8.6.0.post6 (26 January 2023)
-----------------------------

**Announcement**

I'm just cranking these out today! The truth is, I'm catching more things with the increased
scrutiny of heavy Curator testing. This is good, right?

**Changes**

  * Discovered that passwords were being logged. Added a function to replace any value
    from a key (from ``KEYS_TO_REDACT`` in ``defaults.py``) with ``REDACTED``. Keys are
    ``['password', 'basic_auth', 'bearer_auth', 'api_key', 'id', 'opaque_id']``

8.6.0.post5 (26 January 2023)
-----------------------------

**Changes**

  * Python 3.11 was unofficially supported in 8.6.0.post4. It is now officially listed
    in ``pyproject.toml`` as a supported version.
  * Discovered that Builder was not validating Elasticsearch host URLs, and not catching
    those lead to an invisible failure in Curator.

8.6.0.post4 (26 January 2023)
-----------------------------

**Changes**

  * Fix an example in ``README.rst`` that showed the old and no longer viable way to
    get the client. New example reflects the current way.
  * Purge older setuptools files ``setup.py`` and ``setup.cfg`` in favor of building
    with ``flit``, using ``pyproject.toml``. Testing and dependencies here should install
    properly with ``pip install -U '.[test]'``. After this, testing works with ``pytest``,
    or ``pytest --cov=es_client --cov-report html:cov_html`` (``cov_html`` was added to
    ``.gitignore``). These changes appear to be necessary to build functional packages
    for Python 3.11.
  * Building now works with ``flit``. First ``pip install flit``, then ``flit build``.

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
