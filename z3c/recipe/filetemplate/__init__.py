import os
import string
import logging
import zc.buildout

class FileTemplate(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

    def install(self, update=False):
        here = self.buildout['buildout']['directory']
        filenames = self.options['files'].split()
        logger = logging.getLogger(self.name)

        for filename in filenames:
            if os.path.isabs(filename):
                msg = ('%s is an absolute path. File paths must be '
                       'relative to the buildout directory.' % filename)
                logger.error(msg)
                raise zc.buildout.UserError(msg)

            absname = os.path.join(here, filename)

            if not os.path.exists(absname + '.in'):
                msg = 'No template found at %s.in.' % filename
                logger.error(msg)
                raise zc.buildout.UserError(msg)

            if not update and os.path.exists(absname):
                msg = ('File %s already exists. Please make sure that you '
                       'really want to have it generated automatically.  Then '
                       'move it away.' % filename)
                logger.error(msg)
                raise zc.buildout.UserError(msg)

            templ = string.Template(open(absname + '.in').read())
            outfile = open(absname, 'w')
            outfile.write(templ.substitute(self.options))
            outfile.close()
        return filenames

    def update(self):
        return self.install(update=True)
