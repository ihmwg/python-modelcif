from datetime import date
import unittest
import utils
import os
import datetime
from io import StringIO

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.reader
import modelcif.reference
import ihm
import ihm.reader


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
4 1 integer-csv intlist 1,2,3,4 .
5 1 float-csv floatlist 1.5,3.8 .
#
loop_
_ma_software_group.ordinal_id
_ma_software_group.group_id
_ma_software_group.software_id
_ma_software_group.parameter_group_id
1 1 1 .
2 1 2 .
3 2 3 .
4 2 4 1
"""
        s, = modelcif.reader.read(StringIO(cif))
        s1, s2, s3, s4 = s.software
        g1, g2 = s.software_groups
        self.assertEqual(len(g1), 2)
        self.assertEqual(len(g2), 2)
        self.assertIsInstance(g1[0], modelcif.Software)
        self.assertIsInstance(g1[1], modelcif.Software)
        self.assertEqual(g1[0], s1)
        self.assertEqual(g1[1], s2)

        self.assertIsInstance(g2[0], modelcif.Software)
        self.assertIsInstance(g2[1], modelcif.SoftwareWithParameters)
        self.assertEqual(g2[0], s3)
        self.assertEqual(g2[1].software, s4)
        p1, p2, p3, intlist, floatlist = g2[1].parameters
        self.assertEqual(p1.name, 'foo')
        self.assertEqual(p1.value, 42)
        self.assertEqual(p1.description, 'foodesc')
        self.assertEqual(p2.name, 'bar')
        self.assertTrue(p2.value)
        self.assertIsNone(p2.description)
        self.assertEqual(p3.name, 'baz')
        self.assertEqual(p3.value, 'ok')
        self.assertIsNone(p3.description)
        self.assertEqual(intlist.value, [1, 2, 3, 4])
        f1, f2 = floatlist.value
        self.assertAlmostEqual(f1, 1.5, delta=1e-1)
        self.assertAlmostEqual(f2, 3.8, delta=1e-1)

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
_ma_target_ref_db_details.seq_db_sequence_version_date
_ma_target_ref_db_details.seq_db_sequence_checksum
_ma_target_ref_db_details.is_primary
1 UNP . MED1_YEAST Q12321 test_iso 1 10 test_tax test_org 1996-11-01
637FEA3E78D915BC YES
1 Other foo . . ? 1 10 . . . . NO
1 other bar . . ? 1 10 . . . . .
1 MIS baz . . ? 1 10 . . . . .
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
        self.assertEqual(r1.sequence_version_date, date(1996, 11, 1))
        self.assertIsNone(r1.sequence)
        self.assertIsNone(r1.details)
        self.assertTrue(r1.is_primary)
        self.assertEqual(r1.alignments, [])
        self.assertEqual(r2.name, 'Other')
        self.assertFalse(r2.is_primary)
        self.assertEqual(r2.other_details, 'foo')
        self.assertEqual(r3.name, 'Other')
        self.assertEqual(r3.other_details, 'bar')
        self.assertIsNone(r3.is_primary)
        self.assertEqual(r4.name, 'MIS')
        self.assertIsNone(r4.other_details)  # should be ignored

    def test_target_ref_db_handler_with_struct_ref(self):
        """Test TargetRefDBHander combined with struct_ref info"""
        cif = """
