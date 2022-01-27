import sys
import unittest
import utils
import os
if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from io import BytesIO as StringIO

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.reader
import modelcif.reference
import ihm


class Tests(unittest.TestCase):

    def test_old_file_read_default(self):
        """Test default handling of old files"""
        cif = """
loop_
_audit_conform.dict_name
_audit_conform.dict_version
mmcif_pdbx.dic  5.311
mmcif_ma.dic    0.14
"""
        s, = modelcif.reader.read(StringIO(cif))

    def test_old_file_read_fail(self):
        """Test failure reading old files"""
        cif = """
loop_
_audit_conform.dict_name
_audit_conform.dict_version
mmcif_pdbx.dic  5.311
mmcif_ma.dic    0.1.3
"""
        self.assertRaises(modelcif.reader.OldFileError,
                          modelcif.reader.read, StringIO(cif),
                          reject_old_file=True)

    def test_new_file_read_ok(self):
        """Test success reading not-old files"""
        # File read is OK if version is new enough, or version cannot be parsed
        # because it is non-int or has too many elements
        for ver in ('1.3.2', '1.3', '0.0.4.3', '0.0a'):
            cif = """
loop_
_audit_conform.dict_name
_audit_conform.dict_version
mmcif_pdbx.dic  5.311
mmcif_ma.dic    %s
""" % ver
            s, = modelcif.reader.read(StringIO(cif), reject_old_file=True)

    def test_software_group_handler(self):
        """Test SoftwareGroupHandler and SoftwareParameterHandler"""
        cif = """
loop_
_ma_software_parameter.parameter_id
_ma_software_parameter.group_id
_ma_software_parameter.data_type
_ma_software_parameter.name
_ma_software_parameter.value
_ma_software_parameter.description
1 1 integer foo 42 foodesc
2 1 boolean bar YES .
3 1 string baz ok .
#
loop_
_ma_software_group.ordinal_id
_ma_software_group.group_id
_ma_software_group.software_id
_ma_software_group.parameter_group_id
1 1 1 .
2 1 2 .
3 2 3 1
"""
        s, = modelcif.reader.read(StringIO(cif))
        s1, s2, s3 = s.software
        g1, g2 = s.software_groups
        self.assertEqual(len(g1), 2)
        self.assertEqual(len(g2), 1)
        self.assertEqual(g1.parameters, [])
        self.assertEqual(g1[0], s1)
        self.assertEqual(g1[1], s2)
        self.assertEqual(g2[0], s3)
        p1, p2, p3 = g2.parameters
        self.assertEqual(p1.name, 'foo')
        self.assertEqual(p1.value, 42)
        self.assertEqual(p1.description, 'foodesc')
        self.assertEqual(p2.name, 'bar')
        self.assertTrue(p2.value)
        self.assertIsNone(p2.description)
        self.assertEqual(p3.name, 'baz')
        self.assertEqual(p3.value, 'ok')
        self.assertIsNone(p3.description)

    def test_enumeration_mapper(self):
        """Test EnumerationMapper class"""
        m = modelcif.reader._EnumerationMapper(
            modelcif.reference, modelcif.reference.TargetReference)
        # Check get of a handled enumeration value
        unp = m.get('UNP', None)
        self.assertIs(unp, modelcif.reference.UniProt)
        self.assertEqual(unp.name, 'UNP')
        self.assertIsNone(unp.other_details)
        # We should get the same class each time (case insensitive)
        unp2 = m.get('unp', None)
        self.assertIs(unp, unp2)
        # Check get of an unhandled value
        miss = m.get('MIS', None)
        self.assertEqual(miss.name, 'MIS')
        self.assertIsNone(unp.other_details)
        # We should get the same class each time (case insensitive)
        miss2 = m.get('mis', None)
        self.assertIs(miss, miss2)
        # Check get of a custom "other" value
        custom = m.get('other', "custom type 1")
        self.assertEqual(custom.name, 'Other')
        self.assertEqual(custom.other_details, "custom type 1")
        # We should get the same class each time (case insensitive)
        custom2 = m.get('Other', "CUSTOM TYPE 1")
        self.assertIs(custom, custom2)
        # Check get of a different custom "other" value
        custom = m.get('other', "custom type 2")
        self.assertEqual(custom.name, 'Other')
        self.assertEqual(custom.other_details, "custom type 2")

    def test_database_handler(self):
        """Test DatabaseHandler"""
        cif = """
_database_2.database_id                'PDB'
_database_2.database_code              '5HVP'
"""
        s, = modelcif.reader.read(StringIO(cif))
        self.assertEqual(s.database.id, 'PDB')
        self.assertEqual(s.database.code, '5HVP')

    def test_target_ref_db_handler(self):
        """Test TargetRefDBHander"""
        cif = """
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
1 UNP . MED1_YEAST Q12321 test_iso 1 10 test_tax test_org
1 Other foo . . ? 1 10 . .
1 other bar . . ? 1 10 . .
1 MIS baz . . ? 1 10 . .
"""
        s, = modelcif.reader.read(StringIO(cif))
        e, = s.entities
        r1, r2, r3, r4 = e.references
        self.assertIsInstance(r1, modelcif.reference.UniProt)
        self.assertEqual(r1.code, 'MED1_YEAST')
        self.assertEqual(r1.accession, 'Q12321')
        self.assertEqual(r1.isoform, 'test_iso')
        self.assertEqual(r1.align_begin, 1)
        self.assertEqual(r1.align_end, 10)
        self.assertEqual(r1.ncbi_taxonomy_id, 'test_tax')
        self.assertEqual(r1.organism_scientific, 'test_org')
        self.assertEqual(r2.name, 'Other')
        self.assertEqual(r2.other_details, 'foo')
        self.assertEqual(r3.name, 'Other')
        self.assertEqual(r3.other_details, 'bar')
        self.assertEqual(r4.name, 'MIS')
        self.assertIsNone(r4.other_details)  # should be ignored

    def test_transformation_handler(self):
        """Test _TransformationHandler"""
        cif = """
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
1 1.000000 0.000000 0.000000 0.000000 1.000000 0.000000 0.000000 0.000000
1.000000 0.000 0.000 0.000
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, = s.template_transformations
        self.assertAlmostEqual(t.rot_matrix[0][0], 1.0, delta=1e-6)
        self.assertAlmostEqual(t.tr_vector[0], 0.0, delta=1e-6)

    def test_template_details_handler(self):
        """Test _TemplateDetailsHandler"""
        cif = """
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
1 1 'reference database' polymer 1 2 A B 3 4
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, = s.templates
        self.assertEqual(t.entity._id, '3')
        self.assertEqual(t.model_num, 4)
        self.assertEqual(t.asym_id, 'B')

    def test_template_ref_db_handler(self):
        """Test _TemplateRefDBHandler"""
        cif = """
loop_
_ma_template_ref_db_details.template_id
_ma_template_ref_db_details.db_name
_ma_template_ref_db_details.db_name_other_details
_ma_template_ref_db_details.db_accession_code
1 PDB . 3nc1
1 MIS . testacc
1 Other foo acc2
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, = s.templates
        r1, r2, r3 = t.references
        self.assertIsInstance(r1, modelcif.reference.PDB)
        self.assertEqual(r1.accession, '3nc1')
        self.assertEqual(r2.name, 'MIS')
        self.assertIsNone(r2.other_details)
        self.assertEqual(r3.name, 'Other')
        self.assertEqual(r3.other_details, 'foo')

    def _get_models_cif(self):
        cif = """
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
1 1 1 'Best scoring model' 'All models' 99 4 'Homology model' .
1 2 1 '2nd best scoring model' 'All models' 99 5 'Ab initio model' .
1 3 2 'Best scoring model' 'group2' 99 6 'Other' 'Custom other model'
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
ATOM 1 C CA . ASP 1 1 ? A 1.000 2.000 3.000 . 1 A . 6
ATOM 2 C CA . ASP 1 1 ? A 1.000 2.000 3.000 . 1 A . 8
"""
        return cif

    def test_model_list_handler_default(self):
        """Test _ModelListHandler with default model class"""
        cif = self._get_models_cif()
        s, = modelcif.reader.read(StringIO(cif))
        mg1, mg2, mg3 = s.model_groups
        self.assertEqual(mg1.name, 'All models')
        m1, m2 = list(mg1)
        self.assertIsInstance(m1, modelcif.model.HomologyModel)
        self.assertEqual(m1.model_type, 'Homology model')
        self.assertIsNone(m1.other_details)
        self.assertIsInstance(m2, modelcif.model.AbInitioModel)
        self.assertEqual(m2.model_type, 'Ab initio model')
        self.assertIsNone(m2.other_details)
        self.assertEqual(m1.name, 'Best scoring model')
        self.assertEqual(m2.name, '2nd best scoring model')
        self.assertEqual(mg2.name, 'group2')
        m1, = list(mg2)
        self.assertEqual(m1.model_type, 'Other')
        self.assertEqual(m1.other_details, 'Custom other model')
        self.assertEqual(m1.name, 'Best scoring model')
        self.assertEqual(m1.assembly._id, '99')
        # Last group is auto-created to contain the non-grouped models
        # referenced by atom_site
        self.assertIsNone(mg3.name)
        m1, m2 = list(mg3)
        self.assertEqual(m1.model_type, 'Other')
        self.assertEqual(m1._id, '6')
        self.assertEqual(m2.model_type, 'Other')
        self.assertEqual(m2._id, '8')

    def test_model_list_handler_custom(self):
        """Test _ModelListHandler with custom model class"""
        class MyModel(modelcif.model.Model):
            """Custom model type"""
            pass
        cif = self._get_models_cif()
        s, = modelcif.reader.read(StringIO(cif), model_class=MyModel)
        mg1, mg2, mg3 = s.model_groups
        m1, m2 = list(mg1)
        m3, = list(mg2)
        m4, m5 = list(mg3)
        # Custom model type should always be returned, regardless of what
        # the mmCIF file says it is, but model_type should be set
        self.assertIsInstance(m1, MyModel)
        self.assertIsInstance(m2, MyModel)
        self.assertIsInstance(m3, MyModel)
        self.assertIsInstance(m4, MyModel)
        self.assertIsInstance(m5, MyModel)
        self.assertEqual(m1.model_type, 'Homology model')
        self.assertEqual(m2.model_type, 'Ab initio model')
        self.assertEqual(m3.model_type, 'Other')
        self.assertEqual(m4.model_type, 'Other')
        self.assertEqual(m5.model_type, 'Other')

    def test_assembly_handler(self):
        """Test _AssemblyHandler and _AssemblyDetailsHandler"""
        cif = """
