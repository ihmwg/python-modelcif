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
        self.assertIsNone(ma.qa_metric.Energy.other_details)
        self.assertEqual(ma.qa_metric.PAE.type, "PAE")
        self.assertEqual(ma.qa_metric.ContactProbability.type,
                         "contact probability")

        # MetricType itself should have no other_details
        class Custom1(ma.qa_metric.Global, ma.qa_metric.MetricType):
            """Custom 1"""
        x = Custom1(42)
        self.assertEqual(x.type, "other")
        self.assertIsNone(x.other_details)

        class CustomMetricType(ma.qa_metric.MetricType):
            """foo
               bar"""

        class Custom2(ma.qa_metric.Global, CustomMetricType):
            """Custom 2"""
        x = Custom2(42)
        self.assertEqual(x.type, "other")
        self.assertEqual(x.other_details, "foo")

    def test_global_metric(self):
        """Test Global MetricMode"""
        class MyScore(ma.qa_metric.Global, ma.qa_metric.Energy):
            pass

        q = MyScore(42)
        _ = repr(q)

    def test_local_metric(self):
        """Test Local MetricMode"""
        class MyScore(ma.qa_metric.Local, ma.qa_metric.Energy):
            pass

        e1 = ma.Entity('ACGT')
        asym = ma.AsymUnit(e1, 'foo')
        q = MyScore(asym.residue(2), 42)
        _ = repr(q)

    def test_local_pairwise_metric(self):
        """Test LocalPairwise MetricMode"""
        class MyScore(ma.qa_metric.LocalPairwise, ma.qa_metric.Energy):
            pass

        e1 = ma.Entity('ACGT')
        asym = ma.AsymUnit(e1, 'foo')
        q = MyScore(asym.residue(2), asym.residue(3), 42)
        _ = repr(q)


if __name__ == '__main__':
    unittest.main()
