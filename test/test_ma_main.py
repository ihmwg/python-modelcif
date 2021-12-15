import os
import unittest
import utils

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import ma


class Tests(unittest.TestCase):
    def test_all_template_transformations(self):
        """Test _all_template_transformations() method"""
        s = ma.System()
        tr1 = 'tr1'
        tr2 = 'tr2'
        s.template_transformations.extend((tr1, tr2))

        template = ma.Template('mockentity', asym_id="A", model_num=1,
                               name="test template",
                               transformation=tr1)
        s.templates.append(template)

        tt = s._all_template_transformations()
        # List may contain duplicates
        self.assertEqual(list(tt), [tr1, tr2, tr1])

    def test_transformation(self):
        """Test Transformation class"""
        _ = ma.Transformation([[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                              [1, 2, 3])

    def test_identity_transformation(self):
        """Test identity transformation"""
        t = ma.Transformation.identity()
        for i in range(3):
            self.assertAlmostEqual(t.tr_vector[i], 0., delta=0.1)
            for j in range(3):
                self.assertAlmostEqual(t.rot_matrix[i][j],
                                       1. if i == j else 0., delta=0.1)


if __name__ == '__main__':
    unittest.main()
