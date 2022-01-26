import utils
import os
import unittest
import sys
import subprocess

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)

import modelcif.reader
import ihm


def get_example_dir():
    return os.path.join(TOPDIR, "examples")


def get_example_path(fname):
    return os.path.join(get_example_dir(), fname)


class Tests(unittest.TestCase):

    @unittest.skipIf('APPVEYOR' in os.environ,
                     "AppVeyor environments have old SSL certs")
    @unittest.skipIf('GITHUB_ACTIONS' in os.environ,
                     "Example is slow and fails when ModBase is down")
    def test_validator_example(self):
        """Test validator example"""
        subprocess.check_call([sys.executable,
                               get_example_path("validate_modbase.py")])

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
            if hasattr(ihm.System, 'structure_determination_methodology'):
                self.assertEqual(len(contents), 441)
            else:
                self.assertEqual(len(contents), 440)
            with open(os.path.join(tmpdir, 'output.cif')) as fh:
                s, = modelcif.reader.read(fh)


if __name__ == '__main__':
    unittest.main()
