import os
import unittest
import utils

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import ma.qa_metric


class Tests(unittest.TestCase):
    def test_metric_types(self):
        """Test MetricType subclasses"""
        self.assertEqual(ma.qa_metric.Energy.type, "energy")
        self.assertEqual(ma.qa_metric.PAE.type, "PAE")
        self.assertEqual(ma.qa_metric.ContactProbability.type,
                         "contact probability")


if __name__ == '__main__':
    unittest.main()