loop_
_struct_ref.id
_struct_ref.entity_id
_struct_ref.db_name
_struct_ref.db_code
_struct_ref.pdbx_db_accession
_struct_ref.pdbx_align_begin
_struct_ref.pdbx_seq_one_letter_code
_struct_ref.details
1 1 UNP MED1_YEAST Q12321 1 DSYVETLDCC "test details"
2 1 UNP sr_only_code sr_only_acc 1 DSYVETLDPP .
#
#
loop_
_struct_ref_seq.align_id
_struct_ref_seq.ref_id
_struct_ref_seq.seq_align_beg
_struct_ref_seq.seq_align_end
_struct_ref_seq.db_align_beg
_struct_ref_seq.db_align_end
1 1 1 10 1 10
2 2 1 10 1 10
#
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
1 UNP . MED1_YEAST Q12321 test_iso 1 10 test_tax test_org 1996-11-01
637FEA3E78D915BC
1 UNP . rd_only_code rd_only_acc rd_only_iso . . . . . .
"""
        s, = modelcif.reader.read(StringIO(cif))
        e, = s.entities
        r1, r2, r3 = e.references
        # r1 should contain both target_ref_db and struct_ref info
        self.assertIsInstance(r1, modelcif.reference.UniProt)
        self.assertEqual(r1.code, 'MED1_YEAST')
        self.assertEqual(r1.accession, 'Q12321')
        self.assertEqual(r1.isoform, 'test_iso')
        self.assertEqual(r1.align_begin, 1)
        self.assertEqual(r1.align_end, 10)
        self.assertEqual(r1.ncbi_taxonomy_id, 'test_tax')
        self.assertEqual(r1.organism_scientific, 'test_org')
        self.assertEqual(r1.sequence_version_date, date(1996, 11, 1))
        self.assertEqual(r1.sequence, 'DSYVETLDCC')
        self.assertEqual(r1.details, "test details")
        a, = r1.alignments
        self.assertEqual(a.db_begin, 1)
        self.assertEqual(a.db_end, 10)
        self.assertEqual(a.entity_begin, 1)
        self.assertEqual(a.entity_end, 10)
        # r2 should contain only target_ref_db info
        self.assertIsInstance(r2, modelcif.reference.UniProt)
        self.assertEqual(r2.code, 'rd_only_code')
        self.assertEqual(r2.accession, 'rd_only_acc')
        self.assertEqual(r2.isoform, 'rd_only_iso')
        self.assertIsNone(r2.sequence)
        # r3 should contain only struct_ref info
        self.assertIsInstance(r3, modelcif.reference.UniProt)
        self.assertEqual(r3.code, 'sr_only_code')
        self.assertEqual(r3.accession, 'sr_only_acc')
        self.assertIsNone(r3.isoform)
        self.assertIsNone(r3.ncbi_taxonomy_id)
        self.assertEqual(r3.sequence, 'DSYVETLDPP')
        a, = r3.alignments
        self.assertEqual(a.db_begin, 1)
        self.assertEqual(a.db_end, 10)
        self.assertEqual(a.entity_begin, 1)
        self.assertEqual(a.entity_end, 10)

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
_ma_template_details.template_auth_asym_id
1 1 'reference database' polymer 1 2 A B 3 4 Z
2 2 'reference database' polymer 2 3 . B 3 4 Z
3 3 customized polymer 2 3 . B 3 4 Z
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, t2, t3 = s.templates
        self.assertIsInstance(t, modelcif.Template)
        self.assertIsInstance(t2, modelcif.Template)
        self.assertIsInstance(t3, modelcif.CustomTemplate)
        self.assertEqual(t.entity_id, '3')
        self.assertEqual(t.model_num, 4)
        self.assertEqual(t.asym_id, 'B')
        self.assertEqual(t.strand_id, 'Z')
        self.assertEqual(len(s.alignments), 0)

    def test_template_customized_handler(self):
        """Test _TemplateCustomizedHandler"""
        cif = """
loop_
_ma_template_details.ordinal_id
_ma_template_details.template_id
1 1
#
loop_
_ma_template_customized.template_id
_ma_template_customized.details
1 'details x'
2 'details y'
"""
        s, = modelcif.reader.read(StringIO(cif))
        t1, t2 = s.templates
        # template_details does not specify template_origin, so template #1
        # will be initially instantiated as a Template, and should be corrected
        # to CustomTemplate on reading template_customized:
        self.assertIsInstance(t1, modelcif.CustomTemplate)
        self.assertEqual(t1.details, 'details x')
        self.assertEqual(len(t1.atoms), 0)
        self.assertIsInstance(t2, modelcif.CustomTemplate)
        self.assertEqual(t2.details, 'details y')
        self.assertEqual(len(t2.atoms), 0)

    def test_template_details_handler_nonpoly(self):
        """Test _TemplateDetailsHandler with nonpolymeric template"""
        cif = """
