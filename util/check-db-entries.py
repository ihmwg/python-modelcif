import unittest
import modelcif.reader
import modelcif.dumper
import urllib.request
import os


class Tests(unittest.TestCase):
    def _read_cif(self, url):
        with urllib.request.urlopen(url) as fh:
            s, = modelcif.reader.read(fh)
        return s

    def _write_cif(self, s, check=True):
        with open('test.cif', 'w') as fh:
            modelcif.dumper.write(fh, [s], check=check)
        os.unlink('test.cif')

    def test_modbase(self):
        """Test ModBase structure without errors"""
        model_id = '3c79945a94ec00cac8a03104e853ca50'
        modbase_top = 'https://salilab.org/modbase/retrieve/modbase'
        url = '%s/?modelID=%s&format=mmcif' % (modbase_top, model_id)
        s = self._read_cif(url)
        self._write_cif(s)

    def test_swiss_model(self):
        """Test SWISS-MODEL structure without errors"""
        model_id = '680335e5cca47f7d2b00afc1'
        url = 'https://swissmodel.expasy.org/repository/%s.cif' % model_id
        s = self._read_cif(url)
        self._write_cif(s)

    def test_alpha_fold(self):
        """Test AlphaFold structure without errors"""
        model_id = 'AF-B4GKE9-F1-model_v4'
        url = 'https://alphafold.ebi.ac.uk/files/%s.cif' % model_id
        s = self._read_cif(url)
        self._write_cif(s)


if __name__ == '__main__':
    unittest.main()
