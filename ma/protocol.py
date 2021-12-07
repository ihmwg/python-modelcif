"""Classes for handling modeling protocols.
"""


class Step(object):
    """A single step in a :class:`Protocol`."""
    method_type = "other"

    def __init__(self, input_data, output_data, name=None, details=None,
                 software=None):
        self.input_data, self.output_data = input_data, output_data
        self.name, self.details, self.software = name, details, software


class TemplateSearchStep(Step):
    method_type = "template search"


class ModelingStep(Step):
    method_type = "modeling"


class ModelSelectionStep(Step):
    method_type = "model selection"


class Protocol(object):
    """A modeling protocol.
       Each protocol consists of a number of protocol steps."""
    def __init__(self):
        #: All modeling steps (:class:`Step` objects)
        self.steps = []