loop_
_pdbx_entity_nonpoly.entity_id
_pdbx_entity_nonpoly.name
_pdbx_entity_nonpoly.comp_id
_pdbx_entity_nonpoly.ma_model_mode
3 Heme HEM explicit
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
_ma_template_details.template_auth_asym_id
1 1 'reference database' non-polymer 1 2 A B 3 4 Z
#
loop_
_ma_template_non_poly.template_id
_ma_template_non_poly.comp_id
_ma_template_non_poly.details
1 HEM "Template Heme"
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, = s.templates
        self.assertEqual(t.entity_id, '3')
        self.assertEqual(t.model_num, 4)
        self.assertEqual(t.asym_id, 'B')
        self.assertEqual(t.strand_id, 'Z')
        self.assertEqual(len(s.alignments), 0)
        self.assertEqual(t.entity.description, 'Template Heme')
        a, = s.asym_units
        self.assertIsInstance(a, modelcif.NonPolymerFromTemplate)
        self.assertIs(a.template, t)
        self.assertTrue(a.explicit)

    def test_custom_template_coord_handler(self):
        """Test reading of coordinates for CustomTemplate"""
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
_ma_template_details.template_auth_asym_id
1 1 customized polymer 2 3 . B 3 4 Z
#
loop_
_ma_template_customized.template_id
_ma_template_customized.details
1 'Provided by user'
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
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, = s.templates
        self.assertIsInstance(t, modelcif.CustomTemplate)
        self.assertEqual(t.details, 'Provided by user')
        self.assertEqual(len(t.atoms), 2)
        a1 = t.atoms[0]
        self.assertEqual(a1.seq_id, 1)
        self.assertEqual(a1.atom_id, 'CA')
        self.assertEqual(a1.type_symbol, 'C')
        self.assertAlmostEqual(a1.x, 0.0, delta=1e-2)
        self.assertAlmostEqual(a1.y, 1.0, delta=1e-2)
        self.assertAlmostEqual(a1.z, 2.0, delta=1e-2)
        self.assertAlmostEqual(a1.occupancy, 0.5, delta=1e-2)
        self.assertAlmostEqual(a1.biso, 2.0, delta=1e-2)
        self.assertAlmostEqual(a1.charge, 1.0, delta=1e-2)
        self.assertEqual(a1.auth_seq_id, 42)
        self.assertEqual(a1.auth_comp_id, 'XXX')
        self.assertEqual(a1.auth_atom_id, 'X')

        a2 = t.atoms[1]
        self.assertEqual(a2.seq_id, 2)
        self.assertEqual(a2.atom_id, 'OXT')
        self.assertEqual(a2.type_symbol, 'O')

    def test_entity_nonpoly_bad_model_mode(self):
        """Test pdbx_entity_nonpoly with missing ma_model_mode"""
        cif = """
loop_
_struct_asym.id
_struct_asym.entity_id
A 1
B 2
C 3
#
loop_
_pdbx_entity_nonpoly.entity_id
_pdbx_entity_nonpoly.name
_pdbx_entity_nonpoly.comp_id
_pdbx_entity_nonpoly.ma_model_mode
1 test1 TE1 explicit
2 test2 TE2 .
3 test3 TE3 ?
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
_ma_template_details.template_auth_asym_id
1 1 'reference database' non-polymer 1 2 A A 1 4 Z
2 2 'reference database' non-polymer 1 3 B B 2 4 Z
3 3 'reference database' non-polymer 1 4 C C 3 4 Z
#
loop_
_ma_template_non_poly.template_id
_ma_template_non_poly.comp_id
_ma_template_non_poly.details
1 TE1 test1
2 TE2 test2
3 TE3 test3
"""
        s, = modelcif.reader.read(StringIO(cif))
        a1, a2, a3 = s.asym_units
        self.assertTrue(a1.explicit)
        self.assertIsNone(a2.explicit)
        self.assertIs(a3.explicit, ihm.unknown)

    def test_template_ref_db_handler(self):
        """Test _TemplateRefDBHandler"""
        cif = """
loop_
_ma_template_ref_db_details.template_id
_ma_template_ref_db_details.db_name
_ma_template_ref_db_details.db_name_other_details
_ma_template_ref_db_details.db_accession_code
_ma_template_ref_db_details.db_version_date
1 PDB . 3nc1 2021-10-06
1 MIS . testacc .
1 Other foo acc2 .
1 PubChem . 1046 .
1 AlphaFoldDB . I6XD65 2022-06-01
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, = s.templates
        r1, r2, r3, r4, r5 = t.references
        self.assertIsInstance(r1, modelcif.reference.PDB)
        self.assertEqual(r1.accession, '3nc1')
        self.assertEqual(r1.db_version_date, date(2021, 10, 6))
        self.assertEqual(r2.name, 'MIS')
        self.assertIsNone(r2.other_details)
        self.assertIsNone(r2.db_version_date)
        self.assertEqual(r3.name, 'Other')
        self.assertEqual(r3.other_details, 'foo')
        self.assertIsInstance(r4, modelcif.reference.PubChem)
        self.assertEqual(r4.accession, '1046')
        self.assertIsInstance(r5, modelcif.reference.AlphaFoldDB)
        self.assertEqual(r5.accession, 'I6XD65')
        self.assertEqual(r5.db_version_date, date(2022, 6, 1))

    def _get_models_cif(self, old=False):
        if old:
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
2 2 1 '2nd best scoring model' 'All models' 99 5 'Ab initio model' .
3 3 2 'Best scoring model' 'group2' 99 6 'Other' 'Custom other model'
#
"""
        else:
            cif = """
loop_
_ma_model_list.ordinal_id
_ma_model_list.model_name
_ma_model_list.assembly_id
_ma_model_list.data_id
_ma_model_list.model_type
_ma_model_list.model_type_other_details
1 'Best scoring model' 99 4 'Homology model' .
2 '2nd best scoring model' 99 5 'Ab initio model' .
3 'Best scoring model' 99 6 'Other' 'Custom other model'
#
loop_
_ma_model_group.id
_ma_model_group.name
_ma_model_group.details
1 'All models' .
2 'group2' 'second group details'
#
#
loop_
_ma_model_group_link.group_id
_ma_model_group_link.model_id
1 1
1 2
2 3
#
"""
        cif += """
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

    def test_model_list_handler_default_old(self):
        """Test _ModelListHandler with default model class, old dictionary"""
        self._test_model_list_handler_default(old=True)

    def test_model_list_handler_default(self):
        """Test _ModelListHandler with default model class"""
        self._test_model_list_handler_default(old=False)

    def _test_model_list_handler_default(self, old):
        cif = self._get_models_cif(old=old)
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

    def test_model_list_handler_group_new_old(self):
        """Test _ModelListHandler handling mix of new and old style groups"""
        cif = """
