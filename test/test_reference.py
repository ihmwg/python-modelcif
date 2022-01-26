import utils
import os
import unittest

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.reference


class Tests(unittest.TestCase):
    def test_template_reference(self):
        """Test TemplateReference classes"""
        ref = modelcif.reference.PDB("1abc")
        self.assertEqual(ref.name, "PDB")
        self.assertIsNone(ref.other_details)

        # generic "other" reference
        ref = modelcif.reference.TemplateReference("1abc")
        self.assertEqual(ref.name, "Other")
        self.assertIsNone(ref.other_details)

        # custom "other" reference
        class CustomRef(modelcif.reference.TemplateReference):
            """foo
               bar"""

        ref = CustomRef("1abc")
        self.assertEqual(ref.name, "Other")
        self.assertEqual(ref.other_details, "foo")

    def test_target_reference(self):
        """Test TargetReference classes"""
        ref = modelcif.reference.UniProt("code", "acc")
        self.assertEqual(ref.name, "UNP")
        self.assertIsNone(ref.other_details)

        # generic "other" reference
        ref = modelcif.reference.TargetReference("code", "acc")
        self.assertEqual(ref.name, "Other")
        self.assertIsNone(ref.other_details)

        # custom "other" reference
        class CustomRef(modelcif.reference.TargetReference):
            """foo
               bar"""

        ref = CustomRef("code", "acc")
        self.assertEqual(ref.name, "Other")
        self.assertEqual(ref.other_details, "foo")


if __name__ == '__main__':
    unittest.main()
