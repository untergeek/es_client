.. _tutorial2:

####################
Tutorial 2: Advanced
####################

**********************
It's the little things
**********************

If you haven't gone through the regular :ref:`tutorial` yet, you should definitely look there first.

The following are little things that will help with making that app more complete.

.. _setting_version:

*******************************
Setting the application version
*******************************

You probably noticed that there's a version output flag in the help/usage output:

.. code-block:: console

   -v, --version                   Show the version and exit.

If you leave this as-is, it will only ever show the version of ``es_client``, so let's see how to
change this to be our own version.

===================
Where's my version?
===================

Most PEP compliant releases of a project will have a ``__version__`` defined somewhere. By default,
Click will attempt to guess the version from that value. It does so successfully with ``es_client``
in our example script.

.. code-block:: python

   @click.version_option(None, '-v', '--version', prog_name="cli_example")

If Click guesses wrong, you can try to tell it which package to check:

.. code-block:: python

   @click.version_option(None, '-v', '--version', pacakge_name='es_client', prog_name="cli_example")

And if that still doesn't work, you can manually specify a version:

.. code-block:: python

   @click.version_option('X.Y.Z', '-v', '--version', prog_name="cli_example")

or directly reference your ``__version__``:

.. code-block:: python

   from es_client import __version__
   # ...
   @click.version_option(__version__, '-v', '--version', prog_name="cli_example")

With regard to ``prog_name``, the documentation says, "The name of the CLI to show in the message. If
not provided, it will be detected from the command."

If I leave ``prog_name`` unset and run the version output, I would see:

.. code-block:: console

   run_script.py, version X.Y.Z

But with it set, I see:

.. code-block:: console

   cli_example, version X.Y.Z

But you can also format the output of this using ``message``. According to the documentation, "The
message to show. The values ``%(prog)s``, ``%(package)s``, and ``%(version)s`` are available.
Defaults to ``"%(prog)s, version %(version)s"``."

So if I set:

.. code-block:: python

   @click.version_option(
      None, '-v', '--version', prog_name="cli_example",
      message='%(prog)s from %(package)s, version %(version)s')

I would see:

.. code-block:: console

   python run_script.py -v                                                                                                  ─╯
   cli_example from es_client, version X.Y.Z

.. _importing:

*****************************************
Importing es_client into your own project
*****************************************

It's all well and good to test against the es_client code, but wouldn't you rather make use of it
in your own code?

=================================
Include es_client as a dependency
=================================

If you're following PEP conventions, your project probably has a ``pyproject.toml`` file. Inside
that file will be a header labeled ``[project]``, and under that section will be a subsection
titled ``dependencies`` followed by a list of modules your project depends on. This is where you
need to list ``es_client`` as a dependency:

.. code-block:: toml

   dependencies = [
       ...
       "es_client==X.Y.Z"
       ...
   ]

You will probably need to do something to make sure it's imported into your virtualenv while you are
coding and testing. Having it installed allows IDEs and similar coding environments to help with
documentation and code completion. Installing dependencies can be accomplished by running:

.. code-block:: console

   pip install -U .

If run from the root of your project, this will install all dependencies in ``pyproject.toml``.

=====================
Import into your code
=====================

Once ``es_client`` is available to your code, you can import it or any of its classes, submodules,
functions and constants. This pattern is visible in the example script at the top of the page:

.. code-block:: python

   from es_client.helpers.config import (
      context_settings, generate_configdict, get_client, get_config,
      options_from_dict)
   from es_client.defaults import OPTION_DEFAULTS, SHOW_EVERYTHING
   from es_client.helpers.logging import configure_logging


==================
"Secret Borrowing"
==================

"Good artists borrow. Great artists steal." (Attributed to Pablo Picasso)

It's completely acceptable and appropriate to copy the :ref:`example script <example_file>` and use
it as the basis for your own application. Why re-invent the wheel when you have a working wheel that
you only need to tweak a bit?

-----------------------------
Add your bits or link to them
-----------------------------

If your code is ready to go and just needs es_client, then you should know what to do now. First,
import the dependencies:

.. code-block:: python

   import click
   from es_client.helpers.config import (
      context_settings, generate_configdict, get_client, get_config,
      options_from_dict)
   from es_client.defaults import OPTION_DEFAULTS, SHOW_EVERYTHING
   from es_client.helpers.logging import configure_logging

Then, create a Click command that will allow you to collect all of the settings needed to create a
client connection:

.. code-block:: python

   @click.group(context_settings=context_settings())
   @options_from_dict(OPTION_DEFAULTS)
   @click.version_option(None, '-v', '--version', prog_name="cli_example")
   @click.pass_context
   def run(ctx, config, hosts, cloud_id, api_token, id, api_key, username, password, bearer_auth,
       opaque_id, request_timeout, http_compress, verify_certs, ca_certs, client_cert, client_key,
       ssl_assert_hostname, ssl_assert_fingerprint, ssl_version, master_only, skip_version_test,
       loglevel, logfile, logformat, blacklist
   ):
       """
       CLI Example 
       
       Any text added to a docstring will show up in the --help/usage output.
   
       Set short_help='' in @func.command() definitions for each command for terse descriptions in the
       main help/usage output, as with show_all_options() in this example.
       """
       ctx.obj['default_config'] = None
       get_config(ctx, quiet=False)
       configure_logging(ctx)
       generate_configdict(ctx)
   
   @run.command()
   @click.pass_context
   def my_command(ctx):
       client = get_client(configdict=ctx.obj['configdict'])
       # your code goes here

This will follow the pattern where you get the credentials and settings in the root-level command,
and then tell it you want to run ``my_command`` where a client connection will be established and
then your code uses it however you like! Note that we use the name of our root-level command as the
name of the decorator: ``@run.command()``. This guarantees that ``my_command`` will be a
sub-command of ``run``.

To run this automatically when this file is called, put this at the end of the file:

.. code-block:: python

   if __name__ == '__main__':
       run()

Calling your script like ``python my_script.py`` will now automatically call your ``run`` function,
and you're on your way!

.. _more_advanced:

****************
Watch This Space
****************

More advanced tutorials will follow!