loop_
_ma_model_list.ordinal_id
_ma_model_list.model_id
_ma_model_list.model_group_id
_ma_model_list.model_name
_ma_model_list.model_group_name
_ma_model_list.data_id
_ma_model_list.model_type
_ma_model_list.model_type_other_details
1 1 1 . . 4 'Homology model' .
2 2 . . . 4 'Homology model' .
3 3 1 . . 4 'Homology model' .
#
#
loop_
_ma_model_group.id
_ma_model_group.name
_ma_model_group.details
1 'group1' .
2 'group2' .
#
#
loop_
_ma_model_group_link.model_id
_ma_model_group_link.group_id
2 1
3 2
"""
        s, = modelcif.reader.read(StringIO(cif))
        # model1 is in group1, using old-style tables;
        # model2 is in group1, using new-style tables;
        # model3 is in group2 according to new-style tables but group1
        # according to old style (new-style should take precedence)
        mg1, mg2 = s.model_groups
        self.assertEqual(mg1._id, '1')
        self.assertEqual(mg2._id, '2')
        self.assertEqual([m._id for m in mg1], ['2', '1'])
        self.assertEqual([m._id for m in mg2], ['3'])

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
3 1 1 A . .
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
        self.assertEqual(len(a), 3)
        # Complete asym
        self.assertIsInstance(a[0], modelcif.AsymUnit)
        # asym range
        self.assertIsInstance(a[1], modelcif.AsymUnitRange)
        self.assertEqual(a[1].seq_id_range, (1, 1))
        # No specified range -> complete asym
        self.assertIsInstance(a[2], modelcif.AsymUnit)

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
_ma_template_details.template_auth_asym_id
1 1 'reference database' polymer 1 1 A A 1 1 Z
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
_ma_template_details.template_auth_asym_id
1 1 'reference database' polymer 1 1 A A 1 1 Z
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

    def test_data_ref_db_handler(self):
        """Test _DataRefDBHandler"""
        cif = """
