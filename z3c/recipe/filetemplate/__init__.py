##############################################################################
#
# Copyright (c) 2007-2009 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import fnmatch
import logging
import os
import re
import stat
import string
import sys
import traceback
import zc.recipe.egg
import zc.buildout
import zc.buildout.easy_install

ABS_PATH_ERROR = ('%s is an absolute path. Paths must be '
                  'relative to the buildout directory.')

class FileTemplate(object):

    filters = {}
    dynamic_options = {}

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        self.buildout_root = zc.buildout.easy_install.realpath(
            buildout['buildout']['directory'])
        self.logger=logging.getLogger(self.name)
        # get defaults from extended sections
        defaults = {}
        extends = self.options.get('extends', '').split()
        extends.reverse()
        for section_name in extends:
            defaults.update(self.buildout[section_name])
        for key, value in defaults.items():
            self.options.setdefault(key, value)
        relative_paths = self.options.setdefault(
            'relative-paths',
            buildout['buildout'].get('relative-paths', 'false')
            )
        if relative_paths not in ('true', 'false'):
            self._user_error(
                'The relative-paths option must have the value of '
                'true or false.')
        self.relative_paths = relative_paths = (relative_paths == 'true')
        self.paths = paths = []
        # set up paths for eggs, if given
        if 'eggs' in options:
            eggs = zc.recipe.egg.Scripts(buildout, name, options)
            orig_distributions, ws = eggs.working_set()
            paths.extend(
                zc.buildout.easy_install.realpath(dist.location)
                for dist in ws)
            paths.extend(
                zc.buildout.easy_install.realpath(path)
                for path in eggs.extra_paths)
        else:
            paths.extend(
                os.path.join(buildout.options['directory'], p.strip())
                for p in options.get('extra-paths', '').split('\n')
                if p.strip()
                )
        options['_paths'] = '\n'.join(paths)
        # get and check the files to be created
        self.filenames = self.options.get('files', '*').split()
        self.source_dir = self.options.get('source-directory', '').strip()
        here = zc.buildout.easy_install.realpath(
            self.buildout['buildout']['directory'])
        self.destination_dir = here
        if self.source_dir:
            self.recursive = True
            if os.path.isabs(self.source_dir):
                self._user_error(ABS_PATH_ERROR, self.source_dir)
            self.source_dir = zc.buildout.easy_install.realpath(
                os.path.normpath(os.path.join(here, self.source_dir)))
            if not self.source_dir.startswith(here):
                self._user_error(
                    'source-directory must be within the buildout directory')
        else:
            self.recursive = False
            self.options['source-directory'] = ''
            self.source_dir = self.buildout['buildout']['directory']
        source_patterns = []
        for filename in self.filenames:
            if os.path.isabs(filename):
                self._user_error(ABS_PATH_ERROR, filename)
            if not zc.buildout.easy_install.realpath(
                os.path.normpath(os.path.join(self.source_dir, filename))
                ).startswith(self.source_dir):
                # path used ../ to get out of buildout dir
                self._user_error(
                    'source files must be within the buildout directory')
            source_patterns.append('%s.in' % filename)
        unmatched = set(source_patterns)
        unexpected_dirs = []
        self.actions = [] # each entry is tuple of
                          # (relative path, source last-modified-time, mode)
        if self.recursive:
            def visit(ignored, dirname, names):
                relative_prefix = dirname[len(self.source_dir)+1:]
                file_info = {}
                for name in names:
                    val = os.path.join(relative_prefix, name)
                    source = os.path.join(self.source_dir, val)
                    statinfo = os.stat(source)
                    last_modified = statinfo.st_mtime
                    if stat.S_ISREG(statinfo.st_mode):
                        file_info[name] = (
                            val, last_modified, statinfo.st_mode)
                found = set()
                for orig_pattern in source_patterns:
                    parts = orig_pattern.split('/')
                    dir = os.path.sep.join(parts[:-1])
                    pattern = parts[-1]
                    if (dir and
                        relative_prefix != dir and
                        (dir != '.' or relative_prefix != '')):
                        # if a directory is specified, it must match
                        # precisely.  We also support the '.' directory.
                        continue
                    matching = fnmatch.filter(file_info, pattern)
                    if matching:
                        unmatched.discard(orig_pattern)
                        found.update(matching)
                for name in found:
                    self.actions.append(file_info[name])
            os.path.walk(
                self.source_dir, visit, None)
        else:
            for val in source_patterns:
                source = zc.buildout.easy_install.realpath(
                    os.path.join(self.source_dir, val))
                if os.path.exists(source):
                    unmatched.discard(val)
                    statinfo = os.stat(source)
                    last_modified = statinfo.st_mtime
                    if not stat.S_ISREG(statinfo.st_mode):
                        unexpected_dirs.append(source)
                    else:
                        self.actions.append(
                            (val, last_modified, statinfo.st_mode))
        # This is supposed to be a flag so that when source files change, the
        # recipe knows to reinstall.
        self.options['_actions'] = repr(self.actions)
        if unexpected_dirs:
            self._user_error(
                'Expected file but found directory: %s',
                ', '.join(unexpected_dirs))
        if unmatched:
            self._user_error(
                'No template found for these file names: %s',
                ', '.join(unmatched))
        # parse interpreted options
        interpreted = self.options.get('interpreted-options')
        if interpreted:
            globs = {'__builtins__': __builtins__, 'os': os, 'sys': sys}
            locs = {'name': name, 'options': options, 'buildout': buildout,
                    'paths': paths, 'all_paths': paths}
            for value in interpreted.split('\n'):
                if value:
                    value = value.split('=', 1)
                    key = value[0].strip()
                    if len(value) == 1:
                        try:
                            expression = options[key]
                        except KeyError:
                            self._user_error(
                                'Expression for key not found: %s', key)
                    else:
                        expression = value[1]
                    try:
                        evaluated = eval(expression, globs, locs)
                    except:
                        self._user_error(
                            'Error when evaluating %r expression %r:\n%s',
                            key, expression, traceback.format_exc())
                    if not isinstance(evaluated, basestring):
                        self._user_error(
                            'Result of evaluating Python expression must be a '
                            'string.  The result of %r expression %r was %r, '
                            'a %s.',
                            key, expression, evaluated, type(evaluated))
                    options[key] = evaluated

    def _user_error(self, msg, *args):
        msg = msg % args
        self.logger.error(msg)
        raise zc.buildout.UserError(msg)

    def install(self):
        already_exists = [
                rel_path[:-3] for rel_path, last_mod, st_mode in self.actions
            if os.path.exists(
                os.path.join(self.destination_dir, rel_path[:-3]))
            ]
        if already_exists:
            self._user_error(
                'Destinations already exist: %s. Please make sure that '
                'you really want to generate these automatically.  Then '
                'move them away.', ', '.join(already_exists))
        self.seen = []
        # We throw ``seen`` away right now, but could move template
        # processing up to __init__ if valuable.  That would mean that
        # templates would be rewritten even if a value in another
        # section had been referenced; however, it would also mean that
        # __init__ would do virtually all of the work, with install only
        # doing the writing.
        for rel_path, last_mod, st_mode in self.actions:
            source = os.path.join(self.source_dir, rel_path)
            dest = os.path.join(self.destination_dir, rel_path[:-3])
            mode=stat.S_IMODE(st_mode)
            # we process the file first so that it won't be created if there
            # is a problem.
            processed = Template(source, dest, self).substitute()
            self._create_paths(os.path.dirname(dest))
            result=open(dest, "wt")
            result.write(processed)
            result.close()
            os.chmod(dest, mode)
            self.options.created(rel_path[:-3])
        return self.options.created()

    def _create_paths(self, path):
        if not os.path.exists(path):
            self._create_paths(os.path.dirname(path))
            os.mkdir(path)
            self.options.created(path)

    def _call_and_log(self, callable, args, message_generator):
        try:
            return callable(*args)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # Argh.  Would like to raise wrapped exception.
            colno, lineno = self.get_colno_lineno(start)
            msg = message_generator(lineno, colno)
            self.logger.error(msg, exc_info=True)
            raise

    def update(self):
        pass


