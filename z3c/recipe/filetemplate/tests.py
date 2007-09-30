import zc.buildout.testing
from zope.testing import doctest

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('z3c.recipe.filetemplate', test)

def test_suite():
    return doctest.DocFileSuite(
        'README.txt', 'tests.txt',
        setUp=setUp,
        tearDown=zc.buildout.testing.buildoutTearDown,
        optionflags=doctest.NORMALIZE_WHITESPACE,
        )
