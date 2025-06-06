from datetime import date
import warnings
import utils
import os
import unittest
from io import StringIO
try:
    import msgpack
except ImportError:
    msgpack = None

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.dumper
import modelcif.protocol
import modelcif.model
import modelcif.reference
import modelcif.alignment
import modelcif.associated
import modelcif.descriptor
import ihm.format
import ihm.dumper


def _get_dumper_output(dumper, system, check=True):
    dumper._check = check
    fh = StringIO()
    writer = ihm.format.CifWriter(fh)
    dumper.dump(system, writer)
    return fh.getvalue()


class Tests(unittest.TestCase):
    def test_write(self):
        """Test write() function"""
        sys1 = modelcif.System(id='system1')
        sys2 = modelcif.System(id='system 2+3')
        fh = StringIO()
        modelcif.dumper.write(fh, [sys1, sys2])
        lines = fh.getvalue().split('\n')
        self.assertEqual(lines[:2], ["data_system1", "_entry.id system1"])
        if lines[9] == 'data_system23':
            self.assertEqual(lines[9:11],
                             ["data_system23", "_entry.id 'system 2+3'"])
        else:
            self.assertEqual(lines[11:13],
                             ["data_system23", "_entry.id 'system 2+3'"])

    def test_audit_conform_dumper(self):
        """Test AuditConformDumper"""
        system = modelcif.System()
        dumper = modelcif.dumper._AuditConformDumper()
        out = _get_dumper_output(dumper, system)
        lines = sorted(out.split('\n'))
        self.assertEqual(lines[1].split()[0], "_audit_conform.dict_location")
        self.assertEqual(lines[2].rstrip('\r\n'),
                         "_audit_conform.dict_name mmcif_ma.dic")
        self.assertEqual(lines[3].split()[0], "_audit_conform.dict_version")

    def test_database_dumper(self):
        """Test DatabaseDumper"""
        system = modelcif.System()
        dumper = modelcif.dumper._DatabaseDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, '')

        system = modelcif.System(
            database=modelcif.Database(id='foo', code='bar'))
        dumper = modelcif.dumper._DatabaseDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, "_database_2.database_code bar\n"
                              "_database_2.database_id foo\n")

    def test_software_group_dumper(self):
        """Test SoftwareGroupDumper"""
        class MockObject:
            pass
        p1 = modelcif.SoftwareParameter(name='foo', value=42)
        p2 = modelcif.SoftwareParameter(name='bar', value=True)
        p3 = modelcif.SoftwareParameter(name='baz', value='ok')
        intlist = modelcif.SoftwareParameter(name='intlist', value=[1, 2, 3])
        floatlist = modelcif.SoftwareParameter(
            name='floatlist', value=(1., 2., 3.))
        mixlist = modelcif.SoftwareParameter(name='mixlist', value=[1, 2., 3])
        s1 = modelcif.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s1._id = 1
        s2 = modelcif.Software(
            name='s2', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s2._id = 2
        s3 = modelcif.Software(
            name='s3', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s3._id = 3
        system = modelcif.System()
        aln1 = MockObject()
        aln1.pairs = []
        aln1.software = modelcif.SoftwareGroup((s1, s2))
        # SoftwareGroup.parameters should be ignored
        aln1.software.parameters.append('garbage')
        aln2 = MockObject()
        aln2.pairs = []
        aln2.software = s3
        aln3 = MockObject()
        aln3.pairs = []
        s3param = modelcif.SoftwareWithParameters(
            software=s3, parameters=[p1, p2, p3, intlist, floatlist, mixlist])
        aln3.software = modelcif.SoftwareGroup((s2, s3param))

        # Duplicate parameters, should get the same ID as for aln3
        aln4 = MockObject()
        aln4.pairs = []
        aln4.software = modelcif.SoftwareGroup((s3param,))

        system.alignments.extend((aln1, aln2, aln3, aln4))
        system._before_write()  # populate system.software_groups
        dumper = modelcif.dumper._SoftwareGroupDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        # Should have two groups (s1, s2) and (s2, s3) and another
        # singleton group (s3)
        self.assertEqual(out, """#
loop_
_ma_software_parameter.parameter_id
_ma_software_parameter.group_id
_ma_software_parameter.data_type
_ma_software_parameter.name
_ma_software_parameter.value
_ma_software_parameter.description
1 1 integer foo 42 .
2 1 boolean bar YES .
3 1 string baz ok .
4 1 integer-csv intlist 1,2,3 .
5 1 float-csv floatlist 1.0,2.0,3.0 .
6 1 float-csv mixlist 1,2.0,3 .
#
#
loop_
_ma_software_group.ordinal_id
_ma_software_group.group_id
_ma_software_group.software_id
_ma_software_group.parameter_group_id
1 1 1 .
2 1 2 .
3 2 3 .
4 3 2 .
5 3 3 1
6 4 3 1
#
""")

    def test_bad_software_parameter(self):
        """Test invalid SoftwareParameter"""
        p1 = modelcif.SoftwareParameter(name='foo', value=['string', 'list'])
        s1 = modelcif.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        system = modelcif.System()
        system.software.append(s1)
        s1param = modelcif.SoftwareWithParameters(s1, parameters=[p1])
        sg1 = modelcif.SoftwareGroup([s1param])
        system.software_groups.append(sg1)
        dumper = modelcif.dumper._SoftwareGroupDumper()
        dumper.finalize(system)
        # Only lists of ints or floats are supported, not strings
        self.assertRaises(TypeError, _get_dumper_output, dumper, system)

    def test_data_dumper(self):
        """Test DataDumper"""
        system = modelcif.System()
        entity = modelcif.Entity("DMA", description='test entity')
        system.entities.append(entity)
        # Template and target use same entity here (but different data IDs)
        template = modelcif.Template(
            entity, asym_id="A", model_num=1, name="test template",
            transformation=modelcif.Transformation.identity())
        system.templates.append(template)
        system.data.append(modelcif.data.Data(name="test other",
                                              details="test details"))
        system._before_write()  # populate system.data
        dumper = modelcif.dumper._DataDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_data.id
_ma_data.name
_ma_data.content_type
_ma_data.content_type_other_details
1 'test other' other 'test details'
2 'test template' 'template structure' .
3 'test entity' target .
#
""")

    def test_data_group_dumper(self):
        """Test DataGroupDumper"""
        system = modelcif.System()
        tgt_e1 = modelcif.Entity("D")
        tgt_e2 = modelcif.Entity("M")
        tgt_e3 = modelcif.Entity("A")
        tgt_e1._data_id = 1
        tgt_e2._data_id = 2
        tgt_e3._data_id = 3
        system.entities.extend((tgt_e1, tgt_e2, tgt_e3))
        dg12 = modelcif.data.DataGroup((tgt_e1, tgt_e2))
        p = modelcif.protocol.Protocol()
        p.steps.append(modelcif.protocol.ModelingStep(
            input_data=dg12, output_data=tgt_e3))
        system.protocols.append(p)
        system._before_write()  # populate system.data_groups
        dumper = modelcif.dumper._DataGroupDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        # First group (tgt_e1,tgt_e2); second group contains just tgt_e3
        self.assertEqual(out, """#
loop_
_ma_data_group.ordinal_id
_ma_data_group.group_id
_ma_data_group.data_id
1 1 1
2 1 2
3 2 3
#
""")

    def test_data_ref_db_dumper(self):
        """Test DataRefDBDumper"""
        system = modelcif.System()
        system.data.append(modelcif.ReferenceDatabase(
            name='testdb', url='testurl', version='1.0',
            release_date=date(1979, 11, 22)))
        system.data.append(modelcif.data.Data(name="test other",
                                              details="test details"))
        dumper = modelcif.dumper._DataDumper()
        dumper.finalize(system)  # Assign Data IDs
        dumper = modelcif.dumper._DataRefDBDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_data_ref_db.data_id
_ma_data_ref_db.name
_ma_data_ref_db.location_url
_ma_data_ref_db.version
_ma_data_ref_db.release_date
1 testdb testurl 1.0 1979-11-22
#
""")

    def test_qa_metric_dumper(self):
        """Test QAMetricDumper"""
        system = modelcif.System()
        s1 = modelcif.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s1._group_id = 1

        class MockObject:
            pass

        class CustomMetricType(modelcif.qa_metric.MetricType):
            """my custom type"""

        class DistanceScore(modelcif.qa_metric.Global,
                            modelcif.qa_metric.Distance):
            """test description"""
            name = "test score"
            software = s1

        class CustomScore(modelcif.qa_metric.Global, CustomMetricType):
            """Description does not match docstring"""
            description = "custom description"
            software = None

        class LocalScore(modelcif.qa_metric.Local, modelcif.qa_metric.ZScore):
            """custom local description
               Second line of docstring (ignored)"""
            name = "custom local score"
            software = None

        class PairScore(modelcif.qa_metric.LocalPairwise,
                        modelcif.qa_metric.Energy):
            """custom pair description"""
            name = "custom pair score"
            software = None

        class FeatureScore(modelcif.qa_metric.Feature,
                           modelcif.qa_metric.ZScore):
            """feature score"""
            name = "feature score"
            software = None

        class FeaturePairwiseScore(modelcif.qa_metric.FeaturePairwise,
                                   modelcif.qa_metric.ZScore):
            """feature pairwise score"""
            name = "feature pairwise score"
            software = None

        m1 = DistanceScore(42.)
        m2 = CustomScore(99.)
        m3 = DistanceScore(60.)
        e1 = modelcif.Entity('ACGT')
        asym = modelcif.AsymUnit(e1, 'foo')
        asym._id = 'Z'
        m4 = LocalScore(asym.residue(2), 20.)
        m5 = PairScore(asym.residue(1), asym.residue(3), 30.)
        resf = modelcif.PolyResidueFeature((asym.residue(1), asym.residue(2)))
        instf = modelcif.EntityInstanceFeature((asym,))
        m6 = FeatureScore(resf, 40.)
        m7 = FeaturePairwiseScore(resf, instf, 50.)
        model = MockObject()
        model._id = 18
        model.qa_metrics = [m1, m2, m3, m4, m5, m6, m7]
        mg = modelcif.model.ModelGroup((model,))
        system.model_groups.append(mg)
        # Assign feature IDs
        dumper = modelcif.dumper._FeatureDumper()
        dumper.finalize(system)
        dumper = modelcif.dumper._QAMetricDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_qa_metric.id
_ma_qa_metric.name
_ma_qa_metric.description
_ma_qa_metric.type
_ma_qa_metric.mode
_ma_qa_metric.type_other_details
_ma_qa_metric.software_group_id
1 'test score' 'test description' distance global . 1
2 CustomScore 'custom description' other global 'my custom type' .
3 'custom local score' 'custom local description' zscore local . .
4 'custom pair score' 'custom pair description' energy local-pairwise . .
5 'feature score' 'feature score' zscore per-feature . .
6 'feature pairwise score' 'feature pairwise score' zscore per-feature-pair . .
#
#
loop_
_ma_qa_metric_global.ordinal_id
_ma_qa_metric_global.model_id
_ma_qa_metric_global.metric_id
_ma_qa_metric_global.metric_value
1 18 1 42.000
2 18 2 99.000
3 18 1 60.000
#
#
loop_
_ma_qa_metric_local.ordinal_id
_ma_qa_metric_local.model_id
_ma_qa_metric_local.label_asym_id
_ma_qa_metric_local.label_seq_id
_ma_qa_metric_local.label_comp_id
_ma_qa_metric_local.metric_id
_ma_qa_metric_local.metric_value
1 18 Z 2 CYS 3 20.000
#
#
loop_
_ma_qa_metric_local_pairwise.ordinal_id
_ma_qa_metric_local_pairwise.model_id
_ma_qa_metric_local_pairwise.label_asym_id_1
_ma_qa_metric_local_pairwise.label_seq_id_1
_ma_qa_metric_local_pairwise.label_comp_id_1
_ma_qa_metric_local_pairwise.label_asym_id_2
_ma_qa_metric_local_pairwise.label_seq_id_2
_ma_qa_metric_local_pairwise.label_comp_id_2
_ma_qa_metric_local_pairwise.metric_id
_ma_qa_metric_local_pairwise.metric_value
1 18 Z 1 ALA Z 3 GLY 4 30.000
#
#
loop_
_ma_qa_metric_feature.ordinal_id
_ma_qa_metric_feature.model_id
_ma_qa_metric_feature.feature_id
_ma_qa_metric_feature.metric_id
_ma_qa_metric_feature.metric_value
1 18 1 5 40.000
#
#
loop_
_ma_qa_metric_feature_pairwise.ordinal_id
_ma_qa_metric_feature_pairwise.model_id
_ma_qa_metric_feature_pairwise.feature_id_1
_ma_qa_metric_feature_pairwise.feature_id_2
_ma_qa_metric_feature_pairwise.metric_id
_ma_qa_metric_feature_pairwise.metric_value
1 18 1 2 6 50.000
#
""")

    def test_feature_dumper(self):
        """Test FeatureDumper"""
        system = modelcif.System()

        class MockObject:
            pass

        class TestScore(modelcif.qa_metric.Feature, modelcif.qa_metric.ZScore):
            """test score"""
            name = "test score"
            software = None

        e1 = modelcif.Entity('ACGT')
        asym = modelcif.AsymUnit(e1, 'foo')
        e2 = ihm.Entity([ihm.NonPolymerChemComp('HEM')])
        heme = modelcif.AsymUnit(e2, 'heme')

        asym._id = 'Y'
        heme._id = 'Z'
        atomf = modelcif.AtomFeature((1, 2, 3), details='atom f')
        resf = modelcif.PolyResidueFeature((asym.residue(1), asym.residue(2)),
                                           details='prf')
        instf = modelcif.EntityInstanceFeature((asym,))
        inst2f = modelcif.EntityInstanceFeature((heme,))
        atoms = TestScore(atomf, 20.)
        ress = TestScore(resf, 30.)
        insts = TestScore(instf, 40.)
        inst2s = TestScore(inst2f, 40.)

        model = MockObject()
        model._id = 18
        model.qa_metrics = [atoms, ress, insts, inst2s]
        mg = modelcif.model.ModelGroup((model,))
        system.model_groups.append(mg)

        dumper = modelcif.dumper._FeatureDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_feature_list.feature_id
_ma_feature_list.feature_type
_ma_feature_list.entity_type
_ma_feature_list.details
1 atom other 'atom f'
2 residue polymer prf
3 'entity instance' polymer .
4 'entity instance' non-polymer .
#
#
loop_
_ma_atom_feature.ordinal_id
_ma_atom_feature.feature_id
_ma_atom_feature.atom_id
1 1 1
2 1 2
3 1 3
#
#
loop_
_ma_poly_residue_feature.ordinal_id
_ma_poly_residue_feature.feature_id
_ma_poly_residue_feature.label_asym_id
_ma_poly_residue_feature.label_seq_id
_ma_poly_residue_feature.label_comp_id
1 2 Y 1 ALA
2 2 Y 2 CYS
#
#
loop_
_ma_entity_instance_feature.ordinal_id
_ma_entity_instance_feature.feature_id
_ma_entity_instance_feature.label_asym_id
1 3 Y
2 4 Z
#
""")
        # Test empty feature
        emptyf = modelcif.EntityInstanceFeature(())
        emptys = TestScore(emptyf, 20.)
        model.qa_metrics = [emptys]
        dumper = modelcif.dumper._FeatureDumper()
        dumper.finalize(system)
        self.assertRaises(ValueError, _get_dumper_output, dumper, system)
        # Should work with checks disabled
        _ = _get_dumper_output(dumper, system, check=False)

        # Test feature that selects multiple entity types
        multf = modelcif.EntityInstanceFeature((asym, heme))
        mults = TestScore(multf, 20.)
        model.qa_metrics = [mults]
        dumper = modelcif.dumper._FeatureDumper()
        dumper.finalize(system)
        self.assertRaises(ValueError, _get_dumper_output, dumper, system)
        # Should work with checks disabled
        _ = _get_dumper_output(dumper, system, check=False)

    def test_protocol_dumper(self):
        """Test ProtocolDumper"""
        class MockObject:
            pass
        indat = MockObject()
        indat._data_group_id = 1
        outdat = MockObject()
        outdat._data_group_id = 2
        system = modelcif.System()
        s1 = modelcif.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s1._group_id = 42
        p = modelcif.protocol.Protocol()
        p.steps.append(modelcif.protocol.TemplateSearchStep(
            name='tsstep', details="some details", software=s1,
            input_data=indat, output_data=outdat))
        p.steps.append(modelcif.protocol.ModelingStep(
            name='modstep', input_data=indat, output_data=outdat))
        p.steps.append(modelcif.protocol.ModelingStep(
            name='nullstep', input_data=None, output_data=None))
        system.protocols.append(p)
        dumper = modelcif.dumper._ProtocolDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_protocol_step.ordinal_id