loop_
_entity_poly_seq.entity_id
_entity_poly_seq.num
_entity_poly_seq.mon_id
1 1 ALA
1 2 ALA
#
loop_
_struct_asym.id
_struct_asym.entity_id
_struct_asym.details
A 1 Nup84
#
loop_
_ma_struct_assembly.ordinal_id
_ma_struct_assembly.assembly_id
_ma_struct_assembly.entity_id
_ma_struct_assembly.asym_id
_ma_struct_assembly.seq_id_begin
_ma_struct_assembly.seq_id_end
1 1 1 A 1 2
2 1 1 A 1 1
#
loop_
_ma_struct_assembly_details.assembly_id
_ma_struct_assembly_details.assembly_name
_ma_struct_assembly_details.assembly_description
1 foo bar
"""
        s, = modelcif.reader.read(StringIO(cif))
        a, = s.assemblies
        self.assertEqual(a.name, 'foo')
        self.assertEqual(a.description, 'bar')
        self.assertEqual(len(a), 2)
        # Complete asym
        self.assertIsInstance(a[0], modelcif.AsymUnit)
        # asym range
        self.assertIsInstance(a[1], modelcif.AsymUnitRange)
        self.assertEqual(a[1].seq_id_range, (1, 1))

    def test_template_poly_segment_handler(self):
        """Test _TemplatePolySegmentHandler"""
        cif = """