class Template:
    # Heavily hacked from--"inspired by"?--string.Template
    pattern = re.compile(r"""
    \$(?:
      \${(?P<escaped>[^}]*)} |           # Escape sequence of two delimiters.

      {((?P<section>[-a-z0-9 ._]+):)?    # Optional section name.
       (?P<option>[-a-z0-9 ._]+)         # Required option name.
       (?P<path_extension>/[^|}]+/?)?    # Optional path extensions.
       ([ ]*(?P<filters>(\|[ ]*[-a-z0-9._]+[ ]*)+))?
                                         # Optional filters.
        } |

      {(?P<invalid>[^}]*})               # Other ill-formed delimiter exprs.
    )
    """, re.IGNORECASE | re.VERBOSE)

    def __init__(self, source, destination, recipe):
        self.source = source
        self.destination = zc.buildout.easy_install.realpath(destination)
        self.recipe = recipe
        self.template = open(source).read()

    def get_colno_lineno(self, i):
        lines = self.template[:i].splitlines(True)
        if not lines:
            colno = 1
            lineno = 1
        else:
            colno = len(lines[-1]) + 1
            lineno = len(lines)
        return colno, lineno

    def _get(self, section, option, start):
        if section is None:
            section = self.recipe.name # This sets up error messages properly.
        if section == self.recipe.name:
            factory = self.recipe.dynamic_options.get(option)
            if factory is not None:
                return self.recipe._call_and_log(
                    factory, (self, start, option),
                    lambda lineno, colno: (
                        'Dynamic option %r in line %d, col %d of %s '
                        'crashed.') % (option, lineno, colno, self.source))
            # else...
            options = self.recipe.options
        elif section in self.recipe.buildout:
            options = self.recipe.buildout[section]
        else:
            value = options = None
        if options is not None:
            value = options.get(option, None, self.recipe.seen)
        if value is None:
            colno, lineno = self.get_colno_lineno(start)
            raise zc.buildout.buildout.MissingOption(
                "Option '%s:%s', referenced in line %d, col %d of %s, "
                "does not exist." %
                (section, option, lineno, colno, self.source))
        return value

    def substitute(self):
        def convert(mo):
            start = mo.start()
            # Check the most common path first.
            option = mo.group('option')
            if option is not None:
                section = mo.group('section')
                val = self._get(section, option, start)
                path_extension = mo.group('path_extension')
                filters = mo.group('filters')
                if path_extension is not None:
                    val = os.path.join(val, *path_extension.split('/')[1:])
                if filters is not None:
                    for filter_name in filters.split('|')[1:]:
                        filter_name = filter_name.strip()
                        filter = self.recipe.filters.get(filter_name)
                        if filter is None:
                            colno, lineno = self.get_colno_lineno(start)
                            raise ValueError(
                                'Unknown filter %r '
                                'in line %d, col %d of %s' %
                                (filter_name, lineno, colno, self.source))
                        val = self.recipe._call_and_log(
                            filter, (val, self, start, filter_name),
                            lambda lineno, colno: (
                                'Filter %r in line %d, col %d of %s '
                                'crashed processing value %r') % (
                                filter_name, lineno, colno, self.source, val))
                # We use this idiom instead of str() because the latter will
                # fail if val is a Unicode containing non-ASCII characters.
                return '%s' % (val,)
            escaped = mo.group('escaped')
            if escaped is not None:
                return '${%s}' % (escaped,)
            invalid = mo.group('invalid')
            if invalid is not None:
                colno, lineno = self.get_colno_lineno(mo.start('invalid'))
                raise ValueError(
                    'Invalid placeholder %r in line %d, col %d of %s' %
                    (mo.group('invalid'), lineno, colno, self.source))
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern) # programmer error, AFAICT
        return self.pattern.sub(convert, self.template)


