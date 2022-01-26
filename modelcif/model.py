import sys
import ihm.representation
from ihm.model import Atom, ModelGroup  # noqa: F401
import modelcif.data

# Provide ma-specific docs for Atom
if sys.version_info[0] >= 3:
    Atom.__doc__ = """Coordinates of part of the model represented by an atom.

See :meth:`Model.get_atoms` for more details.

:param asym_unit: The asymmetric unit that this atom represents
:type asym_unit: :class:`modelcif.AsymUnit`
:param int seq_id: The residue index represented by this atom
       (can be None for HETATM sites)
:param str atom_id: The name of the atom in the residue
:param str type_symbol: Element name
:param float x: x coordinate of the atom
:param float y: y coordinate of the atom
:param float z: z coordinate of the atom
:param bool het: True for HETATM sites, False (default) for ATOM
:param float biso: Temperature factor or equivalent (if applicable)
:param float occupancy: Fraction of the atom type present
       (if applicable)
"""

# Provide ma-specific docs for ModelGroup
if sys.version_info[0] >= 3:
    ModelGroup.__doc__ = """A set of related models. See :class:`Model`.
It is implemented as a simple list of the models.

These objects are typically stored directly in the system; see
:attr:`modelcif.System.model_groups`.

:param elements: Initial set of models in the group.
:param str name: Descriptive name for the group.
"""


class Model(modelcif.data.Data):
    """Base class for coordinates of a single structure.
       Use a subclass such as :class:`HomologyModel` or
       :class:`AbInitioModel`, or represent a custom model type by
       creating a new subclass and providing a docstring to describe it, e.g.::

           class CustomModel(Model):
               "custom model type"

       :param assembly: The :class:`modelcif.AsymUnit` objects that make up
              this model.
       :type assembly: :class:`modelcif.Assembly`
       :param str name: Short name for this model.
    """
    data_content_type = 'model coordinates'
    model_type = "Other"

    def __init__(self, assembly, name=None):
        modelcif.data.Data.__init__(self, name)
        self.assembly = assembly
        # Assume everything is atomic for ModelCIF models
        self.representation = ihm.representation.Representation(
            [ihm.representation.AtomicSegment(seg, rigid=False)
             for seg in assembly])
        self._atoms = []
        #: Quality scores for the model or part of it (a simple list of
        #: metric objects; see :mod:`modelcif.qa_metric`)
        self.qa_metrics = []

    def _get_other_details(self):
        if (type(self) is not Model
                and self.model_type == Model.model_type):
            return self.__doc__.split('\n')[0]

    other_details = property(
        _get_other_details,
        doc="More information about a custom model type. "
            "By default it is the first line of the docstring.")

    def get_atoms(self):
        """Yield :class:`Atom` objects that represent this model.

           The default implementation simply iterates over an internal
           list of atoms, but this is not very memory-efficient, particularly
           if the atoms are already stored somewhere else, e.g. in the
           software's own data structures. It is recommended to subclass
           and provide a more efficient implementation. For example,
           `the modbase_pdb_to_cif script <https://github.com/salilab/modbase_utils/blob/model_archive/modbase_pdb_to_cif.py>`_
           uses a custom ``MyModel`` subclass that creates Atom objects on
           the fly from PDB ATOM or HETATM lines.
        """  # noqa: E501
        for a in self._atoms:
            yield a

    def add_atom(self, atom):
        self._atoms.append(atom)


class HomologyModel(Model):
    """Coordinates of a single structure generated using homology
       or comparative modeling.

       See :class:`Model` for a description of the parameters.
    """
    model_type = "Homology model"
    other_details = None


class AbInitioModel(Model):
    """Coordinates of a single structure generated using ab initio modeling.

       See :class:`Model` for a description of the parameters.
    """
    model_type = "Ab initio model"
    other_details = None