loop_
_ma_data.id
_ma_data.name
_ma_data.content_type
_ma_data.content_type_other_details
1 defaultname1 'reference database' .
2 defaultname2 'reference database' .
#
loop_
_ma_data_ref_db.data_id
_ma_data_ref_db.name
_ma_data_ref_db.location_url
_ma_data_ref_db.version
_ma_data_ref_db.release_date
1 name1 url1 1.0 1979-11-22
2 . url2 . .
"""
        s, = modelcif.reader.read(StringIO(cif))
        d1, d2 = s.data
        self.assertIsInstance(d1, modelcif.ReferenceDatabase)
        self.assertIsInstance(d2, modelcif.ReferenceDatabase)
        # Name in ma_data_ref_db used rather than that from ma_data
        self.assertEqual(d1.name, 'name1')
        self.assertEqual(d1.url, 'url1')
        self.assertEqual(d1.version, '1.0')
        self.assertIsInstance(d1.release_date, date)
        self.assertEqual(d1.release_date, date(1979, 11, 22))
        # Name not given in ma_data_ref_db so taken from ma_data
        self.assertEqual(d2.name, 'defaultname2')
        self.assertIsNone(d2.version)
        self.assertIsNone(d2.release_date)

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
2 1 2 'template selection' . . . . .
3 1 3 'target-template alignment' . . . . .
4 1 4 modeling . . 2 2 1
5 1 5 'model selection' . . 1 1 1
6 1 6 'model refinement' . . . . .
7 1 7 other testname testdetails 42 99 66
"""
        s, = modelcif.reader.read(StringIO(cif))
        p, = s.protocols
        self.assertEqual(len(p.steps), 7)
        s1, s2, s3, s4, s5, s6, s7 = p.steps
        self.assertIsInstance(s1, modelcif.protocol.TemplateSearchStep)
        self.assertIsInstance(s2, modelcif.protocol.TemplateSelectionStep)
        self.assertIsInstance(s3,
                              modelcif.protocol.TargetTemplateAlignmentStep)
        self.assertIsInstance(s4, modelcif.protocol.ModelingStep)
        self.assertIsInstance(s5, modelcif.protocol.ModelSelectionStep)
        self.assertIsInstance(s6, modelcif.protocol.ModelRefinementStep)
        self.assertIsInstance(s7, modelcif.protocol.Step)
        self.assertEqual(s7.method_type, "other")
        self.assertEqual(s7.name, "testname")
        self.assertEqual(s7.details, "testdetails")
        self.assertEqual(s7.input_data._id, '99')
        self.assertEqual(s7.output_data._id, '66')
        self.assertEqual(s7.software._id, '42')

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
4 'TSVMod NO35' . 'normalized score' global . .
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
        self.assertIsNone(q4.description)
        self.assertIsNone(q4.__doc__)

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

    def test_qa_metric_feature_handler(self):
        """Test _QAMetricFeatureHandler"""
        feat = """
loop_
_ma_atom_feature.ordinal_id
_ma_atom_feature.feature_id
_ma_atom_feature.atom_id
1 1 1
#
loop_
_ma_poly_residue_feature.ordinal_id
_ma_poly_residue_feature.feature_id
_ma_poly_residue_feature.label_asym_id
_ma_poly_residue_feature.label_seq_id
_ma_poly_residue_feature.label_comp_id
1 2 Y 1 ALA
#
loop_
_ma_entity_instance_feature.ordinal_id
_ma_entity_instance_feature.feature_id
_ma_entity_instance_feature.label_asym_id
1 3 Y
"""
        qa = """
loop_
_ma_feature_list.feature_id
_ma_feature_list.feature_type
_ma_feature_list.entity_type
_ma_feature_list.details
1 atom other 'atom f'
2 residue polymer prf
3 'entity instance' polymer .
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
1 'test local' 'some local score' 'normalized score' per-feature . .
#
loop_
_ma_qa_metric_feature.ordinal_id
_ma_qa_metric_feature.model_id
_ma_qa_metric_feature.feature_id
_ma_qa_metric_feature.metric_id
_ma_qa_metric_feature.metric_value
1 1 1 1 1.0
2 1 2 1 2.0
3 1 3 1 3.0
"""
        # Test both ways to make sure features still work if they are
        # referenced by ID before their type is known
        for cif in (feat + qa, qa + feat):
            s, = modelcif.reader.read(StringIO(cif))
            mg, = s.model_groups
            m, = mg
            q1, q2, q3 = m.qa_metrics
            self.assertIsInstance(q1, modelcif.qa_metric.Feature)
            self.assertIsInstance(q1, modelcif.qa_metric.NormalizedScore)
            self.assertIsInstance(q1.feature, modelcif.AtomFeature)
            self.assertEqual(q1.feature.details, 'atom f')
            self.assertAlmostEqual(q1.value, 1.0, delta=1e-6)
            self.assertIsInstance(q2.feature, modelcif.PolyResidueFeature)
            self.assertEqual(len(q2.feature.residues), 1)
            self.assertEqual(q2.feature.residues[0].seq_id, 1)
            self.assertAlmostEqual(q2.value, 2.0, delta=1e-6)
            self.assertIsInstance(q3.feature, modelcif.EntityInstanceFeature)
            self.assertEqual(len(q3.feature.asym_units), 1)
            self.assertAlmostEqual(q3.value, 3.0, delta=1e-6)

    def test_qa_metric_feature_pairwise_handler(self):
        """Test _QAMetricFeaturePairwiseHandler"""
        feat = """
loop_
_ma_poly_residue_feature.ordinal_id
_ma_poly_residue_feature.feature_id
_ma_poly_residue_feature.label_asym_id
_ma_poly_residue_feature.label_seq_id
_ma_poly_residue_feature.label_comp_id
1 1 Y 1 ALA
2 2 Y 2 CYS
"""
        qa = """
loop_
_ma_feature_list.feature_id
_ma_feature_list.feature_type
_ma_feature_list.entity_type
_ma_feature_list.details
1 residue polymer .
2 residue polymer .
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
1 'test local' 'some local score' 'normalized score' per-feature-pair . .
#
loop_
_ma_qa_metric_feature_pairwise.ordinal_id
_ma_qa_metric_feature_pairwise.model_id
_ma_qa_metric_feature_pairwise.feature_id_1
_ma_qa_metric_feature_pairwise.feature_id_2
_ma_qa_metric_feature_pairwise.metric_id
_ma_qa_metric_feature_pairwise.metric_value
1 1 1 2 1 50.000
"""
        # Test both ways to make sure features still work if they are
        # referenced by ID before their type is known
        for cif in (feat + qa, qa + feat):
            s, = modelcif.reader.read(StringIO(cif))
            mg, = s.model_groups
            m, = mg
            q1, = m.qa_metrics
            self.assertIsInstance(q1, modelcif.qa_metric.FeaturePairwise)
            self.assertIsInstance(q1, modelcif.qa_metric.NormalizedScore)
            self.assertIsInstance(q1.feature1, modelcif.PolyResidueFeature)
            self.assertIsInstance(q1.feature2, modelcif.PolyResidueFeature)
            self.assertAlmostEqual(q1.value, 50.0, delta=1e-6)

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
3 5 1 . 'target-template MSA' local
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
2 2 1 A . . . . . .
3 3 1 A 'HHblits e-value' . 2.0 45.000 'Arithmetic mean sequence length' .
#
loop_
_ma_alignment.ordinal_id
_ma_alignment.alignment_id
_ma_alignment.target_template_flag
_ma_alignment.sequence
1 1 1 DSYV-ETLD
2 1 2 DMACDTFIK
3 1 1 DSYV-ETLD
4 1 2 DMACDTFIK
#
loop_
_ma_target_template_poly_mapping.id
_ma_target_template_poly_mapping.template_segment_id
_ma_target_template_poly_mapping.target_asym_id
_ma_target_template_poly_mapping.target_seq_id_begin
_ma_target_template_poly_mapping.target_seq_id_end
1 1 A 1 8
2 1 A 1 8
"""
        s, = modelcif.reader.read(StringIO(cif))
        a1, a2, a3, = s.alignments
        self.assertIs(a1.__class__, a2.__class__)
        self.assertIsInstance(a1, modelcif.alignment.Global)
        self.assertIsInstance(a1, modelcif.alignment.Pairwise)
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
        self.assertIsInstance(a3, modelcif.alignment.Local)
        self.assertIsInstance(a3, modelcif.alignment.Multiple)
        p, = a2.pairs
        self.assertIsNone(p.score)
        self.assertIsNone(p.identity)
        p, = a3.pairs
        self.assertIsInstance(p.score, modelcif.alignment.HHblitsEValue)
        self.assertAlmostEqual(p.score.value, 2.0, delta=1e-6)
        self.assertIsInstance(p.identity,
                              modelcif.alignment.MeanSequenceIdentity)

    def test_associated_files(self):
        """Test _AssociatedHandler and _AssociatedArchiveHandler"""
        cif = """