############################################################################
# Filters
def filter(func):
    "Helper function to register filter functions."
    FileTemplate.filters[func.__name__.replace('_', '-')] = func
    return func

@filter
def capitalize(val, template, start, filter):
    return val.capitalize()

@filter
def title(val, template, start, filter):
    return val.title()

@filter
def upper(val, template, start, filter):
    return val.upper()

@filter
def lower(val, template, start, filter):
    return val.lower()

@filter
def path_repr(val, template, start, filter):
    # val is a path.
    return _maybe_relativize(
        val, template,
        lambda p: "_z3c_recipe_filetemplate_path_repr(%r)" % (p,),
        repr)

@filter
def shell_path(val, template, start, filter):
    # val is a path.
    return _maybe_relativize(
        val, template,
        lambda p: '"$Z3C_RECIPE_FILETEMPLATE_BASE"/%s' % (p,),
        lambda p: p)

# Helpers hacked from zc.buildout.easy_install.
def _maybe_relativize(path, template, relativize, absolutize):
    path = zc.buildout.easy_install.realpath(path)
    if template.recipe.relative_paths:
        buildout_root = template.recipe.buildout_root
        if path == buildout_root:
            return relativize(os.curdir)
        destination = template.destination
        common = os.path.dirname(os.path.commonprefix([path, destination]))
        if (common == buildout_root or
            common.startswith(os.path.join(buildout_root, ''))
            ):
            return relativize(_relative_path(common, path))
    return absolutize(path)

