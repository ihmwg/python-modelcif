import utils
import os
import unittest

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utils.set_search_paths(TOPDIR)
import modelcif.associated


class Tests(unittest.TestCase):
    def test_local_pairwise_qa_scores_file(self):
        """Test LocalPairwiseQAScoresFile class"""
        self.assertWarns(UserWarning,
                         modelcif.associated.LocalPairwiseQAScoresFile,
                         path='foo')


if __name__ == '__main__':
    unittest.main()
