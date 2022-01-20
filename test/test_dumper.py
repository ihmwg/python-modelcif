import utils
import os
import unittest
import sys
if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from io import BytesIO as StringIO

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import ma.dumper
import ma.protocol
import ma.model
import ma.reference
import ma.alignment
import ihm.format
import ihm.dumper


def _get_dumper_output(dumper, system):
    fh = StringIO()
    writer = ihm.format.CifWriter(fh)
    dumper.dump(system, writer)
    return fh.getvalue()


class Tests(unittest.TestCase):
    def test_write(self):
        """Test write() function"""
        sys1 = ma.System(id='system1')
        sys2 = ma.System(id='system 2+3')
        fh = StringIO()
        ma.dumper.write(fh, [sys1, sys2])
        lines = fh.getvalue().split('\n')
        self.assertEqual(lines[:2], ["data_system1", "_entry.id system1"])
        self.assertEqual(lines[7:9],
                         ["data_system23", "_entry.id 'system 2+3'"])

    def test_audit_conform_dumper(self):
        """Test AuditConformDumper"""
        system = ma.System()
        dumper = ma.dumper._AuditConformDumper()
        out = _get_dumper_output(dumper, system)
        lines = sorted(out.split('\n'))
        self.assertEqual(lines[1].split()[0], "_audit_conform.dict_location")
        self.assertEqual(lines[2].rstrip('\r\n'),
                         "_audit_conform.dict_name mmcif_ma.dic")
        self.assertEqual(lines[3].split()[0], "_audit_conform.dict_version")

    def test_software_group_dumper(self):
        """Test SoftwareGroupDumper"""
        class MockObject(object):
            pass
        s1 = ma.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s1._id = 1
        s2 = ma.Software(
            name='s2', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s2._id = 2
        s3 = ma.Software(
            name='s3', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s3._id = 3
        system = ma.System()
        aln1 = MockObject()
        aln1.pairs = []
        aln1.software = ma.SoftwareGroup((s1, s2))
        aln2 = MockObject()
        aln2.pairs = []
        aln2.software = s3
        system.alignments.extend((aln1, aln2))
        system._before_write()  # populate system.software_groups
        dumper = ma.dumper._SoftwareGroupDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        # Should have one group (s1, s2) and another singleton group (s3)
        self.assertEqual(out, """#
loop_
_ma_software_group.ordinal_id
_ma_software_group.group_id
_ma_software_group.software_id
_ma_software_group.parameter_group_id
1 1 1 .
2 1 2 .
3 2 3 .
#
""")

    def test_data_dumper(self):
        """Test DataDumper"""
        system = ma.System()
        entity = ma.Entity("DMA", description='test entity')
        system.target_entities.append(entity)
        # Template and target use same entity here (but different data IDs)
        template = ma.Template(entity, asym_id="A", model_num=1,
                               name="test template",
                               transformation=ma.Transformation.identity())
        system.templates.append(template)
        system.data.append(ma.data.Data(name="test other",
                                        details="test details"))
        system._before_write()  # populate system.data
        dumper = ma.dumper._DataDumper()
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
        system = ma.System()
        tgt_e1 = ma.Entity("D")
        tgt_e2 = ma.Entity("M")
        tgt_e3 = ma.Entity("A")
        tgt_e1._data_id = 1
        tgt_e2._data_id = 2
        tgt_e3._data_id = 3
        system.target_entities.extend((tgt_e1, tgt_e2, tgt_e3))
        dg12 = ma.data.DataGroup((tgt_e1, tgt_e2))
        p = ma.protocol.Protocol()
        p.steps.append(ma.protocol.ModelingStep(
            input_data=dg12, output_data=tgt_e3))
        system.protocols.append(p)
        system._before_write()  # populate system.data_groups
        dumper = ma.dumper._DataGroupDumper()
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

    def test_qa_metric_dumper(self):
        """Test QAMetricDumper"""
        system = ma.System()
        s1 = ma.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s1._group_id = 1

        class MockObject(object):
            pass

        class CustomMetricType(ma.qa_metric.MetricType):
            other_details = "my custom type"

        class DistanceScore(ma.qa_metric.Global, ma.qa_metric.Distance):
            name = "test score"
            description = "test description"
            software = s1

        class CustomScore(ma.qa_metric.Global, CustomMetricType):
            name = "custom score"
            description = "custom description"
            software = None

        class LocalScore(ma.qa_metric.Local, ma.qa_metric.ZScore):
            name = "custom local score"
            description = "custom local description"
            software = None

        class PairScore(ma.qa_metric.LocalPairwise, ma.qa_metric.ZScore):
            name = "custom pair score"
            description = "custom pair description"
            software = None

        m1 = DistanceScore(42.)
        m2 = CustomScore(99.)
        m3 = DistanceScore(60.)
        e1 = ma.Entity('ACGT')
        asym = ma.AsymUnit(e1, 'foo')
        asym._id = 'Z'
        m4 = LocalScore(asym.residue(2), 20.)
        m5 = PairScore(asym.residue(1), asym.residue(3), 30.)
        model = MockObject()
        model._id = 18
        model.qa_metrics = [m1, m2, m3, m4, m5]
        mg = ma.model.ModelGroup((model,))
        system.model_groups.append(mg)
        dumper = ma.dumper._QAMetricDumper()
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
2 'custom score' 'custom description' other global 'my custom type' .
3 'custom local score' 'custom local description' zscore local . .
4 'custom pair score' 'custom pair description' zscore local-pairwise . .
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
""")

    def test_protocol_dumper(self):
        """Test ProtocolDumper"""
        class MockObject(object):
            pass
        indat = MockObject()
        indat._data_group_id = 1
        outdat = MockObject()
        outdat._data_group_id = 2
        system = ma.System()
        s1 = ma.Software(
            name='s1', classification='test code',
            description='Some test program',
            version=1, location='http://test.org')
        s1._group_id = 42
        p = ma.protocol.Protocol()
        p.steps.append(ma.protocol.TemplateSearchStep(
            name='tsstep', details="some details", software=s1,
            input_data=indat, output_data=outdat))
        p.steps.append(ma.protocol.ModelingStep(
            name='modstep', input_data=indat, output_data=outdat))
        system.protocols.append(p)
        dumper = ma.dumper._ProtocolDumper()
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
#
""")

    def test_model_dumper(self):
        """Test ModelDumper"""
        class CustomModel(ma.model.Model):
            other_details = "custom model"

        system = ma.System()
        e1 = ma.Entity('ACGT')
        e1._id = 9
        system.entities.append(e1)
        asym = ma.AsymUnit(e1, 'foo')
        asym._id = 'A'
        system.asym_units.append(asym)
        asmb = ma.Assembly((asym,))
        asmb._id = 2
        model1 = ma.model.HomologyModel(assembly=asmb, name='test model')
        model1._data_id = 42
        model1._atoms = [ma.model.Atom(asym_unit=asym, seq_id=1, atom_id='C',
                                       type_symbol='C', x=1.0, y=2.0, z=3.0)]
        model2 = ma.model.AbInitioModel(assembly=asmb, name='model2')
        model2._data_id = 43
        model3 = CustomModel(assembly=asmb, name='model3')
        model3._data_id = 44
        mg = ma.model.ModelGroup((model1, model2, model3), name='test group')
        system.model_groups.append(mg)
        dumper = ma.dumper._ModelDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_model_list.ordinal_id
_ma_model_list.model_id
_ma_model_list.model_group_id
_ma_model_list.model_name
_ma_model_list.model_group_name
_ma_model_list.assembly_id
_ma_model_list.data_id
_ma_model_list.model_type
_ma_model_list.model_type_other_details
1 1 1 'test model' 'test group' 2 42 'Homology model' .
2 2 1 model2 'test group' 2 43 'Ab initio model' .
3 3 1 model3 'test group' 2 44 Other 'custom model'
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
_atom_site.B_iso_or_equiv
_atom_site.pdbx_PDB_model_num
ATOM 1 C C . ALA 1 1 ? A 1.000 2.000 3.000 . 9 A . 1
#
#
loop_
_atom_type.symbol
C
#
""")

    def test_target_ref_db_dumper(self):
        """Test TargetRefDBDumper"""

        class CustomRef(ma.reference.TargetReference):
            other_details = 'my custom ref'

        system = ma.System()
        ref1 = ma.reference.UniProt(
            code='testcode', accession='testacc', align_begin=4, align_end=8,
            isoform='testiso', ncbi_taxonomy_id='1234',
            organism_scientific='testorg')
        ref2 = ma.reference.UniProt(code='c2', accession='a2')
        ref3 = CustomRef(code='c3', accession='a3')

        e1 = ma.Entity('ACGT', references=[ref1, ref2, ref3])
        e1._id = 1
        system.target_entities.append(e1)

        dumper = ma.dumper._TargetRefDBDumper()
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
1 UNP . testcode testacc testiso 4 8 1234 testorg
1 UNP . c2 a2 ? 1 4 . .
1 Other 'my custom ref' c3 a3 ? 1 4 . .
#
""")

    def test_alignment_dumper(self):
        """Test AlignmentDumper"""

        class CustomRef(ma.reference.TemplateReference):
            other_details = 'my custom ref'

        class Alignment(ma.alignment.Global, ma.alignment.Pairwise):
            pass

        system = ma.System()
        tmp_e = ma.Entity('ACG')
        tmp_e._id = 1
        tgt_e = ma.Entity('ACE')
        tgt_e._id = 1
        system.entities.extend((tmp_e, tgt_e))
        asym = ma.AsymUnit(tgt_e, id='A')
        asym._id = 'A'
        system.asym_units.append(asym)
        ref1 = ma.reference.PDB('1abc')
        ref2 = CustomRef('2xyz')
        tr = ma.Transformation.identity()
        tr._id = 42
        t = ma.Template(tmp_e, asym_id='H', model_num=1, name='testtmp',
                        transformation=tr, references=[ref1, ref2])
        t._data_id = 99
        p = ma.alignment.Pair(
            template=t.segment('AC-G', 1, 3),
            target=asym.segment('ACE-', 1, 3),
            score=ma.alignment.BLASTEValue("1e-15"),
            identity=ma.alignment.ShorterSequenceIdentity(42.))
        aln = Alignment(name='testaln', pairs=[p])
        aln._data_id = 100
        system.alignments.append(aln)
        system._before_write()  # populate system.templates

        dumper = ma.dumper._AlignmentDumper()
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
1 1 'reference database' polymer 42 99 A H 1 1
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
1 PDB . 1abc
1 Other 'my custom ref' 2xyz
#
#
loop_
_ma_target_template_poly_mapping.id
_ma_target_template_poly_mapping.template_segment_id
_ma_target_template_poly_mapping.target_asym_id
_ma_target_template_poly_mapping.target_seq_id_begin
_ma_target_template_poly_mapping.target_seq_id_end
1 1 A 1 3
#
#
loop_
_ma_alignment_info.alignment_id
_ma_alignment_info.data_id
_ma_alignment_info.software_group_id
_ma_alignment_info.alignment_length
_ma_alignment_info.alignment_type
_ma_alignment_info.alignment_mode
1 100 . . 'target-template pairwise alignment' global
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
#
#
loop_
_ma_alignment.ordinal_id
_ma_alignment.alignment_id
_ma_alignment.target_template_flag
_ma_alignment.sequence
1 1 1 ACE-
2 1 2 AC-G
#
""")

    def test_template_transform_dumper(self):
        """Test TemplateTransformDumper"""
        system = ma.System()
        tr1 = ma.Transformation(
            rot_matrix=[[-0.64, 0.09, 0.77], [0.76, -0.12, 0.64],
                        [0.15, 0.99, 0.01]],
            tr_vector=[1., 2., 3.])
        system.template_transformations.append(tr1)
        dumper = ma.dumper._TemplateTransformDumper()
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
        system = ma.System()
        e1 = ma.Entity("D")
        e1._id = 42
        e1._data_id = 99
        system.target_entities.append(e1)

        a1 = ma.AsymUnit(e1, 'foo')
        a1._id = 'X'
        system.asym_units.append(a1)

        dumper = ma.dumper._TargetEntityDumper()
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

    def test_assembly_dumper(self):
        """Test AssemblyDumper"""
        system = ma.System()
        e1 = ma.Entity('ACGT')
        e1._id = 42
        system.entities.append(e1)
        asym = ma.AsymUnit(e1, 'foo')
        system.asym_units.append(asym)
        asmb = ma.Assembly((asym,), name='foo', description='bar')
        system.assemblies.append(asmb)

        dumper = ihm.dumper._StructAsymDumper()  # Assign _ordinal_id
        dumper.finalize(system)

        dumper = ma.dumper._AssemblyDumper()
        dumper.finalize(system)
        out = _get_dumper_output(dumper, system)
        self.assertEqual(out, """#
loop_
_ma_struct_assembly.ordinal_id
_ma_struct_assembly.assembly_id
_ma_struct_assembly.entity_id
_ma_struct_assembly.asym_id
_ma_struct_assembly.seq_id_begin
_ma_struct_assembly.seq_id_end
1 1 42 A 1 4
#
#
loop_
_ma_struct_assembly_details.assembly_id
_ma_struct_assembly_details.assembly_name
_ma_struct_assembly_details.assembly_description
1 foo bar
#
""")


if __name__ == '__main__':
    unittest.main()
