import utils
import os
import unittest

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.descriptor


class Tests(unittest.TestCase):
    def test_descriptor(self):
        """Test Descriptor classes"""
        base = modelcif.descriptor.Descriptor("1abc")
        self.assertEqual(base.value, "1abc")
        _ = repr(base)


if __name__ == '__main__':
    unittest.main()
