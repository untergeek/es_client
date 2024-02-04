.. _tutorial:

########
Tutorial
########

*************************
Create A Command-Line App
*************************

Now that we see the power of the command-line that is ready for the taking, what's the next step?
How do you make your own app work with ``es_client``?

As StackOverflow as it may sound, feel free to clone the :ref:`example file <example_file>` and
start there. I've done the ground work so you don't have to.

.. important:: All of these examples assume you have a simple Elasticsearch instance running at
   localhost:9200 that needs no username or password. This can, in fact, be done using the 
   ``docker_test`` scripts included in the Github repository. Run 
   ``docker_test/scripts/create.sh 8.12.0`` to create such an image locally (substitute the version
   of your choice), and ``docker_test/scripts/destroy.sh`` to remove them when you're done. If you
   do not have Docker, or choose to use a different cluster, you're responsible for adding whatever
   configuration options/flags are needed to connect. And I am not at all responsible if you delete
   an index in production because you did something you shouldn't have.

.. _tutorial_step_1:

*****************
Add a New Command
*****************

To make things really simple, we can just add a new command. We already have 2 commands:

.. code-block:: console

   Commands:
     show-all-options  Show all configuration options
     test-connection   Test connection to Elasticsearch

A look at the code shows us where that name came from:

.. code-block:: python

   @run.command(context_settings=context_settings())
   @click.pass_context
   def test_connection(ctx):
       """
       Test connection to Elasticsearch
       """
       # Because of `@click.pass_context`, we can access `ctx.obj` here from the `run` function
       # that made it:
       es_client = get_client(configdict=ctx.obj['configdict'])

       # If we're here, we'll see the output from GET http(s)://hostname.tld:PORT
       click.secho('\nConnection result: ', bold=True)
       click.secho(f'{es_client.info()}\n')

Yeah, it really is that simple. The name of the function becomes the name of the command. Also note
that ``@run.command()`` decorator above the ``@click.pass_context`` decorator. These are both
absolutely necessary. The ``@run.command()`` decorator gets its ``run`` from the initial function.
All you really need to know is that this decorator means, "add this function name as a command to 
the existing, decorated function ``run``". You probably scrolled back and noticed all of the
decorators above the ``run`` function and recognized that's where all of the options come from.
That's it! It's actually easier than it looks.

So let's copy the entire ``test_connection`` function and make a few changes:

.. code-block:: python

   @run.command(context_settings=context_settings())
   @click.pass_context
   def delete_index(ctx):
       """
       Delete an Elasticsearch Index
       """
       # Because of `@click.pass_context`, we can access `ctx.obj` here from the `run` function
       # that made it:
       es_client = get_client(configdict=ctx.obj['configdict'])

       # If we're here, we'll see the output from GET http(s)://hostname.tld:PORT
       click.secho('\nConnection result: ', bold=True)
       click.secho(f'{es_client.info()}\n')

So what's different now? We renamed our copied function to ``delete_index``. We also changed the
Python docstring--that's the part in between the triple quotes underneath the function name. Let's
see what this looks like when we run the basic help output:

.. code-block:: console

   python run_script.py -h

Now the output has a difference at the bottom:

.. code-block:: console

   Commands:
     delete-index      Delete an Elasticsearch Index
     show-all-options  Show all configuration options
     test-connection   Test connection to Elasticsearch

Cool! Now our new command, ``delete-index`` is starting to take shape. Did you see how the value in
the docstring became the description for our new command?

.. note:: Our function is named ``delete_index`` but the command is hyphenated: ``delete-index``.

.. _tutorial_step_2:

*************
Add an Option
*************

While our function is named differently and has a different description, it's identical to the
``test-connections`` command still. Let's make a few more changes.

.. code-block:: python

   @run.command(context_settings=context_settings())
   @click.option('--index', help='An index name', type=str)
   @click.pass_context
   def delete_index(ctx, index):
       """
       Delete an Elasticsearch Index
       """
       # Because of `@click.pass_context`, we can access `ctx.obj` here from the `run` function
       # that made it:
       es_client = get_client(configdict=ctx.obj['configdict'])

       # If we're here, we'll see the output from GET http(s)://hostname.tld:PORT
       click.secho('\nConnection result: ', bold=True)
       click.secho(f'{es_client.info()}\n')

So, two more changes. We added a new option via one of those clever decorators. Please note that
this is the direct way to add an option. The ones you see in the example are using stored default
options. For right now, this is all we need. This decorator is telling Click that the command
``delete_index`` now needs to have an option, ``--index``, which has its own helpful description,
and we tell Click to reject any non-string values because ``type=str``.

Also note that we need to add our new option as a variable in the function definition:

.. code-block:: python

   def delete_index(ctx, index):

