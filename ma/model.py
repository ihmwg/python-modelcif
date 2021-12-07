import ihm.representation
from ihm.model import Atom, ModelGroup


class Model(object):
    def __init__(self, assembly, protocol, name=None):
        self.assembly, self.protocol = assembly, protocol
        # Assume everything is atomic for MA models
        self.representation = ihm.representation.Representation(
            [ihm.representation.AtomicSegment(seg, rigid=False)
             for seg in assembly])
        self.name = name
        self._atoms = []

    def get_atoms(self):
        for a in self._atoms:
            yield a

    def add_atom(self, atom):
        self._atoms.append(atom)
