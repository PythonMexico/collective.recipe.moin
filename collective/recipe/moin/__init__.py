import os
import sys
import shutil
import pkg_resources
import logging
import re
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

        self.location = options['location'] = os.path.join( 
                buildout['buildout']['parts-directory'],
                self.name,
            )
        
        self.location = options['location']
        
        if 'data_dir' in options:
            self.data_dir = options['data_dir']
        else:    
            self.data_dir = os.path.join(
                                    self.buildout['buildout']['directory']
                                    ,'var',
                                    self.name,)
                                    
            options['data_dir'] = self.data_dir

        if 'eggs' in options:
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
        
        self.copy_data_wiki()
        self.make_wiki_config()
        
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
        
        
    def make_wiki_config(self):
        template = WIKI_CONFIG
        if 'wiki_config' in self.options:
            template = open(self.options['wiki_config']).read()
        
        if not 'sitename' in self.options:
            self.options['sitename'] = 'Untitled Wiki'
        
        if not 'mount' in self.options:
            self.options['mount'] = ''
            
        if not 'language_default' in self.options:
            self.options['language_default'] = 'en'
            
        if not 'page_front_page' in self.options:
            self.options['page_front_page'] = 'FrontPage'
            
        template=re.sub(r"\$\{([^:]+?)\}", r"${%s:\1}" % self.name, template)
        output = self.options._sub(template, [])
        
        target = os.path.join(self.location, 'wikiconfig.py')
        
        if not os.path.exists(self.location):
            os.mkdir(self.location)
            self.options.created(self.location)
        
        f = open(target, "wt")
        f.write(output)
        f.close()
                            
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

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
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
                os.path.walk(os.curdir, self.copydir, self.data_dir)
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
# -*- coding: utf-8 -*-

import os

from MoinMoin.config import multiconfig, url_prefix_static


class Config(multiconfig.DefaultConfig):
    wikiconfig_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = '${data_dir}'
    data_dir = os.path.join(instance_dir, 'data', '') # path with trailing /
    data_underlay_dir = os.path.join(instance_dir, 'underlay', '') # path with trailing /
    url_prefix_static = '${mount}' + url_prefix_static

    sitename = u'${sitename}'
    logo_string = u'<img src="%s/common/moinmoin.png" alt="MoinMoin Logo">' % url_prefix_static
    page_front_page = u'${page_front_page}'
    
    navi_bar = [
        #u'%(page_front_page)s',
        u'RecentChanges',
        u'FindPage',
        u'HelpContents',
    ]

    theme_default = 'modern'
    language_default = '${language_default}'

    page_category_regex = ur'(?P<all>Category(?P<key>(?!Template)\S+))'
    page_dict_regex = ur'(?P<all>(?P<key>\S+)Dict)'
    page_group_regex = ur'(?P<all>(?P<key>\S+)Group)'
    page_template_regex = ur'(?P<all>(?P<key>\S+)Template)'

    show_hosts = 1

    #interwikiname = u'UntitledWiki'
    #show_interwiki = 1

    #superuser = [u"YourName", ]

    #acl_rights_before = u"YourName:read,write,delete,revert,admin"

    #password_checker = None # None means "don't do any password strength checks"

    #mail_smarthost = ""
    #mail_from = u""
    #mail_login = ""

    #chart_options = {'width': 600, 'height': 300}

"""
