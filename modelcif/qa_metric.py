"""Classes to annotate models with quality scores.

   To use, first declare a class for the desired score by deriving
   from both a subclass of :class:`MetricMode` (which defines the part
   of the system the metric applies to) and a subclass of :class:`MetricType`
   (which describes the meaning of the score value). Set the ``software``
   attribute to point to the software used to calculate the metric
   (as a :class:`modelcif.SoftwareGroup` or :class:`modelcif.Software` object).
   For example to declare a global distance score::

       class MyScore(modelcif.qa_metric.Global, modelcif.qa_metric.Distance):
           "My distance-based quality score"
           software = modelcif.Software(...)

   The name and description of the score in the mmCIF file will be taken from
   the name and docstring of the Python class, unless the
   :attr:`MetricMode.name` or :attr:`MetricMode.description` attributes are
   overridden in the subclass.

   QA metric objects should be added to
   :attr:`modelcif.model.Model.qa_metrics`.
"""


class MetricMode(object):
    """Base class for the mode of a quality metric.
       Use a derived class such as :class:`Global`, :class:`Local`,
       or :class:`LocalPairwise` for declaring a new score.
    """
    name = property(lambda x: type(x).__name__,
                    doc="Short name of this score. By default it is just the "
                        "class name, but this can be overridden in subclasses "
                        "(for example to create names containing spaces).")

    description = property(lambda x: x.__doc__.split("\n")[0],
                           doc="Longer text description of this score. By "
                               "default it is the first line of the "
                               "docstring.")


class Global(MetricMode):
    """A score that is calculated per-model.

       :param float value: The score value (see :class:`MetricType`).
    """

    mode = "global"

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "<%s(value=%r)>" % (type(self).__name__, self.value)


class Local(MetricMode):
    """A score that is calculated on a single residue.

       :param residue: The residue that is scored.
       :type residue: :class:`modelcif.Residue`
       :param float value: The score value (see :class:`MetricType`).
    """

    mode = "local"

    def __init__(self, residue, value):
        self.residue = residue
        self.value = value

    def __repr__(self):
        return "<%s(residue=%r, value=%r)>" % (type(self).__name__,
                                               self.residue, self.value)


class LocalPairwise(MetricMode):
    """A score that is calculated between two residues.

       :param residue1: The first residue that is scored.
       :type residue1: :class:`modelcif.Residue`
       :param residue2: The second residue that is scored.
       :type residue2: :class:`modelcif.Residue`
       :param float value: The score value (see :class:`MetricType`).
    """

    mode = "local-pairwise"

    def __init__(self, residue1, residue2, value):
        self.residue1 = residue1
        self.residue2 = residue2
        self.value = value

    def __repr__(self):
        return ("<%s(residue1=%r, residue2=%r, value=%r)>"
                % (type(self).__name__, self.residue1, self.residue2,
                   self.value))


class MetricType(object):
    """Base class for the type of a quality metric.
       Generally a derived class such as :class:`ZScore` or :class:`Distance`
       is used to declare a new score, but a custom type can also be declared
       by deriving from this class and providing a docstring to describe
       the metric type::

           class MPQSMetricType(modelcif.qa_metric.MetricType):
                "composite score, values >1.1 are reliable"
    """

    type = "other"

    def _get_other_details(self):
        # Find most derived class of MetricType before we pulled in MetricMode
        # and use the first line of its docstring as other_details
        if self.type == MetricType.type:
            for base in type(self).mro():
                if (issubclass(base, MetricType)
                        and base is not MetricType
                        and not issubclass(base, MetricMode)):
                    return base.__doc__.split('\n')[0]

    other_details = property(
        _get_other_details,
        doc="More information about this metric type. By default it is the "
            "first line of the MetricType subclass docstring.")


class ZScore(MetricType):
    """Score that is the number of standard deviations from optimal/best.
       See :class:`MetricType` for more information."""
    type = "zscore"
    other_details = None


class Energy(MetricType):
    """Energy score (the lower the energy, the better the quality).
       See :class:`MetricType` for more information."""
    type = "energy"
    other_details = None


class Distance(MetricType):
    """Distance score (the lower the distance, the better the quality).
       See :class:`MetricType` for more information."""
    type = "distance"
    other_details = None


class NormalizedScore(MetricType):
    """Normalized score ranging from 0 to 1.
       See :class:`MetricType` for more information."""
    type = "normalized score"
    other_details = None


class PAE(MetricType):
    """Score that is a predicted aligned error.
       See :class:`MetricType` for more information."""
    type = "PAE"
    other_details = None


class ContactProbability(MetricType):
    """Score that is a contact probability of a pairwise interaction.
       See :class:`MetricType` for more information."""
    type = "contact probability"
    other_details = None


class PLDDT(MetricType):
    """Predicted lDDT-CA score in [0,100] (higher score, means better
       accuracy). See :class:`MetricType` for more information."""
    type = "pLDDT"
    other_details = None


class PTM(MetricType):
    """Predicted TM-score in [0,1] (higher value means higher confidence).
    See :class:`MetricType` for more information."""
    type = "pTM"
    other_details = None


class IpTM(MetricType):
    """Protein-protein interface score, based on TM-score in [0,1].
    See :class:`MetricType` for more information."""
    type = "ipTM"
    other_details = None