_ma_protocol_step.protocol_id
_ma_protocol_step.step_id
_ma_protocol_step.method_type
_ma_protocol_step.step_name
_ma_protocol_step.details
_ma_protocol_step.software_group_id
_ma_protocol_step.input_data_group_id
_ma_protocol_step.output_data_group_id
1 1 1 'template search' tsstep 'some details' 42 1 2
2 1 2 modeling modstep . . 1 2
3 1 3 modeling nullstep . . . .
#
""")

    def test_model_dumper(self):
        """Test ModelDumper"""
        class CustomModel(modelcif.model.Model):
            """custom model"""

        system = modelcif.System()
        e1 = modelcif.Entity('ACGT')
        e1._id = 9
        system.entities.append(e1)
        asym = modelcif.AsymUnit(e1, 'foo')
        asym._id = 'A'
        system.asym_units.append(asym)
        asmb = modelcif.Assembly((asym,))
        asmb._id = 2
        model1 = modelcif.model.HomologyModel(assembly=asmb, name='test model')
        model1._data_id = 42
        model1._atoms = [modelcif.model.Atom(asym_unit=asym, seq_id=1,
                                             atom_id='C', type_symbol='C',
                                             x=1.0, y=2.0, z=3.0)]
        model2 = modelcif.model.AbInitioModel(assembly=asmb, name='model2')
        model2._data_id = 43
        model3 = CustomModel(assembly=asmb, name='model3')
        model3._data_id = 44
        mg = modelcif.model.ModelGroup((model1, model2, model3),
                                       name='test group')
        system.model_groups.append(mg)
        # model1 is in both groups
        mg = modelcif.model.ModelGroup((model1,),
                                       name='second group')
        # ModelGroup constructor only supports details with python-ihm > 1.8
        mg.details = 'second group details'
        system.model_groups.append(mg)
        dumper = modelcif.dumper._ModelDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_model_list.ordinal_id
_ma_model_list.model_name
_ma_model_list.data_id
_ma_model_list.model_type
_ma_model_list.model_type_other_details
1 'test model' 42 'Homology model' .
2 model2 43 'Ab initio model' .
3 model3 44 Other 'custom model'
#
#
loop_
_ma_model_group.id
_ma_model_group.name
_ma_model_group.details
1 'test group' .
2 'second group' 'second group details'
#
#
loop_
_ma_model_group_link.group_id
_ma_model_group_link.model_id
1 1
1 2
1 3
2 1
#
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_seq_id
_atom_site.auth_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.label_asym_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.label_entity_id
_atom_site.auth_asym_id
_atom_site.auth_comp_id
_atom_site.B_iso_or_equiv
_atom_site.pdbx_PDB_model_num
ATOM 1 C C . ALA 1 1 ? A 1.000 2.000 3.000 . 9 A ALA . 1
#
#
loop_
_atom_type.symbol
C
#
""")

    def test_poly_seq_scheme_dumper(self):
        """Test PolySeqSchemeDumper with ModelCIF models"""
        system = modelcif.System()
        e1 = modelcif.Entity('ACGT')
        e1._id = 9
        system.entities.append(e1)
        asym = modelcif.AsymUnit(e1, 'foo')
        asym._id = 'A'
        system.asym_units.append(asym)
        asmb = modelcif.Assembly((asym,))
        asmb._id = 2
        model1 = modelcif.model.HomologyModel(assembly=asmb, name='test model')
        model1._data_id = 42
        model1._atoms = [modelcif.model.Atom(asym_unit=asym, seq_id=1,
                                             atom_id='C', type_symbol='C',
                                             x=1.0, y=2.0, z=3.0)]
        mg = modelcif.model.ModelGroup((model1,),
                                       name='test group')
        # Add at least one model, since the PolySeqSchemeDumper checks all
        # models' not_modeled_residue_ranges member when writing the table
        system.model_groups.append(mg)
        dumper = ihm.dumper._PolySeqSchemeDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_pdbx_poly_seq_scheme.asym_id
