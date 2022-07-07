import os
import unittest
import utils

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif
import modelcif.protocol
import modelcif.descriptor
import ihm


class Tests(unittest.TestCase):
    def test_all_data(self):
        """Test _all_data() method"""
        s = modelcif.System()
        e1 = modelcif.Entity("D")
        e2 = modelcif.Entity("M")
        s.target_entities.extend((e1, e2))

        e3 = modelcif.Entity("A")
        s.data.extend((e1, e3))

        s.data_groups.append('something not a group')
        e4 = modelcif.Entity("M")
        s.data_groups.append(modelcif.data.DataGroup([e1, e4]))

        d = s._all_data()
        # List may contain duplicates
        self.assertEqual(list(d), [e1, e3, e1, e2, e1, e4])

    def test_all_asym_units(self):
        """Test _all_asym_units() method"""
        s = modelcif.System()
        e1 = modelcif.Entity("DDDD")
        e2 = modelcif.Entity("MMMM")
        a1 = modelcif.AsymUnit(e1)
        a2 = modelcif.AsymUnit(e2)
        s.asym_units.append(a1)

        asmb = modelcif.Assembly((a1, a2(1, 2)))
        s.assemblies.append(asmb)

        asyms = s._all_asym_units()
        # List may contain duplicates and should be all AsymUnit,
        # not AsymUnitRange
        self.assertEqual(list(asyms), [a1, a1, a2])

    def test_all_entities(self):
        """Test _all_entities() method"""
        s = modelcif.System()
        e1 = modelcif.Entity("DDDD")
        e2 = modelcif.Entity("MMMM")
        s.entities.append(e1)

        a1 = modelcif.AsymUnit(e1)
        s.asym_units.append(a1)

        t2 = modelcif.Template(e2, asym_id='A', model_num=1,
                               transformation=None)
        s.templates.append(t2)

        es = s._all_entities()
        # List may contain duplicates, but does not contain template entity e2
        self.assertEqual(list(es), [e1, e1])

    def test_all_data_groups(self):
        """Test _all_data_groups() method"""
        s = modelcif.System()
        e1 = modelcif.Entity("A")
        s.data_groups.append(e1)
        e2 = modelcif.Entity("C")

        p = modelcif.protocol.Protocol()
        p.steps.append(modelcif.protocol.ModelingStep(
            input_data=e1, output_data=e2))
        s.protocols.append(p)

        d = s._all_data_groups()
        self.assertEqual(list(d), [e1, e1, e2])

    def test_all_target_entities(self):
        """Test _all_target_entities() method"""
        s = modelcif.System()
        e1 = modelcif.Entity("D")
        e2 = modelcif.Entity("M")
        s.target_entities.extend((e1, e2))

        template_e = modelcif.Entity("M")
        s.entities.extend((e1, e2, template_e))

        asym = modelcif.AsymUnit(e1, 'foo')
        s.asym_units.append(asym)
        s.assemblies.append(modelcif.Assembly((asym,)))

        te = s._all_target_entities()
        # List may contain duplicates, but no template entities
        self.assertEqual(list(te), [e1, e2, e1])

    def test_all_template_transformations(self):
        """Test _all_template_transformations() method"""
        s = modelcif.System()
        tr1 = 'tr1'
        tr2 = 'tr2'
        s.template_transformations.extend((tr1, tr2))

        template = modelcif.Template('mockentity', asym_id="A", model_num=1,
                                     name="test template",
                                     transformation=tr1)
        s.templates.append(template)

        tt = s._all_template_transformations()
        # List may contain duplicates
        self.assertEqual(list(tt), [tr1, tr2, tr1])

    def test_transformation(self):
        """Test Transformation class"""
        _ = modelcif.Transformation([[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                                    [1, 2, 3])

    def test_identity_transformation(self):
        """Test identity transformation"""
        t = modelcif.Transformation.identity()
        for i in range(3):
            self.assertAlmostEqual(t.tr_vector[i], 0., delta=0.1)
            for j in range(3):
                self.assertAlmostEqual(t.rot_matrix[i][j],
                                       1. if i == j else 0., delta=0.1)

        # Should always get the same object
        t2 = modelcif.Transformation.identity()
        self.assertIs(t, t2)

    def test_all_software_groups(self):
        """Test _all_software_groups() method"""
        s = modelcif.System()
        sg1 = 'sg1'
        sg2 = 'sg2'
        s.software_groups.extend((sg1, sg2))

        p = modelcif.protocol.Protocol()
        p.steps.append(modelcif.protocol.ModelingStep(
            input_data=None, output_data=None, software=sg1))
        s.protocols.append(p)

        allsg = s._all_software_groups()
        # List may contain duplicates
        self.assertEqual(list(allsg), [sg1, sg2, sg1])

    def test_all_ref_software(self):
        """Test _all_ref_software() method"""
        s1 = modelcif.Software(
            name='foo', version='1.0',
            classification='1', description='2', location='3')
        s2 = modelcif.Software(
            name='foo', version='2.0',
            classification='4', description='5', location='6')
        s = modelcif.System()
        s.software_groups.append(modelcif.SoftwareGroup((s1, s2)))
        s.software_groups.append(s1)

        e1 = modelcif.Entity("DDDD")
        t1 = modelcif.Template(e1, asym_id='A', model_num=1,
                               transformation=None)
        s.templates.append(t1)

        # Old-style ChemComp without descriptors
        c1 = ihm.NonPolymerChemComp('C1', name='C1')
        if hasattr(c1, 'descriptors'):
            del c1.descriptors

        # ChemComp with descriptor without software
        c2 = ihm.NonPolymerChemComp('C2', name='C2')
        c2.descriptors = [modelcif.descriptor.IUPACName('foo')]

        # ChemComp with descriptor with software
        c3 = ihm.NonPolymerChemComp('C3', name='C3')
        s3 = modelcif.Software(
            name='foo', version='2.0',
            classification='4', description='5', location='6')
        c3.descriptors = [modelcif.descriptor.IUPACName('foo', software=s3)]

        e2 = modelcif.Entity([c1, c2, c3])
        s.entities.append(e2)

        alls = s._all_ref_software()
        # List may contain duplicates
        self.assertEqual(list(alls), [s1, s2, s1, s3])

    def test_software_parameter(self):
        """Test SoftwareParameter class"""
        p = modelcif.SoftwareParameter(name='foo', value=42)
        self.assertEqual(p.name, 'foo')
        self.assertEqual(p.value, 42)
        self.assertIsNone(p.description)
        _ = repr(p)

    def test_template(self):
        """Test Template class"""
        e1 = modelcif.Entity("DDDD")
        t1 = modelcif.Template(e1, asym_id='A', model_num=1,
                               transformation=None)
        self.assertEqual(t1.seq_id_range, (1, 4))
        self.assertEqual(t1.template, t1)


if __name__ == '__main__':
    unittest.main()