def _relative_path(common, path):
    """Return the relative path from ``common`` to ``path``.

    This is a helper for _relativitize, which is a helper to
    _relative_path_and_setup.
    """
    r = []
    while 1:
        dirname, basename = os.path.split(path)
        r.append(basename)
        if dirname == common:
            break
        assert dirname != path, "dirname of %s is the same" % dirname
        path = dirname
    r.reverse()
    return os.path.join(*r)


############################################################################
# Dynamic options
def dynamic_option(func):
    "Helper function to register dynamic options."
    FileTemplate.dynamic_options[func.__name__.replace('_', '-')] = func
    return func

@dynamic_option
def os_paths(template, start, name):
    return os.pathsep.join(
        shell_path(path, template, start, 'os-paths')
        for path in template.recipe.paths)

@dynamic_option
def string_paths(template, start, name):
    colno, lineno = template.get_colno_lineno(start)
    separator = ',\n' + ((colno - 1) * ' ')
    return separator.join(
        path_repr(path, template, start, 'string-paths')
        for path in template.recipe.paths)

@dynamic_option
def space_paths(template, start, name):
    return ' '.join(
        shell_path(path, template, start, 'space-paths')
        for path in template.recipe.paths)

@dynamic_option
def shell_relative_path_setup(template, start, name):
    if template.recipe.relative_paths:
        depth = _relative_depth(
            template.recipe.buildout['buildout']['directory'],
            template.destination)
        value = SHELL_RELATIVE_PATH_SETUP
        if depth:
            value += '# Ascend to buildout root.\n'
            value += depth * SHELL_DIRNAME
        else:
            value += '# This is the buildout root.\n'
        return value
    else:
        return ''

SHELL_RELATIVE_PATH_SETUP = '''\
# Get full, non-symbolic-link path to this file.
Z3C_RECIPE_FILETEMPLATE_FILENAME=`\\
    readlink -f "$0" 2>/dev/null || \\
    realpath "$0" 2>/dev/null || \\
    type -P "$0" 2>/dev/null`
# Get directory of file.
Z3C_RECIPE_FILETEMPLATE_BASE=`dirname ${Z3C_RECIPE_FILETEMPLATE_FILENAME}`
'''

SHELL_DIRNAME = '''\
Z3C_RECIPE_FILETEMPLATE_BASE=`dirname ${Z3C_RECIPE_FILETEMPLATE_BASE}`
'''

@dynamic_option
def python_relative_path_setup(template, start, name):
    if template.recipe.relative_paths:
        depth = _relative_depth(
            template.recipe.buildout['buildout']['directory'],
            template.destination)
        value = PYTHON_RELATIVE_PATH_SETUP_START
        if depth:
            value += '# Ascend to buildout root.\n'
            value += depth * PYTHON_DIRNAME
        else:
            value += '# This is the buildout root.\n'
        value += PYTHON_RELATIVE_PATH_SETUP_END
        return value
    else:
        return ''

PYTHON_RELATIVE_PATH_SETUP_START = '''\
import os, imp
# Get path to this file.
if __name__ == '__main__':
    _z3c_recipe_filetemplate_filename = __file__
else:
    # If this is an imported module, we want the location of the .py
    # file, not the .pyc, because the .py file may have been symlinked.
    _z3c_recipe_filetemplate_filename = imp.find_module(__name__)[1]
# Get the full, non-symbolic-link directory for this file.
_z3c_recipe_filetemplate_base = os.path.dirname(
    os.path.abspath(os.path.realpath(_z3c_recipe_filetemplate_filename)))
'''

PYTHON_DIRNAME = '''\
_z3c_recipe_filetemplate_base = os.path.dirname(
    _z3c_recipe_filetemplate_base)
'''

PYTHON_RELATIVE_PATH_SETUP_END = '''\
def _z3c_recipe_filetemplate_path_repr(path):
    "Return absolute version of buildout-relative path."
    return os.path.join(_z3c_recipe_filetemplate_base, path)
'''

def _relative_depth(common, path):
    # Helper ripped from zc.buildout.easy_install.
    """Return number of dirs separating ``path`` from ancestor, ``common``.

    For instance, if path is /foo/bar/baz/bing, and common is /foo, this will
    return 2--in UNIX, the number of ".." to get from bing's directory
    to foo.
    """
    n = 0
    while 1:
        dirname = os.path.dirname(path)
        if dirname == path:
            raise AssertionError("dirname of %s is the same" % dirname)
        if dirname == common:
            break
        n += 1
        path = dirname
    return n
