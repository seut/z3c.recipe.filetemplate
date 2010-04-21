``z3c.recipe.filetemplate``
***************************

===========
Basic Usage
===========

With the ``z3c.recipe.filetemplate`` buildout recipe you can automate
the generation of text files from templates.  Upon execution, the
recipe will read a number of template files, perform variable
substitution and write the result to the corresponding output files.

The recipe has several features, but it always takes template files with a
``.in`` suffix, processes the template, and writes out the file to the desired
location with the same file mode, and the same name but without the ``.in``
suffix.

For example, consider this simple template for a text file:

    >>> write(sample_buildout, 'helloworld.txt.in',
    ... """
    ... Hello ${world}!
    ... """)

Now let's create a buildout configuration so that we can substitute
the values in this file.  All we have to do is define a part that uses
the ``z3c.recipe.filetemplate`` recipe.  With the ``files`` parameter
we specify one or more files that need substitution (separated by
whitespace).  Then we can add arbitrary parameters to the section.
Those will be used to fill the variables in the template:

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... world = Philipp
    ... """)

After executing buildout, we can see that ``${world}`` has indeed been
replaced by ``Philipp``:

    >>> print system(buildout)
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt')
    Hello Philipp!

If you need to escape the ${...} pattern, you can do so by repeating the dollar
sign.

    >>> update_file(sample_buildout, 'helloworld.txt.in',
    ... """
    ... Hello world! The double $${dollar-sign} escapes!
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt')
    Hello world! The double ${dollar-sign} escapes!

Note that dollar signs alone, without curly braces, are not parsed.

    >>> update_file(sample_buildout, 'helloworld.txt.in',
    ... """
    ... $Hello $$world! $$$profit!
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt')
    $Hello $$world! $$$profit!

Note that the output file uses the same permission bits as found on the input
file.

    >>> import stat
    >>> import os
    >>> input = os.path.join(sample_buildout, 'helloworld.txt.in')
    >>> output = input[:-3]
    >>> os.chmod(input, 0755)
    >>> stat.S_IMODE(os.stat(input).st_mode) == 0755
    True
    >>> stat.S_IMODE(os.stat(output).st_mode) == 0755
    False
    >>> print system(buildout)
    Uninstalling message.
    Installing message.
    >>> stat.S_IMODE(os.stat(output).st_mode) == 0755
    True

Source Folders and Globs
========================

By default, the recipe looks for a ``.in`` file relative to the buildout root,
and places it in the same folder relative to the buildout root.  However, if
you don't want to clutter up the destination folder, you can add a prefix to
the source folder.  Here is an example.

First, we specify a ``source-directory`` in the buildout.  You can specify
``files`` as a filter if desired, but by default it will find any file (ending
with ".in").

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... source-directory = template
    ... world = Philipp
    ... """)

Now we'll make a "template" directory, as listed in the buildout configuration
above, and populate it for our example.

    >>> mkdir(sample_buildout, 'template')
    >>> mkdir(sample_buildout, 'template', 'etc')
    >>> mkdir(sample_buildout, 'template', 'bin')
    >>> write(sample_buildout, 'template', 'etc', 'helloworld.conf.in',
    ... """
    ... Hello ${world} from the etc dir!
    ... """)
    >>> write(sample_buildout, 'template', 'bin', 'helloworld.sh.in',
    ... """
    ... Hello ${world} from the bin dir!
    ... """)
    >>> os.chmod(
    ...     os.path.join(
    ...         sample_buildout, 'template', 'bin', 'helloworld.sh.in'),
    ...     0711)

Notice that, before running buildout, the ``helloworld.txt`` file is still
around, we don't have an etc directory, and the bin directory doesn't have our
``helloworld.sh``.

    >>> ls(sample_buildout)
    -  .installed.cfg
    d  bin
    -  buildout.cfg
    d  develop-eggs
    d  eggs
    -  helloworld.txt
    -  helloworld.txt.in
    d  parts
    d  template
    >>> ls(sample_buildout, 'bin')
    -  buildout

Now we install.  The old "helloworld.txt" is gone, and we now see etc.  Note
that, for the destination, intermediate folders are created if they do not
exist.

    >>> print system(buildout)
    Uninstalling message.
    Installing message.
    >>> ls(sample_buildout)
    -  .installed.cfg
    d  bin
    -  buildout.cfg
    d  develop-eggs
    d  eggs
    d  etc
    -  helloworld.txt.in
    d  parts
    d  template

