import utils
import os
import unittest
import sys
import shutil
import subprocess
try:
    import msgpack
except ImportError:
    msgpack = None

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)

import modelcif.reader


def get_example_dir():
    return os.path.join(TOPDIR, "examples")


def get_example_path(fname):
    return os.path.join(get_example_dir(), fname)


class Tests(unittest.TestCase):

    @unittest.skipIf('APPVEYOR' in os.environ,
                     "AppVeyor environments have old SSL certs")
    @unittest.skipIf('GITHUB_ACTIONS' in os.environ,
                     "Example is slow and fails when ModBase is down")
    def test_validate_modbase_example(self):
        """Test validate_modbase example"""
        subprocess.check_call([sys.executable,
                               get_example_path("validate_modbase.py")])

    @unittest.skipIf(sys.version_info[0] < 3,
                     "validate_mmcif.py needs Python 3")
    @unittest.skipIf('APPVEYOR' in os.environ,
                     "AppVeyor environments have old SSL certs")
    @unittest.skipIf('GITHUB_ACTIONS' in os.environ,
                     "Example is slow and fails when ModBase is down")
    def test_validate_mmcif_example(self):
        """Test validate_mmcif example"""
        with utils.temporary_directory() as tmpdir:
            subprocess.check_call([sys.executable,
                                   get_example_path("validate_mmcif.py"),
                                   get_example_path("input/ligands.cif")],
                                  cwd=tmpdir)

    def test_mkmodbase_example(self):
        """Test mkmodbase example"""
        with utils.temporary_directory() as tmpdir:
            subprocess.check_call([sys.executable,
                                   get_example_path("mkmodbase.py")],
                                  cwd=tmpdir)

            # Make sure that a complete output file was produced and that we
            # can read it
            with open(os.path.join(tmpdir, 'output.cif')) as fh:
                contents = fh.readlines()
            self.assertEqual(len(contents), 417)
            with open(os.path.join(tmpdir, 'output.cif')) as fh:
                s, = modelcif.reader.read(fh)

    def test_ligands_example(self):
        """Test ligands example"""
        with utils.temporary_directory() as tmpdir:
            subprocess.check_call([sys.executable,
                                   get_example_path("ligands.py")],
                                  cwd=tmpdir)

            # Make sure that a complete output file was produced and that we
            # can read it
            with open(os.path.join(tmpdir, 'output.cif')) as fh:
                contents = fh.readlines()
            self.assertEqual(len(contents), 323)
            with open(os.path.join(tmpdir, 'output.cif')) as fh:
                s, = modelcif.reader.read(fh)

    @unittest.skipIf(msgpack is None, "BinaryCIF needs msgpack")
    def test_convert_bcif_example(self):
        """Test convert_bcif example"""
        with utils.temporary_directory() as tmpdir:
            from_input = get_example_path("input")
            to_input = os.path.join(tmpdir, 'input')
            os.mkdir(to_input)
            shutil.copy(os.path.join(from_input, "ligands.cif"), to_input)
            subprocess.check_call([sys.executable,
                                   get_example_path("convert_bcif.py")],
                                  cwd=tmpdir)

            # Make sure that a complete output file was produced and that we
            # can read it
            with open(os.path.join(tmpdir, 'ligands.bcif'), 'rb') as fh:
                s, = modelcif.reader.read(fh, format='BCIF')


if __name__ == '__main__':
    unittest.main()
