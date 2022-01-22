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
        self.assertEqual(ident.denominator, "Length of the shorter sequence")
        self.assertIsNone(ident.other_details)
        self.assertAlmostEqual(ident.value, 42.0, delta=1e-4)
        ident = ma.alignment.AlignedPositionsIdentity(42.0)

        # generic "other" identity
        ident = ma.alignment.Identity(42.0)
        self.assertEqual(ident.denominator, "Other")
        self.assertIsNone(ident.other_details)

        # custom "other" identity
        class CustomIdentity(ma.alignment.Identity):
            """foo
               bar"""

        ident = CustomIdentity(42.0)
        self.assertEqual(ident.denominator, "Other")
        self.assertEqual(ident.other_details, "foo")


if __name__ == '__main__':
    unittest.main()
