import os
import sys
import shutil
import pkg_resources
import logging
import stat
import zc.buildout
import zc.recipe.egg

class Recipe:
    def __init__(self, buildout, name, options):
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)
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
        
        self.location = os.path.join(
                                    self.buildout["buildout"]["parts-directory"], 
                                    self.name
                        )

        if options.has_key('eggs'):
            options['eggs'] += '\nmoin'
        else:
            options['eggs'] = 'moin'
        #TODO: Verificar si el protocolo es FCGI y flup no esta en los eggs que lo instale


    def install(self, update=False):
        # Crear archivo de configuracion en parts/part_name/wikiconf.py
        if not update:
            if os.path.exists(self.location):
                shutil.rmtree(self.location)
        
        self.make_wiki_bin()
        self.copy_data_wiki()
        
        protocol = self.options.get('protocol', None)
        if protocol:
            if protocol == 'fcgi':
                self.make_protocol_script(FCGI_TEMPLATE, 'moin.fcgi')
            elif protocol == 'wsgi':
                self.make_protocol_script(WSGI_TEMPLATE, 'moin.wsgi')
            else:
                self.logger.warning("'protocol' is not not recognized")
            #TODO: More protocols
                
        else:
            self.logger.warning("'protocol' is not defined")
                    
        return self.options.created()


    def update(self):
        return self.install(update=True)
        
    def make_wiki_bin(self):
        reqs,ws     = self.egg.working_set()
        extra_paths = self.options.get('extra-paths', '').split()
        extra_paths.append(self.location)
        
        zc.buildout.easy_install.scripts(
            [(self.name, 'MoinMoin.script.moin', 'run')], 
            ws, 
            sys.executable,
            self.options['bin-directory'],
            extra_paths = extra_paths,
        )
        
        
    def make_wiki_conf(self):
        pass
                    
    def make_protocol_script(self, template, script):
        output = template % { 'syspath': self.get_eggs_paths() }
        
        if not os.path.exists(self.location):
            os.mkdir(self.location)
            self.options.created(self.location)

        target = os.path.join(self.location, script)
        f = open(target, "wt")
        f.write(output)
        f.close()
        exec_mask = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        os.chmod(target, os.stat(target).st_mode | exec_mask)
        
        return self.options.created(target)
        
    def get_eggs_paths(self):
        reqs,ws     = self.egg.working_set()
        path        = [pkg.location for pkg in ws]
        path.append(self.location)
        extra_paths = self.options.get('extra-paths', '').split()
        path.extend(extra_paths)
        
        return ",\n    ".join((repr(p) for p in path))

    def copy_data_wiki(self):
        reqs,ws     = self.egg.working_set()        
        moin_egg    = ws.find( pkg_resources.Requirement.parse('moin') )
        moin_location = os.path.join(moin_egg.location, 'share', 'moin')

        data_dir = self.options.get('data_dir', os.path.join(
                                    self.buildout['buildout']['directory']
                                    ,'var',
                                    self.name,))

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        else:
            self.logger.info("Nothing to copy")
            return

        # This is fairly ugly.  The chdir() makes path manipulation in the
        # walk() callback a little easier (less magical), so we'll live
        # with it.
        pwd = os.getcwd()
        os.chdir(moin_location)
        try:
            try:
                os.path.walk(os.curdir, self.copydir, data_dir)
            finally:
                os.chdir(pwd)
        except (IOError, OSError), msg:
            print >>sys.stderr, msg
            sys.exit(1)


    def copydir(self, targetdir, sourcedir, names):
        for name in names[:]:
            src = os.path.join(sourcedir, name)
            if os.path.isfile(src):
                # Copy the file:
                dst = os.path.join(targetdir, src)
                if os.path.exists(dst):
                    continue
                shutil.copyfile(src, dst)
                shutil.copymode(src, dst)
            else:
                # Directory:
                dn = os.path.join(targetdir, sourcedir, name)
                if not os.path.exists(dn):
                    os.mkdir(dn)
                    shutil.copymode(src, dn)


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

WIKI_CONFIG = """

"""