loop_
_ma_template_poly_segment.id
_ma_template_poly_segment.template_id
_ma_template_poly_segment.residue_number_begin
_ma_template_poly_segment.residue_number_end
1 42 2 9
"""
        s, = modelcif.reader.read(StringIO(cif))
        seg, = s.template_segments
        self.assertEqual(seg.template._id, '42')
        self.assertEqual(seg.seq_id_range, (2, 9))

    def test_data__handler(self):
        """Test _DataHandler"""
        cif = """
loop_
_ma_data.id
_ma_data.name
_ma_data.content_type
_ma_data.content_type_other_details
1 'Template Structure' 'template structure' .
2 'Model subunit' target .
3 'Default model name' 'model coordinates' .
#
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
1 1 'reference database' polymer 1 1 A A 1 1
#
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
1 1 1 'Model name' 'All models' 1 3 'Homology model' .
"""
        s, = modelcif.reader.read(StringIO(cif))
        d1, d2, d3 = s.data
        self.assertIsInstance(d1, modelcif.Template)
        # d2 is not referenced by any other table, so gets Data base class
        self.assertIsInstance(d2, modelcif.data.Data)
        self.assertIsInstance(d3, modelcif.model.Model)
        # Name not given in template_details so taken from ma_data
        self.assertEqual(d1.name, 'Template Structure')
        self.assertEqual(d2.name, 'Model subunit')
        # Name in model_list used rather than that from ma_data
        self.assertEqual(d3.name, 'Model name')

    def test_data_group_handler(self):
        """Test _DataGroupHandler"""
        cif = """