loop_
_ma_data.id
_ma_data.name
_ma_data.content_type
_ma_data.content_type_other_details
42 'Model subunit' target .
loop_
_ma_target_entity.entity_id
_ma_target_entity.data_id
_ma_target_entity.origin
1 99 'reference database'
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
3 model baz.txt file other other 'test file3' .
4 model baz.cif file cif other 'test mmCIF' .
5 model baz.bcif file bcif other 'test BinaryCIF' 42
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
2 99 99.txt other other 'test file99' .
3 2 bar.cif cif other 'test mmCIF in zip' .
4 2 bar.bcif bcif 'local pairwise QA scores' 'test BinaryCIF in zip' 99
5 2 bar2.bcif bcif 'QA metrics' 'test BinaryCIF in zip' 99
"""
        s, = modelcif.reader.read(StringIO(cif))
        r1, r2 = s.repositories
        self.assertEqual(r1.url_root, 'https://example.com')
        f1, zf = r1.files
        self.assertIsInstance(f1, modelcif.associated.File)
        self.assertEqual(f1.path, 'foo.txt')
        self.assertEqual(f1.details, 'test file')

        self.assertIsInstance(zf, modelcif.associated.ZipFile)
        self.assertEqual(zf.path, 't.zip')
        self.assertIsNone(zf.details)

        f2, f3, f4, f5 = zf.files
        self.assertEqual(f2.path, 'bar.txt')
        self.assertEqual(f2.details, 'test file2')
        self.assertIsNone(f2.data)
        self.assertIsInstance(f3, modelcif.associated.CIFFile)
        self.assertFalse(f3.binary)
        # QA metrics file using old "local pairwise QA scores" name
        self.assertIsInstance(
            f4, modelcif.associated.QAMetricsFile)
        self.assertEqual(f4.file_content, 'QA metrics')
        self.assertTrue(f4.binary)
        self.assertIsInstance(f4.data, modelcif.Entity)
        self.assertIsInstance(
            f5, modelcif.associated.QAMetricsFile)
        self.assertEqual(f5.file_content, 'QA metrics')
        self.assertTrue(f5.binary)
        self.assertIsInstance(f5.data, modelcif.Entity)

        self.assertIsNone(r2.url_root)
        f3, f4, f5 = r2.files
        self.assertEqual(f3.path, 'baz.txt')
        self.assertEqual(f3.details, 'test file3')
        self.assertIsInstance(f4, modelcif.associated.CIFFile)
        self.assertFalse(f4.binary)
        self.assertIsNone(f4.data)
        self.assertIsInstance(f5, modelcif.associated.CIFFile)
        self.assertTrue(f5.binary)
        self.assertEqual(f5.data.__class__, modelcif.data.Data)

    def test_template_poly_handler(self):
        """Test _TemplatePolyHandler"""
        cif = """
