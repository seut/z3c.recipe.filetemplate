import fnmatch
import logging
import os
import re
import stat
import string
import sys
import zc.recipe.egg
import zc.buildout
import zc.buildout.easy_install

ABS_PATH_ERROR = ('%s is an absolute path. Paths must be '
                  'relative to the buildout directory.')

class FileTemplate(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        self.logger=logging.getLogger(self.name)
        # get defaults from extended sections
        defaults = {}
        extends = self.options.get('extends', '').split()
        extends.reverse()
        for section_name in extends:
            defaults.update(self.buildout[section_name])
        for key, value in defaults.items():
            self.options.setdefault(key, value)
        # set up paths for eggs, if given
        if 'eggs' in self.options:
            self.eggs = zc.recipe.egg.Scripts(buildout, name, options)
            orig_distributions, ws = self.eggs.working_set()
            # we want ws, eggs.extra_paths, eggs._relative_paths
            all_paths = [
                zc.buildout.easy_install.realpath(dist.location)
                for dist in ws]
            all_paths.sort()
            all_paths.extend(
                zc.buildout.easy_install.realpath(path)
                for path in self.eggs.extra_paths)
        else:
            all_paths = []
        paths = [path for path in all_paths if not path.endswith('.zip')]
        self.options['os-paths'] = (os.pathsep).join(paths)
        self.options['string-paths'] = ', '.join(repr(p) for p in all_paths)
        self.options['space-paths'] = ' '.join(paths)
        # get and check the files to be created
        self.filenames = self.options.get('files', '*').split()
        self.source_dir = self.options.get('source-directory', '').strip()
        here = self.buildout['buildout']['directory']
        self.destination_dir = here
        if self.source_dir:
            self.recursive = True
            if os.path.isabs(self.source_dir):
                self._user_error(ABS_PATH_ERROR, self.source_dir)
            self.source_dir = os.path.normpath(os.path.join(
                here, self.source_dir))
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
            if self.source_dir:
                if '/' in filename:
                    self._user_error(
                        'Slashes cannot be in file names when a source '
                        'directory is used: %s.',
                        filename)
            else:
                if not os.path.normpath(
                    os.path.join(self.source_dir, filename)
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
                for pattern in source_patterns:
                    # val is relative to
                    matching = fnmatch.filter(file_info, pattern)
                    if matching:
                        unmatched.discard(pattern)
                        found.update(matching)
                for name in found:
                    self.actions.append(file_info[name])
            os.path.walk(
                self.source_dir, visit, None)
        else:
            for val in source_patterns:
                source = os.path.join(self.source_dir, val)
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
        interpreted = self.options.get('interpreted-options')
        if interpreted:
            globs = {'__builtins__': __builtins__, 'os': os, 'sys': sys}
            locs = {'name': name, 'options': options, 'buildout': buildout,
                    'paths': paths, 'all_paths': all_paths}
            for value in interpreted.split():
                if value:
                    key, expression = value.split('=', 1)
                    options[key] = str(eval(expression, globs, locs))
    def _user_error(self, msg, *args):
        msg = msg % args
        self.logger.error(msg)
        raise zc.buildout.UserError(msg)

    def install(self):
        already_exists = [
            rel_path for rel_path, last_mod, st_mode in self.actions
            if os.path.exists(
                os.path.join(self.destination_dir, rel_path[:-3]))
            ]
        if already_exists:
            self._user_error(
                'Destinations already exist: %s. Please make sure that '
                'you really want to generate these automatically.  Then '
                'move them away.', ', '.join(already_exists))
        for rel_path, last_mod, st_mode in self.actions:
            source = os.path.join(self.source_dir, rel_path)
            dest = os.path.join(self.destination_dir, rel_path[:-3])
            mode=stat.S_IMODE(st_mode)
            template=open(source).read()
            template=re.sub(r"\$\{([^:]+?)\}", r"${%s:\1}" % self.name,
                            template)
            self._create_paths(os.path.dirname(dest))
            result=open(dest, "wt")
            result.write(self.options._sub(template, []))
            result.close()
            os.chmod(dest, mode)
            self.options.created(rel_path[:-3])
        return self.options.created()

    def _create_paths(self, path):
        if not os.path.exists(path):
            self._create_paths(os.path.dirname(path))
            os.mkdir(path)
            self.options.created(path)

    def update(self):
        pass
