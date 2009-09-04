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

==============
Advanced Usage
==============

Substituting from Other Sections
================================

Substitutions can also come from other sections in the buildout, using the
standard buildout syntax, but used in the template.  Notice
``${buildout:parts}`` in the template below.

    >>> write(sample_buildout, 'helloworld.txt.in',
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

Sharing variables
=================

The recipe allows extending one or more sections, to decrease repetition, using
the ``extends`` option.  For instance, consider the following buildout.

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

    >>> write(sample_buildout, 'helloworld.txt.in',
    ... """
    ... ${mygreeting}, ${myaudience}!
    ... """)

...would thus result in ``Hi, everybody!``.

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt')
    Hi, everybody!

Specifying paths
================

You can specify eggs and extra-paths in the recipe.  If you do, several
predefined options will be available in the recipe's options for the
template. These are the combination of two sets.  First, consider
"stdlib_paths" to be the paths for the standard library, "egg_paths" to
be the paths for the paths for standalone eggs, "dir_paths" to be the
paths for directories that might contain .pth files (like site-packages
or directories added with extra-paths), and "all_paths" to be the
combination of all three in the order of egg_paths, dir_paths, and
stdlib_paths.  Then combine those with three variants: "os" paths,
joined by os.pathsep; "string" paths, quoted paths separated by strings,
suitable for Python lists; and "space" paths, joined by a space.  The
results of the combination are defined roughly as given here.

``os-paths``
  ``(os.pathsep).join(all_paths)``
  
``string-paths``
  ``', '.join(repr(p) for p in all_paths)``

``space-paths``
  ``' '.join(all_paths)``

``os-stdlib-paths``
  ``(os.pathsep).join(stdlib_paths)``
  
``string-stdlib-paths``
  ``', '.join(repr(p) for p in stdlib_paths)``

``space-stdlib-paths``
  ``' '.join(stdlib_paths)``

``os-egg-paths``
  ``(os.pathsep).join(egg_paths)``
  
``string-egg-paths``
  ``', '.join(repr(p) for p in egg_paths)``

``space-egg-paths``
  ``' '.join(egg_paths)``

``os-dir-paths``
  ``(os.pathsep).join(dir_paths)``
  
``string-dir-paths``
  ``', '.join(repr(p) for p in dir_paths)``

``space-dir-paths``
  ``' '.join(dir_paths)``

(Note that you can work with the different path lists in different ways
with the interpreted options described in the section below.)  

For instance, consider this example.

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
    ... ---
    ... OS stdlib paths:
    ... ${os-stdlib-paths}
    ... ---
    ... String stdlib paths:
    ... ${string-stdlib-paths}
    ... ---
    ... Space stdlib paths:
    ... ${space-stdlib-paths}
    ... ---
    ... OS egg paths:
    ... ${os-egg-paths}
    ... ---
    ... String egg paths:
    ... ${string-egg-paths}
    ... ---
    ... Space egg paths:
    ... ${space-egg-paths}
    ... ---
    ... OS dir paths:
    ... ${os-dir-paths}
    ... ---
    ... String dir paths:
    ... ${string-dir-paths}
    ... ---
    ... Space dir paths:
    ... ${space-dir-paths}
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
    .../eggs/demo-0.2...egg:.../eggs/demoneeded-1.2c1...egg:...
    ---
    String paths:
    '.../eggs/demo-0.2...egg', '.../eggs/demoneeded-1.2c1...egg', '...'
    ---
    Space paths:
    .../eggs/demo-0.2...egg .../eggs/demoneeded-1.2c1...egg ...

Notice that included multiple paths.  In fact, it includes the site packages
and the standard library, so these are appropriate for entirely replacing
sys.path.

You can eliminate the site packages from the paths by specifying
"include-site-packages = false" in the buildout or the specific section.

You can specify extra-paths as well, which will go at the end of the egg paths.

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
    ...demo...:...demoneeded...:.../sample-buildout/foo:...
    ---
    String paths:
    '...demo...', '...demoneeded...', '.../sample-buildout/foo', '...'
    ---
    Space paths:
    ...demo... ...demoneeded... .../sample-buildout/foo ...
    ---
    OS stdlib paths:
    ...:...
    ---
    String stdlib paths:
    '...', ...
    ---
    Space stdlib paths:
    ... ...
    ---
    OS egg paths:
    ...demo...:...demoneeded...
    ---
    String egg paths:
    '...demo...', '...demoneeded...'
    ---
    Space egg paths:
    ...demo... ...demoneeded...
    ---
    OS dir paths:
    .../sample-buildout/foo:...
    ---
    String dir paths:
    '.../sample-buildout/foo', ...
    ---
    Space dir paths:
     .../sample-buildout/foo ...

Defining options in Python
==========================

You can specify that certain variables should be interpreted as Python using
``interpreted-options``.  This takes zero or more lines.  Each line should
specify an option.  It can define immediately (see ``duplicate-os-paths``,
``foo-paths``, and ``silly-range`` in the example below) or point to an option
to be interepreted, which can be useful if you want to define a
multi-line expression (see ``first-interpreted-option`` and
``message-reversed-is-egassem``).

Useful values available in the evaluation context include the following.

``name``
   Section name.
``options``
  The options for the current section.
``buildout``
  The buildout object.
``stdlib_paths``
  The list of the paths in the standard library.
``egg_paths``
  The list of standalone egg paths.
``dir_paths``
  The list of paths that might contain eggs, other packages or modules, or
  .pth files.
``all_paths``
  A concatenation of all of the previously mentioned paths in the order of
  egg_paths, dir_paths, and stdlib_paths.
``paths``
  A shorthand for ``all_paths``.

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = message
    ... 
    ... [message]
    ... recipe = z3c.recipe.filetemplate
    ... files = helloworld.txt
    ... eggs = demo<0.3
    ... interpreted-options = duplicate-os-paths=(os.pathsep).join(paths)
    ...                       foo-paths='FOO'.join(all_paths)
    ...                       silly-range = repr(range(5))
    ...                       first-interpreted-option
    ...                       message-reversed-is-egassem
    ...                       my-name = name
    ...                       paths-are-equivalent
    ...                       
    ... first-interpreted-option = 
    ...     options['interpreted-options'].split()[0].strip()
    ... message-reversed-is-egassem=
    ...     ''.join(
    ...         reversed(
    ...             buildout['buildout']['parts']))
    ... paths-are-equivalent=
    ...     repr((egg_paths + dir_paths + stdlib_paths) == paths)
    ... not-interpreted=hello world
    ...
    ... find-links = %(server)s
    ... index = %(server)s/index
    ... """ % dict(server=link_server))

    >>> write(sample_buildout, 'helloworld.txt.in',
    ... """
    ... ${not-interpreted}!
    ... duplicate-os-paths: ${duplicate-os-paths}
    ... foo-paths: ${foo-paths}
    ... silly-range: ${silly-range}
    ... first-interpreted-option: ${first-interpreted-option}
    ... message-reversed-is-egassem: ${message-reversed-is-egassem}
    ... my-name: ${my-name}
    ... paths-are-equivalent: ${paths-are-equivalent}
    ... """)

    >>> print system(buildout)
    Uninstalling message.
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt') # doctest:+ELLIPSIS
    hello world!
    duplicate-os-paths: ...demo-0.2...egg:...demoneeded-1.2c1...egg:...
    foo-paths: ...demo-0.2...eggFOO...demoneeded-1.2c1...eggFOO...
    silly-range: [0, 1, 2, 3, 4]
    first-interpreted-option: duplicate-os-paths=(os.pathsep).join(paths)
    message-reversed-is-egassem: egassem
    my-name: message
    paths-are-equivalent: True