The files exist and have the content we expect.

    >>> ls(sample_buildout, 'bin')
    - buildout
    - helloworld.sh
    >>> cat(sample_buildout, 'bin', 'helloworld.sh')
    Hello Philipp from the bin dir!
    >>> stat.S_IMODE(os.stat(os.path.join(
    ...     sample_buildout, 'bin', 'helloworld.sh')).st_mode) == 0711
    True
    >>> ls(sample_buildout, 'etc')
    - helloworld.conf
    >>> cat(sample_buildout, 'etc', 'helloworld.conf')
    Hello Philipp from the etc dir!

If you use the ``files`` option along with ``source-directory``, it becomes a
filter.  Every target file must match at least one of the names in ``files``.
Therefore, if we only build .sh files, the etc directory will disappear.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... source-directory = template
    ... files = *.sh
    ... world = Philipp
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.
    >>> ls(sample_buildout)
    -  .installed.cfg
    d  bin
    -  buildout.cfg
    d  develop-eggs
    d  eggs
    -  helloworld.txt.in
    d  parts
    d  template

    >>> ls(sample_buildout, 'bin')
    - buildout
    - helloworld.sh

Also note that, if you use a source directory and your ``files`` specify a
directory, the directory must match precisely.

    >>> # Clean up for later test.
    >>> import shutil
    >>> shutil.rmtree(os.path.join(sample_buildout, 'template', 'etc'))
    >>> os.remove(os.path.join(
    ...     sample_buildout, 'template', 'bin', 'helloworld.sh.in'))

==============
Advanced Usage
==============

Substituting from Other Sections
================================

Substitutions can also come from other sections in the buildout, using the
standard buildout syntax, but used in the template.  Notice
``${buildout:parts}`` in the template below.

    >>> update_file(sample_buildout, 'helloworld.txt.in',
    ... """
    ... Hello ${world}.  I used these parts: ${buildout:parts}.
    ... """)
    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... world = Philipp
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt')
    Hello Philipp.  I used these parts: message.

Path Extensions
===============

Substitutions can have path suffixes using the POSIX "/" path separator.
The template will convert these to the proper path separator for the current
OS.  They also then are part of the value passed to filters, the feature
described next.  Notice ``${buildout:directory/foo/bar.txt}`` in the template
below.

    >>> update_file(sample_buildout, 'helloworld.txt.in',
    ... """
    ... Here's foo/bar.txt in the buildout:
    ... ${buildout:directory/foo/bar.txt}
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt') # doctest: +ELLIPSIS
    Here's foo/bar.txt in the buildout:
    /.../sample-buildout/foo/bar.txt

Filters
=======

You can use pipes within a substitution to filter the original value.  This
recipe provides several filters for you to use.  The syntax is reminiscent of
(and inspired by) POSIX pipes and Django template filters.  For example,
if world = Philipp, ``HELLO ${world|upper}!`` would result in ``HELLO
PHILIPP!``.

A few simple Python string methods are exposed as filters right now:

- capitalize: First letter in string is capitalized.
- lower: All letters in string are lowercase.
- title: First letter of each word in string is capitalized.
- upper: All letters in string are uppercase.

Other filters are important for handling paths if buildout's relative-paths
option is true.  See `Working with Paths`_ for more details.

- path-repr: Converts the path to a Python expression for the path.  If
  buildout's relative-paths option is false, this will simply be a repr
  of the absolute path.  If relative-paths is true, this will be a
  function call to convert a buildout-relative path to an absolute path;
  it requires that ``${python-relative-path-setup}`` be included earlier
  in the template.

- shell-path: Converts the path to a shell expression for the path.  Only
  POSIX is supported at this time.  If buildout's relative-paths option
  is false, this will simply be the absolute path.  If relative-paths is
  true, this will be an expression to convert a buildout-relative path
  to an absolute path; it requires that ``${shell-relative-path-setup}``
  be included earlier in the template.

Combining the three advanced features described so far, then, if the
buildout relative-paths option were false, we were in a POSIX system, and
the sample buildout were in the root of the system, the template
expression ``${buildout:bin-directory/data/initial.csv|path-repr}``
would result in ``'/sample-buildout/bin/data/initial.csv'``.

Here's a real, working example of the string method filters.  We'll have
examples of the path filters in the `Working with Paths`_ section.

    >>> update_file(sample_buildout, 'helloworld.txt.in',
    ... """
    ... HELLO ${world|upper}!
    ... hello ${world|lower}.
    ... ${name|title} and the Chocolate Factory
    ... ${sentence|capitalize}
    ... """)

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... world = Philipp
    ... name = willy wonka
    ... sentence = that is a good book.
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt') # doctest: +ELLIPSIS
    HELLO PHILIPP!
    hello philipp.
    Willy Wonka and the Chocolate Factory
    That is a good book.

Sharing Variables
=================

The recipe allows extending one or more sections, to decrease
repetition, using the ``extends`` option.  For instance, consider the
following buildout.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [template_defaults]
    ... mygreeting = Hi
    ... myaudience = World
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... extends = template_defaults
    ...
    ... myaudience = everybody
    ... """)

