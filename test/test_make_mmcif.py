import utils
import os
import sys
import unittest
import subprocess

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.reader
import modelcif.util.make_mmcif  # Script should also be importable


MAKE_MMCIF = os.path.join(TOPDIR, 'modelcif', 'util', 'make_mmcif.py')


class Tests(unittest.TestCase):
    @unittest.skipIf(sys.version_info[0] < 3, "make_mmcif.py needs Python 3")
    def test_simple(self):
        """Simple test of make_mmcif utility script"""
        incif = utils.get_input_file_name(TOPDIR, 'struct_only.cif')
        subprocess.check_call([sys.executable, MAKE_MMCIF, incif])
        with open('output.cif') as fh:
            s, = modelcif.reader.read(fh)
        self.assertEqual(s.title,
                         'Architecture of Pol II(G) and molecular mechanism '
                         'of transcription regulation by Gdown1')
        os.unlink('output.cif')

    @unittest.skipIf(sys.version_info[0] < 3, "make_mmcif.py needs Python 3")
    def test_non_default_output(self):
        """Simple test of make_mmcif with non-default output name"""
        incif = utils.get_input_file_name(TOPDIR, 'struct_only.cif')
        subprocess.check_call([sys.executable, MAKE_MMCIF, incif,
                               'non-default-output.cif'])
        with open('non-default-output.cif') as fh:
            s, = modelcif.reader.read(fh)
        self.assertEqual(s.title,
                         'Architecture of Pol II(G) and molecular mechanism '
                         'of transcription regulation by Gdown1')
        os.unlink('non-default-output.cif')

    @unittest.skipIf(sys.version_info[0] < 3, "make_mmcif.py needs Python 3")
    def test_no_title(self):
        """Check that make_mmcif adds missing title"""
        incif = utils.get_input_file_name(TOPDIR, 'no_title.cif')
        subprocess.check_call([sys.executable, MAKE_MMCIF, incif])
        with open('output.cif') as fh:
            s, = modelcif.reader.read(fh)
        self.assertEqual(s.title, 'Auto-generated system')
        os.unlink('output.cif')

    @unittest.skipIf(sys.version_info[0] < 3, "make_mmcif.py needs Python 3")
    def test_bad_usage(self):
        """Bad usage of make_mmcif utility script"""
        ret = subprocess.call([sys.executable, MAKE_MMCIF])
        self.assertEqual(ret, 2)

    @unittest.skipIf(sys.version_info[0] < 3, "make_mmcif.py needs Python 3")
    def test_same_file(self):
        """Check that make_mmcif fails if input and output are the same"""
        incif = utils.get_input_file_name(TOPDIR, 'struct_only.cif')
        ret = subprocess.call([sys.executable, MAKE_MMCIF, incif, incif])
        self.assertEqual(ret, 1)

    @unittest.skipIf(sys.version_info[0] < 3, "make_mmcif.py needs Python 3")
    def test_not_modeled(self):
        """Check addition of not-modeled residue information"""
        incif = utils.get_input_file_name(TOPDIR, 'not_modeled.cif')
        subprocess.check_call([sys.executable, MAKE_MMCIF, incif])
        with open('output.cif') as fh:
            contents = fh.readlines()
        loop = contents.index("_pdbx_poly_seq_scheme.pdb_ins_code\n")
        scheme = "".join(contents[loop-11:loop+11])
        # Residues 5 and 6 in chain A, and 2 in chain B, are missing from
        # atom_site, so should now be missing from the scheme table.
        self.assertEqual(scheme, """#
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
A 1 1 VAL 2 2 VAL VAL A ?
A 1 2 GLY 3 3 GLY GLY A ?
A 1 3 GLN 4 4 GLN GLN A ?
A 1 4 GLN 5 5 GLN GLN A ?
A 1 5 TYR 5 ? ? ? A .
A 1 6 SER 6 ? ? ? A .
A 1 7 SER 8 8 SER SER A ?
B 2 1 ASP 3 3 ASP ASP B ?
B 2 2 GLU 2 ? ? ? B .
#
""")
        os.unlink('output.cif')


if __name__ == '__main__':
    unittest.main()