loop_
_ma_data.id
_ma_data.name
_ma_data.content_type
_ma_data.content_type_other_details
1 'Template Structure' 'template structure' .
2 'Model subunit' target .
#
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
1 1 'reference database' polymer 1 1 A A 1 1
#
loop_
_ma_data_group.ordinal_id
_ma_data_group.group_id
_ma_data_group.data_id
1 1 1
2 1 2
3 2 3
"""
        s, = modelcif.reader.read(StringIO(cif))
        g1, g2, = s.data_groups
        self.assertEqual(len(g1), 2)
        self.assertIsInstance(g1[0], modelcif.Template)
        self.assertEqual(g1[0]._data_id, '1')
        self.assertIsInstance(g1[1], modelcif.data.Data)
        self.assertEqual(g1[1]._data_id, '2')
        self.assertEqual(len(g2), 1)
        self.assertIsNone(g2[0])

    def test_protocol_handler(self):
        """Test _ProtocolHandler"""
        cif = """
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
1 1 1 'template search' 'ModPipe Seq-Prf (0001)' . 1 1 2
2 1 2 modeling . . 2 2 1
3 1 3 'model selection' . . 1 1 1
4 1 4 other testname testdetails 42 99 66
"""
        s, = modelcif.reader.read(StringIO(cif))
        p, = s.protocols
        self.assertEqual(len(p.steps), 4)
        s1, s2, s3, s4 = p.steps
        self.assertIsInstance(s1, modelcif.protocol.TemplateSearchStep)
        self.assertIsInstance(s2, modelcif.protocol.ModelingStep)
        self.assertIsInstance(s3, modelcif.protocol.ModelSelectionStep)
        self.assertIsInstance(s4, modelcif.protocol.Step)
        self.assertEqual(s4.method_type, "other")
        self.assertEqual(s4.name, "testname")
        self.assertEqual(s4.details, "testdetails")
        self.assertEqual(s4.input_data._id, '99')
        self.assertEqual(s4.output_data._id, '66')
        self.assertEqual(s4.software._id, '42')

    def test_target_entity_handler(self):
        """Test _TargetEntityHandler"""
        cif = """
