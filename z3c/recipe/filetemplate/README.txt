``z3c.recipe.filetemplate``
***************************

===========
Basic Usage
===========

With the ``z3c.recipe.filetemplate`` buildout recipe you can automate
the generation of text files from templates.  Upon execution, the
recipe will read a number of template files, perform variable
substitution and write the result to the corresponding output files.

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

After executing buildout, we can see that ``$world`` has indeed been
replaced by ``Philipp``:

    >>> print system(buildout)
    Installing message.

    >>> cat(sample_buildout, 'helloworld.txt')
    Hello Philipp!

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

Note that, for the destination, intermediate folders are created if they do not
exist.

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

Substituting from Other Sections
================================

Substitutions can also come from other sections in the buildout, using the
standard buildout syntax.

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

The recipe allows extending one or more sections, to decrease repetition.  For
instance, consider the following buildout.

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

You can specify eggs and extra-paths in the recipe.  If you do, three
predefined options will be available in the recipe's options for the template.
If "paths" are the non-zip paths, and "all_paths" are all paths, then the
options would be defined roughly as given here:

    os-paths: (os.pathsep).join(paths)
    string-paths: ', '.join(repr(p) for p in all_paths)
    space-paths: ' '.join(paths)

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
    .../eggs/demo-0.2...egg:.../eggs/demoneeded-1.2c1...egg
    ---
    String paths:
    '.../eggs/demo-0.2...egg', '.../eggs/demoneeded-1.2c1...egg'
    ---
    Space paths:
    .../eggs/demo-0.2...egg .../eggs/demoneeded-1.2c1...egg

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
    ...demo...:...demoneeded...:.../sample-buildout/foo
    ---
    String paths:
    '...demo...', '...demoneeded...', '.../sample-buildout/foo'
    ---
    Space paths:
    ...demo... ...demoneeded... .../sample-buildout/foo

Defining options in Python
============================

You can specify that certain variables should be interpreted as Python.

XXX

    [buildout]
    parts = message
    
    [message]
    recipe = z3c.recipe.filetemplate
    files = helloworld.txt
    interpreted-options = path-separator=os.pathsep
