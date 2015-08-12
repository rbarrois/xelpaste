========
xelpaste
========


xelpaste is a Django based pastebin, based on the `dpaste <http://dpaste.de>`_ project.
It's intended to run separately but it is also possible to be installed into an existing Django project like a regular app.

You can find a live example on http://xelpaste.org/.


Installation
============

You may install this software from your distribution packages, or through pip:

.. code-block:: sh

    $ pip install xelpaste

Once installed, you must configure it.
The minimal set of settings is the ``[db]`` section of the ``/etc/xelpaste/config.ini`` file (see below for details).

Once this is configured, you must prepare the database:

.. code-block:: sh

    $ xelpastectl migrate

This will create the database; the last step is to point your WSGI server to ``xelpaste.wsgi``.


Configuration
=============

Xelpaste will read all configuration files matching ``/etc/xelpaste/*.ini``.
Those are ini-style files, defining the following parametes:

Database
--------

Required; these define where snippets will be stored.
Valid options are:

``engine``
    ``str``, the engine to choose.
    Must be one of ``sqlite``, ``mysql``, ``postgresql``; default is ``sqlite``.

``name``
    ``str``, the name of the database, or its path for sqlite.
    Defaults to ``/var/lib/xelpaste/db.sqlite``.

``host``
    ``str``, the host of the database server.

``port``
    ``int``, the port of the database server.

``user``
    ``str``, the login to use to connect to the database server.

``password``
    ``str``, the password for the database


Examples:

.. code-block:: ini

    ; A Postgresql configuration; uses default psql port.
    [db]
    engine = postgresql
    name = xelpaste
    host = psql42.local

.. code-block:: ini

    ; A sample sqlite configuration.
    [db]
    engine = sqlite
    name = /data/replicated/xelpaste/db.sqlite
