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

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name='z3c.recipe.filetemplate',
      version = '2.1.0',
      license='ZPL 2.1',
      url='http://pypi.python.org/pypi/z3c.recipe.filetemplate',
      description="zc.buildout recipe for creating files from file templates",
      author='Philipp von Weitershausen',
      author_email='philipp@weitershausen.de',
      maintainer='Gary Poster',
      maintainer_email='gary.poster@canonical.com',
      long_description=(read('z3c', 'recipe', 'filetemplate', 'README.txt')
                        + '\n\n' +
                        read('CHANGES.txt')),
      classifiers = ['Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: Zope Public License',
                     'Programming Language :: Python',
                     'Operating System :: OS Independent',
                     'Topic :: Software Development :: Build Tools',
                     'Framework :: Buildout',
                     ],

      packages=find_packages(),
      namespace_packages=['z3c', 'z3c.recipe'],
      install_requires=['setuptools',
                        'zc.buildout',
                        'zc.recipe.egg',
                        ],
      zip_safe=True,
      entry_points="""
      [zc.buildout]
      default = z3c.recipe.filetemplate:FileTemplate
      """,
      include_package_data=True,
      )
