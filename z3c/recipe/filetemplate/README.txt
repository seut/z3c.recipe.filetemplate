With the ``z3c.recipe.filetemplate`` buildout recipe you can automate
the generation of text files from templates.  Upon execution, the
recipe will read a number of template files, perform a simple variable
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
  ... parts = file
  ...
  ... [file]
  ... recipe = z3c.recipe.filetemplate
  ... files = helloworld.txt
  ... world = Philipp
  ... """)

After executing buildout, we can see that ``$world`` has indeed been
replaced by ``Philipp``:

  >>> print system(buildout)
  Installing file.

  >>> cat(sample_buildout, 'helloworld.txt')
  Hello Philipp!