The "message" section now has values extended from the "template_defaults"
section, and overwritten locally.  A template of
``${mygreeting}, ${myaudience}!``...

    >>> update_file(sample_buildout, 'helloworld.txt.in',
    ... """
    ... ${mygreeting}, ${myaudience}!
    ... """)

...would thus result in ``Hi, everybody!``.

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt')
    Hi, everybody!

Defining options in Python
==========================

You can specify that certain variables should be interpreted as Python using
``interpreted-options``.  This takes zero or more lines.  Each line should
specify an option.  It can define immediately (see ``silly-range`` in
the example below) or point to an option to be interepreted, which can
be useful if you want to define a multi-line expression (see
``first-interpreted-option`` and ``message-reversed-is-egassem``).

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... interpreted-options = silly-range = repr(range(5))
    ...                       first-interpreted-option
    ...                       message-reversed-is-egassem
    ... first-interpreted-option =
    ...     options['interpreted-options'].splitlines()[0].strip()
    ... message-reversed-is-egassem=
    ...     ''.join(
    ...         reversed(
    ...             buildout['buildout']['parts']))
    ... not-interpreted=hello world
    ... """)

    >>> update_file(sample_buildout, 'helloworld.txt.in', """\
    ... ${not-interpreted}!
    ... silly-range: ${silly-range}
    ... first-interpreted-option: ${first-interpreted-option}
    ... message-reversed-is-egassem: ${message-reversed-is-egassem}
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt') # doctest:+ELLIPSIS
    hello world!
    silly-range: [0, 1, 2, 3, 4]
    first-interpreted-option: silly-range = repr(range(5))
    message-reversed-is-egassem: egassem

Working with Paths
==================

We've already mentioned how to handle buildout's relative-paths option
in the discussion of filters.  This section has some concrete examples
and discussion of that.  It also introduces how to get a set of paths
from specifying dependencies.

Here are concrete examples of the path-repr and shell-path filters.
We'll show results when relative-paths is true and when it is false.

------------------------------
Demonstration of ``path-repr``
------------------------------

Let's say we want to make a custom Python script in the bin directory.
It will print some information from a file in a ``data`` directory
within the buildout root.  Here's the template.

    >>> write(sample_buildout, 'template', 'bin', 'dosomething.py.in', '''\
    ... #!${buildout:executable}
    ... ${python-relative-path-setup}
    ... f = open(${buildout:directory/data/info.csv|path-repr})
    ... print f.read()
    ... ''')
    >>> os.chmod(
    ...     os.path.join(
    ...         sample_buildout, 'template', 'bin', 'dosomething.py.in'),
    ...     0711)

If we evaluate that template with relative-paths set to false, the results
shouldn't be too surprising.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... source-directory = template
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'bin', 'dosomething.py') # doctest: +ELLIPSIS
    #!...
    <BLANKLINE>
    f = open('/.../sample-buildout/data/info.csv')
    print f.read()

``${python-relative-path-setup}`` evaluated to an empty string.  The path
is absolute and quoted.

If we evaluate it with relative-paths set to true, the results are much...
bigger.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ... relative-paths = true
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... source-directory = template
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'bin', 'dosomething.py') # doctest: +ELLIPSIS
    #!...
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
    # Ascend to buildout root.
    _z3c_recipe_filetemplate_base = os.path.dirname(
        _z3c_recipe_filetemplate_base)
    def _z3c_recipe_filetemplate_path_repr(path):
        "Return absolute version of buildout-relative path."
        return os.path.join(_z3c_recipe_filetemplate_base, path)
    <BLANKLINE>
    f = open(_z3c_recipe_filetemplate_path_repr('data/info.csv'))
    print f.read()

That's quite a bit of code.  You might wonder why we don't just use '..' for
parent directories.  The reason is that we want our scripts to be usable
from any place on the filesystem.  If we used '..' to construct paths
relative to the generated file, then the paths would only work from
certain directories.

So that's how path-repr works.  It can really come in handy if you want
to support relative paths in buildout.  Now let's look at the shell-path
filter.

