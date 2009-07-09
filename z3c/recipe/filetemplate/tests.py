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
import zc.buildout.testing
import zc.buildout.tests
from zope.testing import doctest

def write_and_wait(dir, *args):
    path = os.path.join(dir, *(args[:-1]))
    original = os.stat(path).st_mtime
    while os.stat(path).st_mtime == original:
        f = open(path, 'w')
        f.write(args[-1])
        f.flush()
        os.fsync(f.fileno())
        f.close()

def setUp(test):
    zc.buildout.tests.easy_install_SetUp(test)
    test.globs['write_and_wait'] = write_and_wait
    zc.buildout.testing.install_develop('z3c.recipe.filetemplate', test)

def test_suite():
    return doctest.DocFileSuite(
        'README.txt', 'tests.txt',
        setUp=setUp,
        tearDown=zc.buildout.testing.buildoutTearDown,
        optionflags=doctest.NORMALIZE_WHITESPACE,
        )
