Introduction
============

''collective.recipe.moin'' is a `zc.buildout`_ recipe which creates
a entry point for the wiki engine `MoinMoin`_

Installation
============

It is very simple to use. This is a minimal ''buildout.cfg'' file:::

    [buildout]
    parts = wiki

    [wiki]
    recipe = collective.recipe.moin
    protocol = wsgi
    sitename = My Wiki
    language_default = en


This will create a folder in parts/ called ``wiki`` that contain the egg folder, the config file and the web server deployment file.

When you have a previous config file you can use this::

    [buildout]
    parts = wiki

    [wiki]
    recipe = collective.recipe.moin
    config = /some/path/to/wikiconfig.py
    protocol = wsgi

Parameters
==========

* ``protocol``, Default: ``wsgi``
        This option create a script for the server deployment. Otrer options: ``fcgi``, ``cgi``
    * ``config``, Default: /path/to/parts/name_of_part/wikiconf.py
        If you don't specify a MoinMoin configuration file, the recipe create a basic config file with the parameters filled in the recipe conf.
    * ``title``, Default: ``My Wiki``
        The title of the Wiki app.

Deployment
==========

The apache configuration for this buildout looks like this:::

    WSGIScriptAlias /mysite /home/me/buildout/parts/wiki/moin.wsgi

    <Directory /home/me/buildout>
        Order deny,allow
        Allow from all
    </Directory>

Credits
=======

    * `Erik Rivera`_, initial implementation

.. _zc.buildout: http://pypi.python.org/pypi/zc.buildout
.. _MoinMoin: http://moinmo.in
.. _`Erik Rivera`: http://rivera.pro