-------------------------------
Demonstration of ``shell-path``
-------------------------------

Maybe you want to write some shell scripts.  The shell-path filter will help
you support buildout relative-paths fairly painlessly.

Right now, only POSIX is supported with the shell-path filter, as mentioned
before.

Usage is very similar to the ``path-repr`` filter.  You need to include
``${shell-relative-path-setup}`` before you use it, just as you include
``${python-relative-path-setup}`` before using ``path-repr``.

Let's say we want to make a custom shell script in the bin directory.
It will print some information from a file in a ``data`` directory
within the buildout root.  Here's the template.

    >>> write(sample_buildout, 'template', 'bin', 'dosomething.sh.in', '''\
    ... #!/bin/sh
    ... ${shell-relative-path-setup}
    ... cat ${buildout:directory/data/info.csv|shell-path}
    ... ''')
    >>> os.chmod(
    ...     os.path.join(
    ...         sample_buildout, 'template', 'bin', 'dosomething.sh.in'),
    ...     0711)

If relative-paths is set to false (the default), the results are simple.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... source-directory = template
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'bin', 'dosomething.sh') # doctest: +ELLIPSIS
    #!/bin/sh
    <BLANKLINE>
    cat /.../sample-buildout/data/info.csv

``${shell-relative-path-setup}`` evaluated to an empty string.  The path
is absolute.

Now let's look at the larger code when relative-paths is set to true.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ... relative-paths = true
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... source-directory = template
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'bin', 'dosomething.sh') # doctest: +ELLIPSIS
    #!/bin/sh
    # Get full, non-symbolic-link path to this file.
    Z3C_RECIPE_FILETEMPLATE_FILENAME=`\
        readlink -f "$0" 2>/dev/null || \
        realpath "$0" 2>/dev/null || \
        type -P "$0" 2>/dev/null`
    # Get directory of file.
    Z3C_RECIPE_FILETEMPLATE_BASE=`dirname ${Z3C_RECIPE_FILETEMPLATE_FILENAME}`
    # Ascend to buildout root.
    Z3C_RECIPE_FILETEMPLATE_BASE=`dirname ${Z3C_RECIPE_FILETEMPLATE_BASE}`
    <BLANKLINE>
    cat "$Z3C_RECIPE_FILETEMPLATE_BASE"/data/info.csv

As with the Python code, we don't just use '..' for
parent directories because we want our scripts to be usable
from any place on the filesystem.

----------------------------------
Getting Arbitrary Dependency Paths
----------------------------------

You can specify ``eggs`` and ``extra-paths`` in the recipe.  The
mechanism is the same as the one provided by the zc.recipe.egg, so
pertinent options such as find-links and index are available.

If you do, the paths for the dependencies will be calculated.  They will
be available as a list in the namespace of the interpreted options as
``paths``.  Also, three predefined options will be available in the
recipe's options for the template.

If ``paths`` are the paths, ``shell_path`` is the ``shell-path`` filter, and
``path_repr`` is the ``path-repr`` filter, then the pre-defined options
would be defined roughly as given here:

``os-paths`` (for shell scripts)
  ``(os.pathsep).join(shell_path(path) for path in paths)``

``string-paths`` (for Python scripts)
  ``',\n    '.join(path_repr(path) for path in paths)``

``space-paths`` (for shell scripts)
  ``' '.join(shell_path(path) for path in paths)``

Therefore, if you want to support the relative-paths option, you should
include ``${shell-relative-path-setup}`` (for ``os-paths`` and
``space-paths``) or ``${python-relative-path-setup}`` (for ``string-paths``)
as appropriate at the top of your template.

