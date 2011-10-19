import logging
import os
import stat
import zc.buildout
from zc.recipe.egg.egg import Eggs

WSGI_TEMPLATE = """\
import sys
syspaths = [
    %(syspath)s,
    ]

for path in reversed(syspaths):
    if path not in sys.path:
        sys.path[0:0]=[path]

from MoinMoin.web.serving import make_application

application = make_application(shared=True)

"""

class Recipe:
    def __init__(self, buildout, name, options):
        self.buildout=buildout
        self.name=name
        self.options=options
        self.logger=logging.getLogger(self.name)

        buildout['buildout'].setdefault(
            'download-cache',
            os.path.join(buildout['buildout']['directory'], 'downloads'))

        options['location'] = os.path.join( 
            buildout['buildout']['parts-directory'],
            self.name,
            )

        options['bin-directory'] = buildout['buildout']['bin-directory']


    def install(self):
        # Descargar MoinMoin de 'http://static.moinmo.in/files/moin-%s.tar.gz' % (version, )
        # Instalar MoinMoin
        # Copiar wiki/data a var/wiki/data
        # Crear parts/part_name
        # Crear archivo de configuracion en parts/part_name/wikiconf.py
        # Crear bin/moin con la ruta parts/part_name/wikiconf.py
        # Crear parts/part_name/moin.wsgi con la ruta de parts/part_name/wikiconf.py
        
        egg=Eggs(self.buildout, self.options["recipe"], self.options)
        reqs,ws=egg.working_set()
        path=[pkg.location for pkg in ws]
        extra_paths = self.options.get('extra-paths', '')
        extra_paths = extra_paths.split()
        path.extend(extra_paths)

        output=WSGI_TEMPLATE % dict(
            syspath=",\n    ".join((repr(p) for p in path))
            )

        location=os.path.join(self.buildout["buildout"]["parts-directory"],
                              self.name)
        if not os.path.exists(location):
            os.mkdir(location)
            self.options.created(location)

        target=os.path.join(location, "moin.wsgi")
        f=open(target, "wt")
        f.write(output)
        f.close()

        exec_mask=stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        os.chmod(target, os.stat(target).st_mode | exec_mask)
        self.options.created(target)

        return self.options.created()


    def update(self):
        self.install()

