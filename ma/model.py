import ihm.representation
from ihm.model import Atom, ModelGroup  # noqa: F401
import ma.data


class Model(ma.data.Data):
    """Base class for coordinates of a single structure.
       Use a subclass such as :class:`HomologyModel` or
       :class:`AbInitioModel`, or represent a custom model type by
       creating a new subclass and providing a docstring to describe it, e.g.::

           class CustomModel(Model):
               "custom model type"

       :param assembly: The :class:`AsymUnit` objects that make up this model.
       :type assembly: :class:`Assembly`
       :param str name: Short name for this model.
    """
    data_content_type = 'model coordinates'
    model_type = "Other"

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

    def _get_other_details(self):
        if (type(self) is not Model
                and self.model_type == Model.model_type):
            return self.__doc__.split('\n')[0]

    other_details = property(
        _get_other_details,
        doc="More information about a custom model type. "
            "By default it is the first line of the docstring.")

    def get_atoms(self):
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
