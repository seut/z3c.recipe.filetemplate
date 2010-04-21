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
import time
import zc.buildout.testing
import zc.buildout.tests
from zope.testing import doctest


def update_file(dir, *args):
    """Update a file.

    Make sure that the mtime of the file is updated so that buildout notices
    the changes.  The resolution of mtime is system dependent, so we keep
    trying to write until mtime has actually changed."""
    path = os.path.join(dir, *(args[:-1]))
    original = os.stat(path).st_mtime
    while True:
        f = open(path, 'w')
        f.write(args[-1])
        f.flush()
        if os.stat(path).st_mtime != original:
            break
        time.sleep(0.2)

def setUp(test):
    zc.buildout.tests.easy_install_SetUp(test)
    test.globs['update_file'] = update_file
    zc.buildout.testing.install_develop('z3c.recipe.filetemplate', test)

def test_suite():
    return doctest.DocFileSuite(
        'README.txt', 'tests.txt',
        setUp=setUp,
        tearDown=zc.buildout.testing.buildoutTearDown,
        optionflags=doctest.NORMALIZE_WHITESPACE,
        )