loop_
_chem_comp.id
_chem_comp.type
_chem_comp.name
_chem_comp.formula
MYTYPE 'D-PEPTIDE LINKING' 'MY CUSTOM COMPONENT' 'C6 H12'
MYTYP2 'D-PEPTIDE LINKING' 'MY CUSTOM COMPONENT2' 'C6 H12'
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
_ma_template_details.template_auth_asym_id
1 1 'reference database' polymer 1 1 A A . 1 A
2 2 'reference database' polymer 1 1 A A . 1 A
3 3 'reference database' polymer 1 1 A A . 1 A
#
loop_
_ma_template_poly.template_id
_ma_template_poly.seq_one_letter_code
_ma_template_poly.seq_one_letter_code_can
1 A(MYTYPE)V AVV
2 A(MYTYP2)V .
3 . .
4 CCC CCC
"""
        s, = modelcif.reader.read(StringIO(cif))
        # template_id=4 in template_poly should be ignored
        t1, t2, t3 = s.templates
        s1, s2, s3 = t1.entity.sequence
        self.assertEqual(s1.id, 'ALA')
        self.assertEqual(s1.code, 'A')
        # Both one-letter and one-letter-canonical were provided
        self.assertEqual(s2.id, 'MYTYPE')
        self.assertEqual(s2.code, 'MYTYPE')
        self.assertEqual(s2.code_canonical, 'V')

        # Only one-letter was provided
        s1, s2, s3 = t2.entity.sequence
        self.assertEqual(s2.id, 'MYTYP2')
        self.assertEqual(s2.code, 'MYTYP2')
        self.assertIsNone(s2.code_canonical)

        # No sequence provided
        self.assertEqual(len(t3.entity.sequence), 0)

    def test_template_non_poly_handler(self):
        """Test _TemplateNonPolyHandler"""
        cif = """
loop_
_chem_comp.id
_chem_comp.type
HEM non-polymer
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
_ma_template_details.template_auth_asym_id
1 1 'reference database' polymer 1 1 A A . 1 A
#
loop_
_ma_template_non_poly.template_id
_ma_template_non_poly.comp_id
_ma_template_non_poly.details
1 HEM Heme
"""
        s, = modelcif.reader.read(StringIO(cif))
        t, = s.templates
        s1, = t.entity.sequence
        self.assertEqual(s1.id, 'HEM')
        self.assertEqual(s1.type, 'non-polymer')
        self.assertIsInstance(s1, ihm.NonPolymerChemComp)

    def test_chem_comp_handler(self):
        """Test ChemCompHandler and ChemCompDescriptorHandler"""
        cif = """