_pdbx_poly_seq_scheme.entity_id
_pdbx_poly_seq_scheme.seq_id
_pdbx_poly_seq_scheme.mon_id
_pdbx_poly_seq_scheme.pdb_seq_num
_pdbx_poly_seq_scheme.auth_seq_num
_pdbx_poly_seq_scheme.pdb_mon_id
_pdbx_poly_seq_scheme.auth_mon_id
_pdbx_poly_seq_scheme.pdb_strand_id
_pdbx_poly_seq_scheme.pdb_ins_code
A 9 1 ALA 1 1 ALA ALA A .
A 9 2 CYS 2 2 CYS CYS A .
A 9 3 GLY 3 3 GLY GLY A .
A 9 4 THR 4 4 THR THR A .
#
""")

    def test_target_ref_db_dumper(self):
        """Test TargetRefDBDumper"""

        class CustomRef(modelcif.reference.TargetReference):
            """my custom ref"""

        system = modelcif.System()
        # Default alignment but with explicit align begin, end
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ref1 = modelcif.reference.UniProt(
                code='testcode', accession='testacc', align_begin=4,
                align_end=8, isoform='testiso', ncbi_taxonomy_id='1234',
                organism_scientific='testorg',
                sequence_version_date=date(1979, 11, 22),
                sequence_crc64="A123B456C789D1E2",
                sequence='ACGT',
                is_primary=True)
        # Default alignment (entire sequence)
        ref2 = modelcif.reference.UniProt(code='c2', accession='a2',
                                          sequence='ACGT')
        ref3 = CustomRef(code='c3', accession='a3', isoform=ihm.unknown,
                         sequence='ACGT')

        # Explicit alignment that extends to the end of the db sequence
        ref4 = modelcif.reference.UniProt(code='c4', accession='a4',
                                          sequence='CCACGT')
        ref4.alignments.append(modelcif.reference.Alignment(db_begin=3))

        # Explicit alignment with explicit db_end
        ref5 = modelcif.reference.UniProt(code='c5', accession='a5',
                                          sequence='XXXACXXGTXXX',
                                          is_primary=False)
        ref5.alignments.append(modelcif.reference.Alignment(
            db_begin=4, db_end=5))
        ref5.alignments.append(modelcif.reference.Alignment(
            db_begin=8, db_end=9))

        e1 = modelcif.Entity('ACGT', references=[ref1, ref2, ref3, ref4, ref5])
        e1._id = 1
        system.entities.append(e1)

        dumper = modelcif.dumper._TargetRefDBDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_target_ref_db_details.target_entity_id
_ma_target_ref_db_details.db_name
_ma_target_ref_db_details.db_name_other_details
_ma_target_ref_db_details.db_code
_ma_target_ref_db_details.db_accession
_ma_target_ref_db_details.seq_db_isoform
_ma_target_ref_db_details.seq_db_align_begin
_ma_target_ref_db_details.seq_db_align_end
_ma_target_ref_db_details.ncbi_taxonomy_id
_ma_target_ref_db_details.organism_scientific
_ma_target_ref_db_details.seq_db_sequence_version_date
_ma_target_ref_db_details.seq_db_sequence_checksum
_ma_target_ref_db_details.is_primary
1 UNP . testcode testacc testiso 4 8 1234 testorg 1979-11-22 A123B456C789D1E2
YES
1 UNP . c2 a2 . 1 4 . . . . .
1 Other 'my custom ref' c3 a3 ? 1 4 . . . . .
1 UNP . c4 a4 . 3 6 . . . . .
1 UNP . c5 a5 . 4 9 . . . . NO
#
""")

    def test_alignment_dumper(self):
        """Test AlignmentDumper"""

        class CustomRef(modelcif.reference.TemplateReference):
            """my custom ref"""

        class Alignment(modelcif.alignment.Global,
                        modelcif.alignment.Pairwise):
            pass

        class LocalAlignment(modelcif.alignment.Local,
                             modelcif.alignment.Multiple):
            pass

        system = modelcif.System()
        tmp_e = modelcif.Entity('ACG')
        tgt_e = modelcif.Entity('ACE')
        tgt_e._id = 1
        system.entities.extend((tmp_e, tgt_e))
        asym = modelcif.AsymUnit(tgt_e, id='A')
        asym._id = 'A'
        system.asym_units.append(asym)
        ref1 = modelcif.reference.PDB('1abc',
                                      db_version_date=date(1979, 11, 22))
        ref2 = CustomRef('2xyz')
        ref3 = modelcif.reference.PubChem("1234")
        ref4 = modelcif.reference.AlphaFoldDB("P12345",
                                              db_version_date=date(2022, 6, 1))
        tr = modelcif.Transformation.identity()
        tr._id = 42
        t = modelcif.Template(tmp_e, asym_id='H', model_num=1, name='testtmp',
                              transformation=tr,
                              references=[ref1, ref2, ref3, ref4],
                              strand_id='Z')
        t._data_id = 99
        p = modelcif.alignment.Pair(
            template=t.segment('AC-G', 1, 3),
            target=asym.segment('ACE-', 1, 3),
            score=modelcif.alignment.BLASTEValue("1e-15"),
            identity=modelcif.alignment.ShorterSequenceIdentity(42.))
        aln = Alignment(name='testaln', pairs=[p])
        aln._data_id = 100
        system.alignments.append(aln)
        # The same alignment using HHblits e-value
        p1 = modelcif.alignment.Pair(
            template=p.template,
            target=p.target,
            score=modelcif.alignment.HHblitsEValue("1e-14"),
            identity=p.identity)
        # The same alignment with missing score and identity
        p2 = modelcif.alignment.Pair(
            template=p.template,
            target=p.target)
        aln = Alignment(name='testaln', pairs=[p1, p2])
        aln._data_id = 101
        system.alignments.append(aln)
        # Local alignment with no pairs
        aln2 = LocalAlignment(name='testaln2', pairs=[])
        aln2._data_id = 102
        system.alignments.append(aln2)
        system._before_write()  # populate system.templates

        dumper = modelcif.dumper._AlignmentDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_template_details.ordinal_id
