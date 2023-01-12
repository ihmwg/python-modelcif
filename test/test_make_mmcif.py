import utils
import os
import sys
import unittest
import subprocess

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.reader


MAKE_MMCIF = os.path.join(TOPDIR, 'util', 'make-mmcif.py')


class Tests(unittest.TestCase):
    @unittest.skipIf(sys.version_info[0] < 3, "make-mmcif.py needs Python 3")
    def test_bad_usage(self):
        """Bad usage of make-mmcif utility script"""
        ret = subprocess.call([sys.executable, MAKE_MMCIF])
        self.assertEqual(ret, 1)

    @unittest.skipIf(sys.version_info[0] < 3, "make-mmcif.py needs Python 3")
    def test_mini(self):
        """Check that make-mmcif works given only basic atom info"""
        incif = utils.get_input_file_name(TOPDIR, 'mini.cif')
        subprocess.check_call([sys.executable, MAKE_MMCIF, incif])
        with open('output.cif') as fh:
            s, = modelcif.reader.read(fh)
        self.assertEqual(s.title, 'Auto-generated system')
        self.assertEqual(len(s.protocols), 1)
        p = s.protocols[0]
        self.assertEqual(len(p.steps), 1)
        step = p.steps[0]
        self.assertIsInstance(step, modelcif.protocol.ModelingStep)
        self.assertEqual(step.name, 'modeling')
        self.assertEqual(step.input_data, [])
        self.assertEqual(step.output_data, [])
        os.unlink('output.cif')


if __name__ == '__main__':
    unittest.main()