loop_
_chem_comp.id
_chem_comp.type
_chem_comp.name
_chem_comp.formula
_chem_comp.ma_provenance
MET 'L-peptide linking' . . .
CYS 'D-peptide linking' CYSTEINE . ?
ALA 'L-peptide linking' ALANINE . 'CCD Core'
MATYPE 'L-PEPTIDE LINKING' 'MODELARCHIVE COMPONENT' . 'CCD MA'
MYTYPE 'L-PEPTIDE LINKING' 'MY CUSTOM COMPONENT' . 'CCD local'
#
loop_
_ma_chem_comp_descriptor.ordinal_id
_ma_chem_comp_descriptor.chem_comp_id
_ma_chem_comp_descriptor.chem_comp_name
_ma_chem_comp_descriptor.type
_ma_chem_comp_descriptor.value
_ma_chem_comp_descriptor.details
_ma_chem_comp_descriptor.software_id
1 MYTYPE 'ignored' 'InChI Key' XDAOLTSRNUSPPH-XMMPIXPASA-N foo 1
2 MYTYPE ? 'IUPAC Name' foobar . .
#
loop_
_entity_poly_seq.entity_id
_entity_poly_seq.num
_entity_poly_seq.mon_id
_entity_poly_seq.hetero
1 1 MET .
1 2 CYS .
1 3 ALA .
1 4 MATYPE .
1 5 MYTYPE .
"""
        s, = modelcif.reader.read(StringIO(cif))
        e1, = s.entities
        s = e1.sequence
        self.assertEqual(len(s), 5)
        self.assertEqual(s[2].ccd, 'core')
        self.assertEqual(s[3].ccd, 'ma')
        self.assertEqual(s[4].ccd, 'local')
        d1, d2 = s[4].descriptors
        self.assertIsInstance(d1, modelcif.descriptor.InChIKey)
        self.assertEqual(d1.value, 'XDAOLTSRNUSPPH-XMMPIXPASA-N')
        self.assertEqual(d1.details, 'foo')
        self.assertEqual(d1.software._id, '1')
        self.assertIsInstance(d2, modelcif.descriptor.IUPACName)
        self.assertEqual(d2.value, 'foobar')
        self.assertIsNone(d2.details)
        self.assertIsNone(d2.software)

    def test_add_to_system(self):
        """Test adding new mmCIF input to existing System"""
        s = modelcif.System()
        e = modelcif.Entity('AHC')
        e._id = '42'
        s.entities.append(e)
        fh = StringIO("""
loop_
_struct_asym.id
_struct_asym.entity_id
_struct_asym.details
A 42 foo
B 99 bar
""")
        s2, = modelcif.reader.read(fh, add_to_system=s)
        self.assertIs(s2, s)
        self.assertEqual(len(s.asym_units), 2)
        # asym A should point to existing entity
        self.assertEqual(s.asym_units[0].id, 'A')
        self.assertIs(s.asym_units[0].entity, e)

    def test_audit_revision_handler(self):
        """Test AuditRevisionHistoryHandler"""
        # We leverage the support in python-ihm, so only a basic test here
        cif = """
loop_
_pdbx_audit_revision_history.ordinal
_pdbx_audit_revision_history.data_content_type
_pdbx_audit_revision_history.major_revision
_pdbx_audit_revision_history.minor_revision
_pdbx_audit_revision_history.revision_date
40 'Structure model' 1 0 ?
41 'Structure model' 1 0 .
42 'Structure model' 2 0 1979-05-03
"""
        s, = modelcif.reader.read(StringIO(cif))
        r1, r2, r3 = s.revisions
        self.assertEqual(r3.major, 2)
        self.assertEqual(r3.minor, 0)
        self.assertEqual(r3.date, datetime.date(1979, 5, 3))

    def test_data_usage_handler(self):
        """Test DataUsageHandler"""
        # We leverage the support in python-ihm, so only a basic test here
        cif = """
loop_
_pdbx_data_usage.id
_pdbx_data_usage.type
_pdbx_data_usage.details
_pdbx_data_usage.url
_pdbx_data_usage.name
1 license 'some license' someurl somename
"""
        s, = modelcif.reader.read(StringIO(cif))
        d1, = s.data_usage
        self.assertEqual(d1.details, "some license")


if __name__ == '__main__':
    unittest.main()
