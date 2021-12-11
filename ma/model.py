import ihm.representation
from ihm.model import Atom, ModelGroup  # noqa: F401
import ma.data


class Model(ma.data.Data):
    data_content_type = 'model coordinates'

    def __init__(self, assembly, name=None):
        ma.data.Data.__init__(self, name)
        self.assembly = assembly
        # Assume everything is atomic for MA models
        self.representation = ihm.representation.Representation(
            [ihm.representation.AtomicSegment(seg, rigid=False)
             for seg in assembly])
        self._atoms = []
        #: QA metrics
        self.qa_metrics = []

    def get_atoms(self):
        for a in self._atoms:
            yield a

    def add_atom(self, atom):
        self._atoms.append(atom)
