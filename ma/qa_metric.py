"""Classes to annotate models with quality scores.

   To use, first declare a class for the desired score by deriving
   from both a subclass of :class:`MetricMode` (which defines the part
   of the system the metric applies to) and a subclass of :class:`MetricType`
   (which describes the meaning of the score value). For example to declare
   a global distance score::

       class MyScore(ma.qa_metric.Global, ma.qa_metric.Distance):
           name = "My score"
           description = "My distance-based quality score"
           software = ma.Software(...)
"""


class MetricMode(object):
    """Base class for the mode of a quality metric.
       Use a derived class such as :class:`Global` for declaring a new score.
    """
    pass


class Global(MetricMode):
    """A score that is calculated per-model.

       :param float value: The score value (see :class:`MetricType`).
    """

    mode = "global"

    def __init__(self, value):
        self.value = value


class MetricType(object):
    """Base class for the type of a quality metric.
       Generally a derived class such as :class:`ZScore` or :class:`Distance`
       is used to declare a new score, but a custom type can also be declared
       by deriving from this class::

           class MPQSMetricType(ma.qa_metric.MetricType):
                other_details = "composite score, values >1.1 are reliable"
    """

    type = "other"


class ZScore(MetricType):
    """Score that is the number of standard deviations from optimal/best"""
    type = "zscore"
    other_details = None


class Distance(MetricType):
    """Distance score (the lower the distance, the better the quality)"""
    type = "distance"
    other_details = None


class NormalizedScore(MetricType):
    """Normalized score ranging from 0 to 1"""
    type = "normalized_score"
    other_details = None