.. note:: Any options or arguments added need to have variables added this way in the same order as
   the decorators.

Let's run this and see what we get. This time we'll actually run the help on our new command:

.. code-block:: console

   python run_script.py delete-index -h

The output from this is pretty cool:

.. code-block:: console

   Usage: run_script.py delete-index [OPTIONS]
   
     Delete an Elasticsearch Index
   
   Options:
     --index TEXT  An index name
     -h, --help    Show this message and exit.

So here we see our command name, ``delete-index``, a positional holder for ``OPTIONS`` which is in
square braces because they are optional, our docstring again, and a list of accepted options which
now includes ``--index``, and a standard help block.

.. _tutorial_step_3:

**************
Add in Logging
**************

This won't actually delete an index yet. We'll get to that part in a bit. First, let's add some
logging:

.. code-block:: python

   @run.command(context_settings=context_settings())
   @click.option('--index', help='An index name', type=str)
   @click.pass_context
   def delete_index(ctx, index):
       """
       Delete an Elasticsearch Index
       """
       logger = logging.getLogger(__name__)
       logger.info("Let's delete index: %s", index)
       logger.info("But first, let's connect to Elasticsearch...")
       es_client = get_client(configdict=ctx.obj['configdict'])

So we deleted some comments, and added 3 lines. The first one says, "create an instance of logger."
The second and third use that ``logger`` at ``info`` level to write some log lines. The first
includes a string substitution ``%s`` which means, "put the contents of variable ``index`` where the
``%s`` is. It should be noted that logging was already "enabled" in the ``run`` function by the
``configure_logging(ctx)`` function call. Whatever log options were set when we got to that point,
whether from a YAML configuration file via ``--config``, or by ``--loglevel``, ``--logfile``, or
``--logformat``, will be in effect before our ``delete_index`` function is ever called.

So let's run this much. Go ahead and put in a dummy index name here. There's no deletes happening
yet:

.. code-block:: console

   python run_script.py delete-index --index myindex

Note that we are omitting the help flag this time.

.. code-block:: console

   2024-02-03 23:44:25,569 INFO      Let's delete index: myindex
   2024-02-03 23:44:25,569 INFO      But first, let's connect to Elasticsearch...

Look at that! We're getting more done. 

.. _tutorial_step_4:

************************
Add the try/except Logic
************************

So now we have a logger and an Elasticsearch client. Let's add in a delete API call with some "try"
logic and see what happens:

.. code-block:: python

   @run.command(context_settings=context_settings())
   @click.option('--index', help='An index name', type=str)
   @click.pass_context
   def delete_index(ctx, index):
       """
       Delete an Elasticsearch Index
       """
       logger = logging.getLogger(__name__)
       logger.info("Let's delete index: %s", index)
       logger.info("But first, let's connect to Elasticsearch...")
       es_client = get_client(configdict=ctx.obj['configdict'])
       logger.info("We're connected!")
       result = 'FAIL'
       try:
           result = es_client.indices.delete(index=index)
       except NotFoundError as exc:
           logger.error("While trying to delete: %s, an error occurred: %s", index, exc.error)
       logger.info('Index deletion result: %s', result)

You probably thought I wasn't going to notice that we are attempting to delete an index on an empty
test cluster. I know what the score is here. The lines we've added here are not just to inform us
when we try to delete an index that's not there, but also to keep the program from dying
unexpectedly. If we did not put in this ``try`` / ``except`` block, the program would have exited
silently after logging, "We're connected". Go ahead. Try it and see.

.. code-block:: console

   2024-02-04 00:24:17,409 INFO      Let's delete index myindex
   2024-02-04 00:24:17,409 INFO      But first, let's connect to Elasticsearch...
   2024-02-04 00:24:17,422 INFO      We're connected!
   2024-02-04 00:24:17,424 ERROR     While trying to delete: myindex, an error occurred: index_not_found_exception
   2024-02-04 00:24:17,424 INFO      Index deletion result: FAIL

FAIL? Wait, why am I here?

.. _tutorial_step_5:

***************
COPY PASTE! GO!
***************

Well, I don't blame you for not wanting to waste your time. So what good is it that we have a delete
function without any indexes to delete?

Hmmmmmmm...

Begin the COPY PASTE! GO!

.. code-block:: python

   @run.command(context_settings=context_settings())
   @click.option('--index', help='An index name', type=str)
   @click.pass_context
   def create_index(ctx, index):
       """
       Create an Elasticsearch Index
       """
       logger = logging.getLogger(__name__)
       logger.info("Let's create index: %s", index)
       logger.info("But first, let's connect to Elasticsearch...")
       es_client = get_client(configdict=ctx.obj['configdict'])
       logger.info("We're connected!")
       result = 'FAIL'
       try:
           result = es_client.indices.create(index=index)
       except BadRequestError as exc:
           logger.error("While trying to create: %s, an error occurred: %s", index, exc.error)
       logger.info('Index creation result: %s', result)