loop_
_ma_target_entity.entity_id
_ma_target_entity.data_id
_ma_target_entity.origin
1 2 'reference database'
"""
        s, = modelcif.reader.read(StringIO(cif))
        e, = s.entities
        self.assertEqual(e._data_id, '2')

    def test_qa_metric_global_handler(self):
        """Test _QAMetricGlobalHandler"""
        cif = """
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
1 1 1 'Best scoring model' 'All models' 1 4 'Homology model' .
#
loop_
_ma_qa_metric.id
_ma_qa_metric.name
_ma_qa_metric.description
_ma_qa_metric.type
_ma_qa_metric.mode
_ma_qa_metric.type_other_details
_ma_qa_metric.software_group_id
1 MPQS 'ModPipe Quality Score' other global
'composite score, values >1.1 are considered reliable' 1
2 zDOPE 'Normalized DOPE' zscore global . 2
3 'TSVMod RMSD' 'TSVMod predicted RMSD (MSALL)' distance global . .
4 'TSVMod NO35' 'TSVMod predicted native overlap (MSALL)' 'normalized score'
global . .
#
loop_
_ma_qa_metric_global.ordinal_id
_ma_qa_metric_global.model_id
_ma_qa_metric_global.metric_id
_ma_qa_metric_global.metric_value
1 1 1 1.0
2 1 2 2.0
3 1 3 3.0
4 1 4 4.0
"""
        s, = modelcif.reader.read(StringIO(cif))
        mg, = s.model_groups
        m, = mg
        q1, q2, q3, q4 = m.qa_metrics
        self.assertIsInstance(q1, modelcif.qa_metric.Global)
        self.assertEqual(q1.type, "other")
        self.assertEqual(q1.name, "MPQS")
        self.assertEqual(type(q1).__name__, "MPQS")
        self.assertEqual(q1.description, "ModPipe Quality Score")
        self.assertEqual(q1.__doc__, "ModPipe Quality Score")
        self.assertEqual(q1.software._id, '1')
        self.assertAlmostEqual(q1.value, 1.0, delta=1e-6)

        self.assertIsInstance(q2, modelcif.qa_metric.Global)
        self.assertIsInstance(q2, modelcif.qa_metric.ZScore)
        self.assertAlmostEqual(q2.value, 2.0, delta=1e-6)

        self.assertIsInstance(q3, modelcif.qa_metric.Global)
        self.assertIsInstance(q3, modelcif.qa_metric.Distance)
        self.assertAlmostEqual(q3.value, 3.0, delta=1e-6)

        self.assertIsInstance(q4, modelcif.qa_metric.Global)
        self.assertIsInstance(q4, modelcif.qa_metric.NormalizedScore)

    def test_qa_metric_local_handler(self):
        """Test _QAMetricLocalHandler"""
        cif = """
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
1 1 1 'Best scoring model' 'All models' 1 4 'Homology model' .
#
loop_
_ma_qa_metric.id
_ma_qa_metric.name
_ma_qa_metric.description
_ma_qa_metric.type
_ma_qa_metric.mode
_ma_qa_metric.type_other_details
_ma_qa_metric.software_group_id
1 'test local' 'some local score' 'normalized score' local . .
#
loop_
_ma_qa_metric_local.ordinal_id
_ma_qa_metric_local.model_id
_ma_qa_metric_local.label_asym_id
_ma_qa_metric_local.label_seq_id
_ma_qa_metric_local.label_comp_id
_ma_qa_metric_local.metric_id
_ma_qa_metric_local.metric_value
1 1 A 2 CYS 1 1.0
"""
        s, = modelcif.reader.read(StringIO(cif))
        mg, = s.model_groups
        m, = mg
        q1, = m.qa_metrics
        self.assertIsInstance(q1, modelcif.qa_metric.Local)
        self.assertIsInstance(q1, modelcif.qa_metric.NormalizedScore)
        self.assertEqual(q1.type, "normalized score")
        self.assertEqual(q1.name, "test local")
        self.assertEqual(q1.description, "some local score")
        self.assertIsNone(q1.software)
        self.assertEqual(q1.residue.asym._id, 'A')
        self.assertEqual(q1.residue.seq_id, 2)
        self.assertAlmostEqual(q1.value, 1.0, delta=1e-6)

    def test_qa_metric_pairwise_handler(self):
        """Test _QAMetricPairwiseHandler"""
        cif = """
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
1 1 1 'Best scoring model' 'All models' 1 4 'Homology model' .
#
loop_
_ma_qa_metric.id
_ma_qa_metric.name
_ma_qa_metric.description
_ma_qa_metric.type
_ma_qa_metric.mode
_ma_qa_metric.type_other_details
_ma_qa_metric.software_group_id
1 'test pair' 'some pair score' 'normalized score' local-pairwise . .
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
1 1 A 2 CYS B 4 GLY 1 1.0
"""
        s, = modelcif.reader.read(StringIO(cif))
        mg, = s.model_groups
        m, = mg
        q1, = m.qa_metrics
        self.assertIsInstance(q1, modelcif.qa_metric.LocalPairwise)
        self.assertIsInstance(q1, modelcif.qa_metric.NormalizedScore)
        self.assertEqual(q1.type, "normalized score")
        self.assertEqual(q1.name, "test pair")
        self.assertEqual(q1.description, "some pair score")
        self.assertIsNone(q1.software)
        self.assertEqual(q1.residue1.asym._id, 'A')
        self.assertEqual(q1.residue1.seq_id, 2)
        self.assertEqual(q1.residue2.asym._id, 'B')
        self.assertEqual(q1.residue2.seq_id, 4)
        self.assertAlmostEqual(q1.value, 1.0, delta=1e-6)

    def test_alignment_info_details_handler(self):
        """Test _AlignmentInfoHandler and _AlignmentDetailsHandler"""
        cif = """
