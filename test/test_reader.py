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
import ma.reader
import ma.reference


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
        s, = ma.reader.read(StringIO(cif))

    def test_old_file_read_fail(self):
        """Test failure reading old files"""
        cif = """
loop_
_audit_conform.dict_name
_audit_conform.dict_version
mmcif_pdbx.dic  5.311
mmcif_ma.dic    0.1.3
"""
        self.assertRaises(ma.reader.OldFileError,
                          ma.reader.read, StringIO(cif), reject_old_file=True)

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
            s, = ma.reader.read(StringIO(cif), reject_old_file=True)

    def test_software_group_handler(self):
        """Test SoftwareGroupHandler"""
        cif = """
loop_
_ma_software_group.ordinal_id
_ma_software_group.group_id
_ma_software_group.software_id
_ma_software_group.parameter_group_id
1 1 1 .
2 1 2 .
3 2 3 .
"""
        s, = ma.reader.read(StringIO(cif))
        s1, s2, s3 = s.software
        g1, g2 = s.software_groups
        self.assertEqual(len(g1), 2)
        self.assertEqual(len(g2), 1)
        self.assertEqual(g1[0], s1)
        self.assertEqual(g1[1], s2)
        self.assertEqual(g2[0], s3)

    def test_enumeration_mapper(self):
        """Test EnumerationMapper class"""
        m = ma.reader._EnumerationMapper(
            ma.reference, ma.reference.TargetReference)
        # Check get of a handled enumeration value
        unp = m.get('UNP', None)
        self.assertIs(unp, ma.reference.UniProt)
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
        s, = ma.reader.read(StringIO(cif))
        e, = s.entities
        r1, r2, r3, r4 = e.references
        self.assertIsInstance(r1, ma.reference.UniProt)
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
        s, = ma.reader.read(StringIO(cif))
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
        s, = ma.reader.read(StringIO(cif))
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
        s, = ma.reader.read(StringIO(cif))
        t, = s.templates
        r1, r2, r3 = t.references
        self.assertIsInstance(r1, ma.reference.PDB)
        self.assertEqual(r1.accession, '3nc1')
        self.assertEqual(r2.name, 'MIS')
        self.assertIsNone(r2.other_details)
        self.assertEqual(r3.name, 'Other')
        self.assertEqual(r3.other_details, 'foo')

    def test_model_list_handler(self):
        """Test _ModelListHandler"""
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
1 2 1 '2nd best scoring model' 'All models' 99 5 'Homology model' .
1 3 2 'Best scoring model' 'group2' 99 6 'Homology model' .
"""
        s, = ma.reader.read(StringIO(cif))
        mg1, mg2 = s.model_groups
        self.assertEqual(mg1.name, 'All models')
        m1, m2 = list(mg1)
        self.assertEqual(m1.name, 'Best scoring model')
        self.assertEqual(m2.name, '2nd best scoring model')
        self.assertEqual(mg2.name, 'group2')
        m1, = list(mg2)
        self.assertEqual(m1.name, 'Best scoring model')
        self.assertEqual(m1.assembly._id, '99')

    def test_assembly_handler(self):
        """Test _AssemblyHandler"""
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
"""
        s, = ma.reader.read(StringIO(cif))
        a, = s.assemblies
        self.assertEqual(len(a), 2)
        # Complete asym
        self.assertIsInstance(a[0], ma.AsymUnit)
        # asym range
        self.assertIsInstance(a[1], ma.AsymUnitRange)
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
        s, = ma.reader.read(StringIO(cif))
        seg, = s.template_segments
        self.assertEqual(seg.template._id, '42')
        self.assertEqual(seg.seq_id_range, (2, 9))


if __name__ == '__main__':
    unittest.main()