_ma_template_details.template_id
_ma_template_details.template_origin
_ma_template_details.template_entity_type
_ma_template_details.template_trans_matrix_id
_ma_template_details.template_data_id
_ma_template_details.target_asym_id
_ma_template_details.template_label_asym_id
_ma_template_details.template_label_entity_id
_ma_template_details.template_model_num
_ma_template_details.template_auth_asym_id
1 1 'reference database' polymer 42 99 A H . 1 Z
2 1 'reference database' polymer 42 99 A H . 1 Z
3 1 'reference database' polymer 42 99 A H . 1 Z
#
#
loop_
_ma_template_poly.template_id
_ma_template_poly.seq_one_letter_code
_ma_template_poly.seq_one_letter_code_can
1 ACG ACG
#
#
loop_
_ma_template_poly_segment.id
_ma_template_poly_segment.template_id
_ma_template_poly_segment.residue_number_begin
_ma_template_poly_segment.residue_number_end
1 1 1 3
#
#
loop_
_ma_template_ref_db_details.template_id
_ma_template_ref_db_details.db_name
_ma_template_ref_db_details.db_name_other_details
_ma_template_ref_db_details.db_accession_code
_ma_template_ref_db_details.db_version_date
1 PDB . 1abc 1979-11-22
1 Other 'my custom ref' 2xyz .
1 PubChem . 1234 .
1 AlphaFoldDB . P12345 2022-06-01
#
#
loop_
_ma_target_template_poly_mapping.id
_ma_target_template_poly_mapping.template_segment_id
_ma_target_template_poly_mapping.target_asym_id
_ma_target_template_poly_mapping.target_seq_id_begin
_ma_target_template_poly_mapping.target_seq_id_end
1 1 A 1 3
2 1 A 1 3
3 1 A 1 3
#
#
loop_
_ma_alignment_info.alignment_id
_ma_alignment_info.data_id
_ma_alignment_info.software_group_id
_ma_alignment_info.alignment_length
_ma_alignment_info.alignment_type
_ma_alignment_info.alignment_mode
1 100 . 4 'target-template pairwise alignment' global
2 101 . 4 'target-template pairwise alignment' global
3 102 . . 'target-template MSA' local
#
#
loop_
_ma_alignment_details.ordinal_id
_ma_alignment_details.alignment_id
_ma_alignment_details.template_segment_id
_ma_alignment_details.target_asym_id
_ma_alignment_details.score_type
_ma_alignment_details.score_type_other_details
_ma_alignment_details.score_value
_ma_alignment_details.percent_sequence_identity
_ma_alignment_details.sequence_identity_denominator
_ma_alignment_details.sequence_identity_denominator_other_details
1 1 1 A 'BLAST e-value' . 1e-15 42.000 'Length of the shorter sequence' .
2 2 1 A 'HHblits e-value' . 1e-14 42.000 'Length of the shorter sequence' .
3 2 1 A . . . . . .
#
#
loop_
_ma_alignment.ordinal_id
_ma_alignment.alignment_id
_ma_alignment.target_template_flag
_ma_alignment.sequence
1 1 1 ACE-
2 1 2 AC-G
3 2 1 ACE-
4 2 2 AC-G
5 2 1 ACE-
6 2 2 AC-G
#
""")

    def test_non_poly_template_unused(self):
        """Test AlignmentDumper with unused nonpolymeric template"""
        system = modelcif.System()
        # Polymeric entity
        e1 = ihm.Entity('ACGT')
        t1 = modelcif.Template(
            e1, asym_id="A", model_num=1, name="test template",
            transformation=modelcif.Transformation.identity(),
            entity_id=9)
        t1._id = 1
        t1._data_id = 99
        # Non-polymeric entity
        e2 = ihm.Entity([ihm.NonPolymerChemComp('HEM')], description='heme')
        t2 = modelcif.Template(
            e2, asym_id="B", model_num=1, name="test template",
            transformation=modelcif.Transformation.identity(),
            entity_id=10)
        t2._id = 2
        t2._data_id = 100
        system.templates.extend((t1, t2))
        dumper = modelcif.dumper._AlignmentDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_template_details.ordinal_id
_ma_template_details.template_id
_ma_template_details.template_origin
_ma_template_details.template_entity_type
_ma_template_details.template_trans_matrix_id
_ma_template_details.template_data_id
_ma_template_details.target_asym_id
_ma_template_details.template_label_asym_id
_ma_template_details.template_label_entity_id
_ma_template_details.template_model_num
_ma_template_details.template_auth_asym_id
1 1 'reference database' polymer 42 99 . A 9 1 A
2 2 'reference database' non-polymer 42 100 . B 10 1 B
#
#
loop_
_ma_template_poly.template_id
_ma_template_poly.seq_one_letter_code
_ma_template_poly.seq_one_letter_code_can
1 ACGT ACGT
#
#
loop_
_ma_template_non_poly.template_id
_ma_template_non_poly.comp_id
_ma_template_non_poly.details
2 HEM heme
#
""")

    def test_non_poly_template_used(self):
        """Test AlignmentDumper with used nonpolymeric template"""
        system = modelcif.System()
        # Polymeric entity
        e1 = ihm.Entity('ACGT')
        t1 = modelcif.Template(
            e1, asym_id="A", model_num=1, name="test template",
            transformation=modelcif.Transformation.identity())
        t1._id = 1
        t1._data_id = 98
        # Non-polymeric entity
        e2 = ihm.Entity([ihm.NonPolymerChemComp('HEM')], description='heme')
        # Template should use entity_id, not e2._id
        e2._id = "THIS SHOULD BE IGNORED"
        t2 = modelcif.Template(
            e2, asym_id="B", model_num=1, name="test template",
            transformation=modelcif.Transformation.identity(),
            entity_id=9)
        t2._id = 2
        t2._data_id = 99
        system.templates.extend((t1, t2))

        a2 = modelcif.NonPolymerFromTemplate(template=t2, explicit=True)
        a2._id = 'X'
        system.asym_units.append(a2)

        dumper = modelcif.dumper._AlignmentDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_template_details.ordinal_id