Let's consider a simple example.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... eggs = demo<0.3
    ...
    ... find-links = %(server)s
    ... index = %(server)s/index
    ... """ % dict(server=link_server))

The relative-paths option is false, the default.

    >>> write(sample_buildout, 'helloworld.txt.in',
    ... """
    ... Hello!  Here are the paths for the ${eggs} eggs.
    ... OS paths:
    ... ${os-paths}
    ... ---
    ... String paths:
    ... ${string-paths}
    ... ---
    ... Space paths:
    ... ${space-paths}
    ... """)

    >>> print system(buildout)
    Getting distribution for 'demo<0.3'.
    Got demo 0.2.
    Getting distribution for 'demoneeded'.
    Got demoneeded 1.2c1.
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt') # doctest:+ELLIPSIS
    Hello!  Here are the paths for the demo<0.3 eggs.
    OS paths:
    /.../eggs/demo-0.2...egg:/.../eggs/demoneeded-1.2c1...egg
    ---
    String paths:
    '/.../eggs/demo-0.2...egg',
    '/.../eggs/demoneeded-1.2c1...egg'
    ---
    Space paths:
    /.../eggs/demo-0.2...egg /.../eggs/demoneeded-1.2c1...egg

You can specify extra-paths as well, which will go at the end of the egg
paths.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... eggs = demo<0.3
    ... extra-paths = ${buildout:directory}/foo
    ...
    ... find-links = %(server)s
    ... index = %(server)s/index
    ... """ % dict(server=link_server))

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt') # doctest:+ELLIPSIS
    Hello!  Here are the paths for the demo<0.3 eggs.
    OS paths:
    /...demo...:/...demoneeded...:/.../sample-buildout/foo
    ---
    String paths:
    '/...demo...',
    '/...demoneeded...',
    '/.../sample-buildout/foo'
    ---
    Space paths:
    /...demo... /...demoneeded... .../sample-buildout/foo

To emphasize the effect of the relative-paths option, let's see what it looks
like when we set relative-paths to True.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ... relative-paths = true
    ...
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... eggs = demo<0.3
    ... extra-paths = ${buildout:directory}/foo
    ...
    ... find-links = %(server)s
    ... index = %(server)s/index
    ... """ % dict(server=link_server))

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt') # doctest:+ELLIPSIS
    Hello!  Here are the paths for the demo<0.3 eggs.
    OS paths:
    "$Z3C_RECIPE_FILETEMPLATE_BASE"/eggs/demo-0.2-py...egg:"$Z3C_RECIPE_FILETEMPLATE_BASE"/eggs/demoneeded-1.2c1-py...egg:"$Z3C_RECIPE_FILETEMPLATE_BASE"/foo
    ---
    String paths:
    _z3c_recipe_filetemplate_path_repr('eggs/demo-0.2-py...egg'),
    _z3c_recipe_filetemplate_path_repr('eggs/demoneeded-1.2c1-py...egg'),
    _z3c_recipe_filetemplate_path_repr('foo')
    ---
    Space paths:
    "$Z3C_RECIPE_FILETEMPLATE_BASE"/eggs/demo-0.2-py...egg "$Z3C_RECIPE_FILETEMPLATE_BASE"/eggs/demoneeded-1.2c1-py...egg "$Z3C_RECIPE_FILETEMPLATE_BASE"/foo


Remember, your script won't really work unless you include
``${shell-relative-path-setup}`` (for ``os-paths`` and ``space-paths``)
or ``${python-relative-path-setup}`` (for ``string-paths``) as
appropriate at the top of your template.

Getting Dependency Paths from ``zc.recipe.egg``
-----------------------------------------------

You can get the ``eggs`` and ``extra-paths`` from another section using
zc.recipe.egg by using the ``extends`` option from the `Sharing Variables`_
section above.  Then you can use the template options described above to
build your paths in your templates.

Getting Dependency Paths from ``z3c.recipe.scripts``
----------------------------------------------------

If, like the Launchpad project, you are using Gary Poster's unreleased
package ``z3c.recipe.scripts`` to generate your scripts, and you want to
have your scripts use the same Python environment as generated by that
recipe, you can just use the path-repr and shell-path filters with standard
buildout directories.  Here is an example buildout.cfg.

::

    [buildout]
    parts = scripts message
    relative-paths = true

    [scripts]
    recipe = z3c.recipe.scripts
    eggs = demo<0.3

    [message]
    recipe = z3c.recipe.filetemplate
    files = helloworld.py

Then the template to use this would want to simply put
``${scripts:parts-directory|path-repr}`` at the beginning of Python's path.

You can do this for subprocesses with PYTHONPATH.

    ${python-relative-path-setup}
    import os
    import subprocess
    env = os.environ.copy()
    env['PYTHONPATH'] = ${scripts:parts-directory|path-repr}
    subprocess.call('myscript', env=env)

That's it.

Similarly, here's an approach to making a script that will have the
right environment.  You want to put the parts directory of the
z3c.recipe.scripts section in the sys.path before site.py is loaded.
This is usually handled by z3c.recipe.scripts itself, but sometimes you
may want to write Python scripts in your template for some reason.

    #!/usr/bin/env python -S
    ${python-relative-path-setup}
    import sys
    sys.path.insert(0, ${scripts:parts-directory|path-repr})
    import site
    # do stuff...

If you do this for many scripts, put this entire snippet in an option in the
recipe and use this snippet as a single substitution in the top of your
scripts.
