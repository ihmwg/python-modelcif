"""Classes for handling modeling protocols.
"""


class Step(object):
    """A single step in a :class:`Protocol`.

       This class describes a generic step in a modeling protocol. In most
       cases, a more specific subclass should be used, such as
       :class:`TemplateSearchStep`, :class:`ModelingStep`, or
       :class:`ModelSelectionStep`.

       :param input_data: Any objects that this step takes as input.
              Any individual :class:`modelcif.data.Data` object (such as
              a template structure, target sequence, alignment, or model
              coordinates) can be given here, or a group of such objects (as a
              :class:`modelcif.data.DataGroup` object) can be passed.
       :type input_data: :class:`modelcif.data.DataGroup`
             or :class:`modelcif.data.Data`
       :param output_data: Any objects that this step creates as output,
              similarly to ``input_data``.
       :type output_data: :class:`modelcif.data.DataGroup`
             or :class:`modelcif.data.Data`
       :param str name: A short name for this step.
       :param str details: Longer description of this step.
       :param software: The software that was employed in this modeling step.
       :type software: :class:`modelcif.Software`
             or :class:`modelcif.SoftwareGroup`
    """
    method_type = "other"

    def __init__(self, input_data, output_data, name=None, details=None,
                 software=None):
        self.input_data, self.output_data = input_data, output_data
        self.name, self.details, self.software = name, details, software


class TemplateSearchStep(Step):
    """A modeling protocol step that searches for templates.
       See :class:`Step` for more details."""
    method_type = "template search"


class ModelingStep(Step):
    """A modeling protocol step that generates model coordinates.
       See :class:`Step` for more details."""
    method_type = "modeling"


class ModelSelectionStep(Step):
    """A modeling protocol step that filters candidates to select models.
       See :class:`Step` for more details."""
    method_type = "model selection"


class Protocol(object):
    """A modeling protocol.
       Each protocol consists of a number of protocol steps."""
    def __init__(self):
        #: All modeling steps (:class:`Step` objects)
        self.steps = []
