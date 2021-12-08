class MetricMode(object):
    software = None


class Global(MetricMode):
    mode = "global"

    def __init__(self, value):
        self.value = value


class MetricType(object):
    type = "other"


class ZScore(MetricType):
    type = "zscore"
    other_details = None


class Distance(MetricType):
    type = "distance"
    other_details = None


class NormalizedScore(MetricType):
    type = "normalized_score"
    other_details = None