_ma_template_details.template_id
_ma_template_details.template_origin
_ma_template_details.template_entity_type
_ma_template_details.template_trans_matrix_id
_ma_template_details.template_data_id
_ma_template_details.target_asym_id
_ma_template_details.template_label_asym_id
_ma_template_details.template_label_entity_id
_ma_template_details.template_model_num
_ma_template_details.template_auth_asym_id
1 2 'reference database' non-polymer 42 99 X B 9 1 B
2 1 'reference database' polymer 42 98 . A . 1 A
#
#
loop_
_ma_template_poly.template_id
_ma_template_poly.seq_one_letter_code
_ma_template_poly.seq_one_letter_code_can
1 ACGT ACGT
#
#
loop_
_ma_template_non_poly.template_id
_ma_template_non_poly.comp_id
_ma_template_non_poly.details
2 HEM heme
#
""")

    def test_custom_template_unused(self):
        """Test AlignmentDumper with custom template"""
        system = modelcif.System()
        e1 = ihm.Entity('ACGT')
        t1 = modelcif.CustomTemplate(
            e1, asym_id="A", model_num=1, name="test template",
            transformation=modelcif.Transformation.identity(),
            entity_id=9, details='my custom template')
        t1.atoms.append(modelcif.TemplateAtom(
            seq_id=1, atom_id='CA',
            type_symbol='C', x=0.0, y=1.0, z=2.0, occupancy=0.5,
            biso=2.0, charge=1.0, auth_seq_id=42, auth_comp_id='XXX',
            auth_atom_id='X'))
        t1.atoms.append(modelcif.TemplateAtom(
            seq_id=2, atom_id='OXT',
            type_symbol='O', x=1.0, y=2.0, z=3.0))
        t1._id = 1
        t1._data_id = 99
        system.templates.append(t1)
        dumper = modelcif.dumper._AlignmentDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_template_details.ordinal_id
_ma_template_details.template_id
_ma_template_details.template_origin
_ma_template_details.template_entity_type
_ma_template_details.template_trans_matrix_id
_ma_template_details.template_data_id
_ma_template_details.target_asym_id
_ma_template_details.template_label_asym_id
_ma_template_details.template_label_entity_id
_ma_template_details.template_model_num
_ma_template_details.template_auth_asym_id
1 1 customized polymer 42 99 . A 9 1 A
#
#
loop_
_ma_template_poly.template_id
_ma_template_poly.seq_one_letter_code
_ma_template_poly.seq_one_letter_code_can
1 ACGT ACGT
#
#
loop_
_ma_template_customized.template_id
_ma_template_customized.details
1 'my custom template'
#
#
loop_
_ma_template_coord.template_id
_ma_template_coord.group_PDB
_ma_template_coord.ordinal_id
_ma_template_coord.type_symbol
_ma_template_coord.label_atom_id
_ma_template_coord.label_comp_id
_ma_template_coord.label_seq_id
_ma_template_coord.label_asym_id
_ma_template_coord.auth_seq_id
_ma_template_coord.auth_asym_id
_ma_template_coord.auth_atom_id
_ma_template_coord.auth_comp_id
_ma_template_coord.Cartn_x
_ma_template_coord.Cartn_y
_ma_template_coord.Cartn_z
_ma_template_coord.occupancy
_ma_template_coord.label_entity_id
_ma_template_coord.B_iso_or_equiv
_ma_template_coord.formal_charge
1 ATOM 1 C CA ALA 1 A 42 A X XXX 0 1.000 2.000 0.500 9 2.000 1.000
1 ATOM 2 O OXT CYS 2 A . A . . 1.000 2.000 3.000 . 9 . .
#
""")

    def test_template_transform_dumper(self):
        """Test TemplateTransformDumper"""
        system = modelcif.System()
        tr1 = modelcif.Transformation(
            rot_matrix=[[-0.64, 0.09, 0.77], [0.76, -0.12, 0.64],
                        [0.15, 0.99, 0.01]],
            tr_vector=[1., 2., 3.])
        system.template_transformations.append(tr1)
        dumper = modelcif.dumper._TemplateTransformDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_template_trans_matrix.id