You'll note very few differences here in this copy/paste:

  * Our function name is ``create_index``
  * Our docstring also says ``Create``
  * Our API call is now ``es_client.indices.create`` instead of ``delete``
  * Our ``except`` is looking for ``BadRequestError``. We expect a index we want to create to not
    be found, so a ``NotFoundError`` doesn't make much sense here. Instead, if we try to create an
    index that's already existing, that would be a bad request.
  * Our final log message is indicating a ``creation`` result.

Let's see our main usage/help page tail now:

.. code-block:: console

   Commands:
     create-index      Create an Elasticsearch Index
     delete-index      Delete an Elasticsearch Index
     show-all-options  Show all configuration options
     test-connection   Test connection to Elasticsearch

Look at all those commands now!

.. _tutorial_step_6:

***********************
Let's Run Some Commands
***********************

=====================
Let's create an index
=====================

.. code-block:: console

   python run_script.py create-index --index myindex
   2024-02-04 00:30:45,160 INFO      Let's create index: myindex
   2024-02-04 00:30:45,160 INFO      But first, let's connect to Elasticsearch...
   2024-02-04 00:30:45,174 INFO      We're connected!
   2024-02-04 00:30:45,255 INFO      Index creation result: {'acknowledged': True, 'shards_acknowledged': True, 'index': 'myindex'}

AHA! Our creation result isn't ``FAIL``!

What happens if we run it again, though?

.. code-block:: console

   python run_script.py create-index --index myindex
   2024-02-04 00:32:24,603 INFO      Let's create index: myindex
   2024-02-04 00:32:24,603 INFO      But first, let's connect to Elasticsearch...
   2024-02-04 00:32:24,613 INFO      We're connected!
   2024-02-04 00:32:24,617 ERROR     While trying to create: myindex, an error occurred: resource_already_exists_exception
   2024-02-04 00:32:24,617 INFO      Index creation result: FAIL

FAIL, but to be expected, right?

=====================
Let's delete an index
=====================

.. code-block:: console

   python run_script.py delete-index --index myindex
   2024-02-04 00:33:41,396 INFO      Let's delete index myindex
   2024-02-04 00:33:41,397 INFO      But first, let's connect to Elasticsearch...
   2024-02-04 00:33:41,405 INFO      We're connected!
   2024-02-04 00:33:41,436 INFO      Index deletion result: {'acknowledged': True}

This is pretty fun, right?

.. _tutorial_step_7:

****************
Just Making Sure
****************

So, one last parting idea. Suppose we want to prompt our users with an, "Are you sure you want to
do this?" message. How would we go about doing that?

With the ``confirmation_option()`` decorator, Like this:

.. code-block:: python

   @run.command(context_settings=context_settings())
   @click.option('--index', help='An index name', type=str)
   @click.confirmation_option()
   @click.pass_context
   def delete_index(ctx, index):
       
By adding ``@click.confirmation_option()``, we can make our command ask us to confirm before
proceding:

===========
Help Output
===========

.. code-block:: console

   python run_script.py delete-index -h
   Usage: run_script.py delete-index [OPTIONS]
   
     Delete an Elasticsearch Index
   
   Options:
     --index TEXT  An index name
     --yes         Confirm the action without prompting.
     -h, --help    Show this message and exit.

You can see the ``--yes`` option in there now.

===============
Run and decline
===============

.. code-block:: console

   python run_script.py delete-index --index myindex
   Do you want to continue? [y/N]: N
   Aborted!

===============
Run and confirm
===============

.. code-block:: console

   python run_script.py delete-index --index myindex
   Do you want to continue? [y/N]: y
   2024-02-04 00:43:47,193 INFO      Let's delete index myindex
   2024-02-04 00:43:47,193 INFO      But first, let's connect to Elasticsearch...
   2024-02-04 00:43:47,207 INFO      We're connected!
   2024-02-04 00:43:47,229 INFO      Index deletion result: {'acknowledged': True}

=============================
Run with the ``--yes`` option
=============================

.. code-block:: console

   python run_script.py delete-index --index myindex --yes
   2024-02-04 00:44:29,313 INFO      Let's delete index myindex
   2024-02-04 00:44:29,313 INFO      But first, let's connect to Elasticsearch...
   2024-02-04 00:44:29,322 INFO      We're connected!
   2024-02-04 00:44:29,356 INFO      Index deletion result: {'acknowledged': True}

You can see that it does not prompt you if you specify the flag.

That's it for our little tutorial!