loop_
_ma_alignment_info.alignment_id
_ma_alignment_info.data_id
_ma_alignment_info.software_group_id
_ma_alignment_info.alignment_length
_ma_alignment_info.alignment_type
_ma_alignment_info.alignment_mode
1 3 1 . 'target-template pairwise alignment' global
2 4 1 . 'target-template pairwise alignment' global
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
1 1 1 A 'BLAST e-value' . 1.0 45.000 'Length of the shorter sequence' .
#
loop_
_ma_alignment.ordinal_id
_ma_alignment.alignment_id
_ma_alignment.target_template_flag
_ma_alignment.sequence
1 1 1 DSYV-ETLD
2 1 2 DMACDTFIK
#
loop_
_ma_target_template_poly_mapping.id
_ma_target_template_poly_mapping.template_segment_id
_ma_target_template_poly_mapping.target_asym_id
_ma_target_template_poly_mapping.target_seq_id_begin
_ma_target_template_poly_mapping.target_seq_id_end
1 1 A 1 8
"""
        s, = modelcif.reader.read(StringIO(cif))
        a1, a2, = s.alignments
        self.assertIs(a1.__class__, a2.__class__)
        self.assertIsInstance(a1, modelcif.alignment.Global)
        self.assertIsInstance(a1, modelcif.alignment.Pairwise)
        self.assertEqual(len(a2.pairs), 0)
        p, = a1.pairs
        self.assertIsInstance(p.score, modelcif.alignment.BLASTEValue)
        self.assertAlmostEqual(p.score.value, 1.0, delta=1e-6)
        self.assertIsInstance(p.identity,
                              modelcif.alignment.ShorterSequenceIdentity)
        self.assertAlmostEqual(p.identity.value, 45.0, delta=1e-6)
        self.assertIsInstance(p.template, modelcif.TemplateSegment)
        self.assertEqual(p.template._id, '1')
        self.assertEqual(p.template.gapped_sequence, 'DMACDTFIK')
        self.assertIsInstance(p.target, ihm.AsymUnitSegment)
        self.assertEqual(p.target.asym._id, 'A')
        self.assertEqual(p.target.gapped_sequence, 'DSYV-ETLD')
        self.assertEqual(p.target.seq_id_range, (1, 8))


if __name__ == '__main__':
    unittest.main()
