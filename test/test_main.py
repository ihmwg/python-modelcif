import os
import unittest
import utils

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import ma
import ma.model
import ma.protocol


class Tests(unittest.TestCase):
    def test_all_data(self):
        """Test _all_data() method"""
        s = ma.System()
        e1 = ma.Entity("D")
        e2 = ma.Entity("M")
        s.target_entities.extend((e1, e2))

        e3 = ma.Entity("A")
        s.data.extend((e1, e3))

        d = s._all_data()
        # List may contain duplicates
        self.assertEqual(list(d), [e1, e3, e1, e2])

    def test_all_data_groups(self):
        """Test _all_data_groups() method"""
        s = ma.System()
        e1 = ma.Entity("A")
        s.data_groups.append(e1)
        e2 = ma.Entity("C")

        p = ma.protocol.Protocol()
        p.steps.append(ma.protocol.ModelingStep(
            input_data=e1, output_data=e2))
        s.protocols.append(p)

        d = s._all_data_groups()
        self.assertEqual(list(d), [e1, e1, e2])

    def test_all_target_entities(self):
        """Test _all_target_entities() method"""
        s = ma.System()
        e1 = ma.Entity("D")
        e2 = ma.Entity("M")
        s.target_entities.extend((e1, e2))

        template_e = ma.Entity("M")
        s.entities.extend((e1, e2, template_e))

        asym = ma.AsymUnit(e1, 'foo')
        s.asym_units.append(asym)
        s.assemblies.append(ma.Assembly((asym,)))

        te = s._all_target_entities()
        # List may contain duplicates, but no template entities
        self.assertEqual(list(te), [e1, e2, e1])

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

    def test_all_software_groups(self):
        """Test _all_software_groups() method"""
        s = ma.System()
        sg1 = 'sg1'
        sg2 = 'sg2'
        s.software_groups.extend((sg1, sg2))

        p = ma.protocol.Protocol()
        p.steps.append(ma.protocol.ModelingStep(
            input_data=None, output_data=None, software=sg1))
        s.protocols.append(p)

        allsg = s._all_software_groups()
        # List may contain duplicates
        self.assertEqual(list(allsg), [sg1, sg2, sg1])

    def test_all_ref_software(self):
        """Test _all_ref_software() method"""
        s1 = ma.Software(name='foo', version='1.0',
                         classification='1', description='2', location='3')
        s2 = ma.Software(name='foo', version='2.0',
                         classification='4', description='5', location='6')
        s = ma.System()
        s.software_groups.append(ma.SoftwareGroup((s1, s2)))
        s.software_groups.append(s1)

        alls = s._all_ref_software()
        # List may contain duplicates
        self.assertEqual(list(alls), [s1, s2, s1])

    def test_software_parameter(self):
        """Test SoftwareParameter class"""
        p = ma.SoftwareParameter(name='foo', value=42)
        self.assertEqual(p.name, 'foo')
        self.assertEqual(p.value, 42)
        self.assertIsNone(p.description)
        _ = repr(p)


if __name__ == '__main__':
    unittest.main()
