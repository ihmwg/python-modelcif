import utils
import os
import unittest

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import ma.alignment


class Tests(unittest.TestCase):
    def test_identity(self):
        """Test sequence identity classes"""
        ident = ma.alignment.ShorterSequenceIdentity(42.0)
        self.assertAlmostEqual(ident.value, 42.0, delta=1e-4)
        ident = ma.alignment.AlignedPositionsIdentity(42.0)


if __name__ == '__main__':
    unittest.main()
