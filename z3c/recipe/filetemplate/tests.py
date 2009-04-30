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

import zc.buildout.testing
import zc.buildout.tests
from zope.testing import doctest

def setUp(test):
    zc.buildout.tests.easy_install_SetUp(test)
    zc.buildout.testing.install_develop('z3c.recipe.filetemplate', test)

def test_suite():
    return doctest.DocFileSuite(
        'README.txt', 'tests.txt',
        setUp=setUp,
        tearDown=zc.buildout.testing.buildoutTearDown,
        optionflags=doctest.NORMALIZE_WHITESPACE,
        )
