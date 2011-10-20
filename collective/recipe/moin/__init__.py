import logging
import os
import stat
import zc.buildout
from zc.recipe.egg.egg import Eggs

WSGI_TEMPLATE = """\
import sys
sys.path[0:0] = [
  %(syspath)s,	
  ]

from MoinMoin.web.serving import make_application

application = make_application(shared=True)

"""
FCGI_TEMPLATE = """\
import sys
sys.path[0:0] = [
  %(syspath)s,
  ]
from MoinMoin import log
from MoinMoin.web.serving import make_application
logging = log.getLogger(__name__)

application = make_application(shared=True)

try:
    from flup.server.fcgi import WSGIServer
except ImportError:
    logging.warning("No flup-package installed, only basic CGI support is available.")
    from MoinMoin.web._fallback_cgi import WSGIServer

WSGIServer(application).run()
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
        

        if options.has_key('eggs'):
            options['eggs'] += '\nmoin'
        else:
            options['eggs'] = 'moin'
        #TODO: Verificar si el protocolo es FCGI y flup no esta en los eggs que lo instale


    def install(self):
        # Instalar MoinMoin desde egg
        # Copiar wiki/data a var/wiki/data
        # Crear parts/part_name
        # Crear archivo de configuracion en parts/part_name/wikiconf.py
        # Crear bin/moin con la ruta parts/part_name/wikiconf.py
        # Crear parts/part_name/moin.wsgi con la ruta de parts/part_name/wikiconf.py
        
        protocol = self.options.get('protocol', None)
        if protocol:
            if protocol == 'fcgi':
                self.make_protocol_script(FCGI_TEMPLATE, 'moin.fcgi')
            elif protocol == 'wsgi':
                self.make_protocol_script(WSGI_TEMPLATE, 'moin.wsgi')
            else:
                logging.getLogger(self.name).warning("'protocol' is not not recognized")
            #TODO: More protocols
                
        else:
            logging.getLogger(self.name).warning("'protocol' is not defined")
        
        return self.options.created()


    def update(self):
        self.install()
        
    def make_wikiconf(self):
        pass

    def make_protocol_script(self, template, script):
        output = template % { 'syspath': self.get_eggs_paths() }
        location = os.path.join(self.buildout["buildout"]["parts-directory"], self.name)
        
        if not os.path.exists(location):
            os.mkdir(location)
            self.options.created(location)

        target = os.path.join(location, script)
        f = open(target, "wt")
        f.write(output)
        f.close()
        exec_mask = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        os.chmod(target, os.stat(target).st_mode | exec_mask)
        
        return self.options.created(target)
        
    def get_eggs_paths(self):
        egg         = Eggs(self.buildout, self.options["recipe"], self.options)
        reqs,ws     = egg.working_set()
        path        = [pkg.location for pkg in ws]
        extra_paths = self.options.get('extra-paths', '')
        extra_paths = extra_paths.split()
        path.extend(extra_paths)
        
        return ",\n    ".join((repr(p) for p in path))
        