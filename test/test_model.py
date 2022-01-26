import utils
import os
import unittest

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.model


class Tests(unittest.TestCase):
    def test_model(self):
        """Test Model classes"""
        m = modelcif.model.HomologyModel([])
        self.assertEqual(m.model_type, "Homology model")
        self.assertIsNone(m.other_details)

        # generic "other" model
        m = modelcif.model.Model([])
        self.assertEqual(m.model_type, "Other")
        self.assertIsNone(m.other_details)

        # custom "other" model
        class CustomRef(modelcif.model.Model):
            """foo
               bar"""

        m = CustomRef([])
        self.assertEqual(m.model_type, "Other")
        self.assertEqual(m.other_details, "foo")


if __name__ == '__main__':
    unittest.main()