_ma_template_trans_matrix.rot_matrix[1][1]
_ma_template_trans_matrix.rot_matrix[2][1]
_ma_template_trans_matrix.rot_matrix[3][1]
_ma_template_trans_matrix.rot_matrix[1][2]
_ma_template_trans_matrix.rot_matrix[2][2]
_ma_template_trans_matrix.rot_matrix[3][2]
_ma_template_trans_matrix.rot_matrix[1][3]
_ma_template_trans_matrix.rot_matrix[2][3]
_ma_template_trans_matrix.rot_matrix[3][3]
_ma_template_trans_matrix.tr_vector[1]
_ma_template_trans_matrix.tr_vector[2]
_ma_template_trans_matrix.tr_vector[3]
1 -0.640000 0.760000 0.150000 0.090000 -0.120000 0.990000 0.770000 0.640000
0.010000 1.000 2.000 3.000
#
""")

    def test_target_entity_dumper(self):
        """Test TargetEntityDumper"""
        system = modelcif.System()
        e1 = modelcif.Entity("D")
        e1._id = 42
        e1._data_id = 99
        system.entities.append(e1)

        a1 = modelcif.AsymUnit(e1, 'foo')
        a1._id = 'X'
        system.asym_units.append(a1)

        dumper = modelcif.dumper._TargetEntityDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_target_entity.entity_id
_ma_target_entity.data_id
_ma_target_entity.origin
42 99 designed
#
#
loop_
_ma_target_entity_instance.asym_id
_ma_target_entity_instance.entity_id
_ma_target_entity_instance.details
X 42 foo
#
""")

    def test_associated_dumper(self):
        """Test AssociatedDumper"""
        system = modelcif.System()
        e = modelcif.Entity('M')
        # File in a repository
        f1 = modelcif.associated.File(path='foo.txt', details='test file')
        # File in an archive
        f2 = modelcif.associated.File(path='bar.txt', details='test file2')
        zf = modelcif.associated.ZipFile(path='t.zip', files=[f2])
        # Local file with data
        f3 = modelcif.associated.File(path='baz.txt', details='test file3',
                                      data=e)
        f4 = modelcif.associated.QAMetricsFile(path='baz.txt',
                                               details='test file4')
        r = modelcif.associated.Repository(url_root='https://example.com',
                                           files=[f1, zf])
        r2 = modelcif.associated.Repository(url_root=None, files=[f3, f4])
        system.repositories.extend((r, r2))

        system._before_write()  # populate data
        dumper = modelcif.dumper._DataDumper()
        dumper.finalize(system)  # Assign Data IDs

        dumper = modelcif.dumper._AssociatedDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_entry_associated_files.id
_ma_entry_associated_files.entry_id
_ma_entry_associated_files.file_url
_ma_entry_associated_files.file_type
_ma_entry_associated_files.file_format
_ma_entry_associated_files.file_content
_ma_entry_associated_files.details
_ma_entry_associated_files.data_id
1 model https://example.com/foo.txt file other other 'test file' .
2 model https://example.com/t.zip archive zip 'archive with multiple files' . .
3 model baz.txt file other other 'test file3' 1
4 model baz.txt file cif 'QA metrics' 'test file4' .
#
#
loop_
_ma_associated_archive_file_details.id
_ma_associated_archive_file_details.archive_file_id
_ma_associated_archive_file_details.file_path
_ma_associated_archive_file_details.file_format
_ma_associated_archive_file_details.file_content
_ma_associated_archive_file_details.description
_ma_associated_archive_file_details.data_id
1 2 bar.txt other other 'test file2' .
#
""")

        # Should be an error to put a zip file inside another zip
        zf2 = modelcif.associated.ZipFile(path='test2.zip', files=[])
        zf.files.append(zf2)
        self.assertRaises(ValueError, dumper.finalize, system)

    def test_write_associated(self):
        """Test write() function with associated files"""
        s = modelcif.System(id='system1')

        f = modelcif.associated.CIFFile(
            path='test_write_associated.cif',
            categories=['struct', '_AUDIT_CONFORM'],
            entry_details='test details', entry_id='testcif')
        f2 = modelcif.associated.File(path='foo.txt', details='test file')
        r = modelcif.associated.Repository(url_root='https://example.com',
                                           files=[f, f2])
        s.repositories.append(r)

        fh = StringIO()
        modelcif.dumper.write(fh, [s])
        main_file = fh.getvalue()
        with open('test_write_associated.cif') as fh:
            assoc_file = fh.read()
        os.unlink('test_write_associated.cif')
        # struct and audit_conform categories should be in associated file,
        # not the main file
        self.assertIn('_struct.title', assoc_file)
        self.assertNotIn('_struct.title', main_file)
        self.assertIn('_audit_conform.dict_name', assoc_file)
        self.assertNotIn('_audit_conform.dict_name', main_file)

    def test_write_associated_in_zip(self):
        """Test write() function with associated files in a ZipFile"""
        s = modelcif.System(id='system1')

        f = modelcif.associated.CIFFile(
            path='test_write_associated_in_zip.cif',
            categories=['struct', '_AUDIT_CONFORM'],
            entry_details='test details', entry_id='testcif')
        zf = modelcif.associated.ZipFile(path='t.zip', files=[f])
        r = modelcif.associated.Repository(url_root='https://example.com',
                                           files=[zf])
        s.repositories.append(r)

        fh = StringIO()
        modelcif.dumper.write(fh, [s])
        main_file = fh.getvalue()
        with open('test_write_associated_in_zip.cif') as fh:
            assoc_file = fh.read()
        os.unlink('test_write_associated_in_zip.cif')
        # struct and audit_conform categories should be in associated file,
        # not the main file
        self.assertIn('_struct.title', assoc_file)
        self.assertNotIn('_struct.title', main_file)
        self.assertIn('_audit_conform.dict_name', assoc_file)
        self.assertNotIn('_audit_conform.dict_name', main_file)

    def test_write_associated_copy(self):
        """Test write() function with associated files, copy_categories"""
        s = modelcif.System(id='system1')

        e1 = modelcif.Entity('ACGT')
        e1._id = 42
        s.entities.append(e1)

        f = modelcif.associated.CIFFile(
            path='/not/exist/foo.cif',
            local_path='test_write_associated_copy.cif',
            categories=['struct'], copy_categories=['entity', 'audit_conform'],
            entry_details='test details', entry_id='testcif')
        r = modelcif.associated.Repository(url_root='https://example.com',
                                           files=[f])
        s.repositories.append(r)

        fh = StringIO()
        modelcif.dumper.write(fh, [s])
        main_file = fh.getvalue()
        with open('test_write_associated_copy.cif') as fh:
            assoc_file = fh.read()
        os.unlink('test_write_associated_copy.cif')
        # struct category should be in associated file, not the main file
        self.assertIn('_struct.title', assoc_file)
        self.assertNotIn('_struct.title', main_file)
        # entity and audit conform categories should be in *both* files
        self.assertIn('_entity.type', assoc_file)
        self.assertIn('_entity.type', main_file)
        self.assertIn('_audit_conform.dict_name', assoc_file)
        self.assertIn('_audit_conform.dict_name', main_file)

    def test_write_associated_none(self):
        """Test write() function with associated files, no categories"""
        s = modelcif.System(id='system1')

        f = modelcif.associated.CIFFile(
            path='test_write_associated_none.cif')
        r = modelcif.associated.Repository(url_root='https://example.com',
                                           files=[f])
        s.repositories.append(r)

        fh = StringIO()
        modelcif.dumper.write(fh, [s])
        main_file = fh.getvalue()
        self.assertIn('_struct.title', main_file)
        self.assertIn('_audit_conform.dict_name', main_file)

    @unittest.skipIf(msgpack is None, "needs Python 3 and msgpack")
    def test_write_associated_binary(self):
        """Test write() function with associated binary files"""
        s = modelcif.System(id='system1')

        f = modelcif.associated.CIFFile(
            path='test_write_associated_binary.bcif',
            categories=['struct', '_AUDIT_CONFORM'],
            entry_details='test details', entry_id='testcif', binary=True)
        r = modelcif.associated.Repository(url_root='https://example.com',
                                           files=[f])
        s.repositories.append(r)

        fh = StringIO()
        modelcif.dumper.write(fh, [s])
        main_file = fh.getvalue()
        with open('test_write_associated_binary.bcif', 'rb') as fh:
            assoc_file = msgpack.unpack(fh, raw=False)
        os.unlink('test_write_associated_binary.bcif')
        assoc_cats = frozenset(
            x['name'] for x in assoc_file['dataBlocks'][0]['categories'])

        self.assertIn('_struct', assoc_cats)
        self.assertNotIn('_struct.title', main_file)
        self.assertIn('_audit_conform', assoc_cats)
        self.assertNotIn('_audit_conform.dict_name', main_file)

    def test_system_writer(self):
        """Test _SystemWriter utility class"""
        class BaseWriter:
            def flush(self):
                return 'flush called'

            def write_comment(self, comment):
                return 'write comment ' + comment

        s = modelcif.dumper._SystemWriter(BaseWriter(), {}, {})
        # These methods are not usually called in ordinary operation, but
        # we should provide them for Writer compatibility
        self.assertEqual(s.flush(), 'flush called')
        self.assertEqual(s.write_comment('foo'), 'write comment foo')

    def test_entity_non_poly_dumper(self):
        """Test EntityNonPolyDumper"""
        system = modelcif.System()
        # Polymeric entity (ignored)
        e1 = modelcif.Entity('ACGT')
        e1._id = 1
        e2 = ihm.Entity([ihm.NonPolymerChemComp('HEM')], description='heme')
        e2._id = 2
        e3 = ihm.Entity([ihm.NonPolymerChemComp('ZN')], description='zinc')
        e3._id = 3
        system.entities.extend((e1, e2, e3))

        t2 = modelcif.Template(e2, 'A', model_num=1, transformation=None)
        a1 = modelcif.AsymUnit(e1, 'foo')
        a2 = modelcif.NonPolymerFromTemplate(template=t2, explicit=True)
        system.asym_units.extend((a1, a2))

        dumper = modelcif.dumper._EntityNonPolyDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_pdbx_entity_nonpoly.entity_id
_pdbx_entity_nonpoly.name
_pdbx_entity_nonpoly.comp_id
_pdbx_entity_nonpoly.ma_model_mode
2 heme HEM explicit
3 zinc ZN .
#
""")

    def test_chem_comp_dumper(self):
        """Test ChemCompDumper"""
        system = modelcif.System()

        # ChemComp without ccd
        c1 = ihm.NonPolymerChemComp('C1', name='C1')

        # ChemComp using core CCD
        c2 = ihm.NonPolymerChemComp('C2', name='C2')
        c2.ccd = 'core'

        # ChemComp using MA CCD
        c3 = ihm.NonPolymerChemComp('C3', name='C3')
        c3.ccd = 'ma'

        # ChemComp with descriptors (local)
        c4 = ihm.NonPolymerChemComp('C4', name='C4')
        c4.ccd = None
        c4.descriptors = [modelcif.descriptor.IUPACName("foo")]

        e1 = modelcif.Entity(['A', 'C', c1, c2, c3, c4])
        system.entities.append(e1)

        e2 = modelcif.Entity('GT')
        t2 = modelcif.Template(e2, 'A', model_num=1, transformation=None)
        system.templates.append(t2)

        dumper = modelcif.dumper._ChemCompDumper()
        out = _get_dumper_output(dumper, system)
        # chem_comp should include both system.entities and system.templates
        self.assertEqual(out, """#
loop_
_chem_comp.id
_chem_comp.type
_chem_comp.name
_chem_comp.formula
_chem_comp.formula_weight
_chem_comp.ma_provenance
ALA 'L-peptide linking' ALANINE 'C3 H7 N O2' 89.094 'CCD Core'
C1 non-polymer C1 . . 'CCD Core'
C2 non-polymer C2 . . 'CCD Core'
C3 non-polymer C3 . . 'CCD MA'
C4 non-polymer C4 . . 'CCD local'
CYS 'L-peptide linking' CYSTEINE 'C3 H7 N O2 S' 121.154 'CCD Core'
GLY 'peptide linking' GLYCINE 'C2 H5 N O2' 75.067 'CCD Core'
THR 'L-peptide linking' THREONINE 'C4 H9 N O3' 119.120 'CCD Core'
#
""")

    def test_chem_comp_dumper_bad_ccd(self):
        """Test ChemCompDumper with invalid value for ccd"""
        system = modelcif.System()

        c1 = ihm.NonPolymerChemComp('C1', name='C1')
        c1.ccd = 'garbage'

        e1 = modelcif.Entity([c1])
        system.entities.append(e1)

        dumper = modelcif.dumper._ChemCompDumper()
        self.assertRaises(KeyError, _get_dumper_output, dumper, system)
        # Should work with checks disabled
        _ = _get_dumper_output(dumper, system, check=False)

    def test_chem_comp_descriptor_dumper(self):
        """Test ChemCompDescriptorDumper"""
        class MockObject:
            pass

        system = modelcif.System()

        # Old-style ChemComp without descriptors
        c1 = ihm.NonPolymerChemComp('C1', name='C1name')
        if hasattr(c1, 'descriptor'):
            del c1.descriptors

        c2 = ihm.NonPolymerChemComp('C2', name='C2name')
        c2.ccd = None
        soft = MockObject()
        soft._id = 42
        c2.descriptors = [modelcif.descriptor.IUPACName("foo"),
                          modelcif.descriptor.PubChemCID(
                              "bar", details="test details", software=soft)]

        e1 = modelcif.Entity(['A', 'C', c1, c2])
        system.entities.append(e1)

        dumper = modelcif.dumper._ChemCompDescriptorDumper()
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_chem_comp_descriptor.ordinal_id
_ma_chem_comp_descriptor.chem_comp_id
_ma_chem_comp_descriptor.chem_comp_name
_ma_chem_comp_descriptor.type
_ma_chem_comp_descriptor.value
_ma_chem_comp_descriptor.details
_ma_chem_comp_descriptor.software_id
1 C2 C2name 'IUPAC Name' foo . .
2 C2 C2name 'PubChem CID' bar 'test details' 42
#
""")

    def test_struct_ref(self):
        """Test StructRefDumper"""
        system = ihm.System()
        lpep = ihm.LPeptideAlphabet()
        sd = modelcif.reference.SeqDif(
            seq_id=2, db_monomer=lpep['W'],
            monomer=lpep['S'], details='Test mutation')
        # Test non-mandatory db_monomer
        sd2 = modelcif.reference.SeqDif(
            seq_id=3, db_monomer=None,
            monomer=lpep['P'], details='Test mutation')
        r1 = modelcif.reference.UniProt(
            code='NUP84_YEAST', accession='P52891', sequence='MELWPTYQT',
            details='test sequence')
        r1.alignments.append(modelcif.reference.Alignment(
            db_begin=3, seq_dif=[sd, sd2]))
        r2 = modelcif.reference.UniProt(
            code='testcode', accession='testacc', sequence='MELSPTYQT',
            details='test2')
        r2.alignments.append(modelcif.reference.Alignment(
            db_begin=4, db_end=5, entity_begin=2, entity_end=3))
        r2.alignments.append(modelcif.reference.Alignment(
            db_begin=9, db_end=9, entity_begin=4, entity_end=4))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r3 = modelcif.reference.UniProt(
                code='testcode2', accession='testacc2', sequence=None)
        r3.alignments.append(modelcif.reference.Alignment(
            db_begin=4, db_end=5, entity_begin=2, entity_end=3))
        r4 = modelcif.reference.UniProt(
            code='testcode3', accession='testacc3', sequence=ihm.unknown)
        r4.alignments.append(modelcif.reference.Alignment(
            db_begin=4, db_end=5, entity_begin=2, entity_end=3))
        system.entities.append(modelcif.Entity(
            'LSPT', references=[r1, r2, r3, r4]))
        dumper = ihm.dumper._EntityDumper()
        dumper.finalize(system)  # Assign entity IDs

        dumper = ihm.dumper._StructRefDumper()
        dumper.finalize(system)  # Assign IDs
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_struct_ref.id
_struct_ref.entity_id
_struct_ref.db_name
_struct_ref.db_code
_struct_ref.pdbx_db_accession
_struct_ref.pdbx_align_begin
_struct_ref.pdbx_seq_one_letter_code
_struct_ref.details
1 1 UNP NUP84_YEAST P52891 3 LWPTYQT 'test sequence'
2 1 UNP testcode testacc 4 SPTYQT test2
3 1 UNP testcode2 testacc2 4 . .
4 1 UNP testcode3 testacc3 4 ? .
#
#
loop_
_struct_ref_seq.align_id
_struct_ref_seq.ref_id
_struct_ref_seq.seq_align_beg
_struct_ref_seq.seq_align_end
_struct_ref_seq.db_align_beg
_struct_ref_seq.db_align_end
1 1 1 4 3 6
2 2 2 3 4 5
3 2 4 4 9 9
4 3 2 3 4 5
5 4 2 3 4 5
#
#
loop_
_struct_ref_seq_dif.pdbx_ordinal
_struct_ref_seq_dif.align_id
_struct_ref_seq_dif.seq_num
_struct_ref_seq_dif.db_mon_id
_struct_ref_seq_dif.mon_id
_struct_ref_seq_dif.details
1 1 2 TRP SER 'Test mutation'
2 1 3 ? PRO 'Test mutation'
#
""")


if __name__ == '__main__':
    unittest.main()
