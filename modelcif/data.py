"""Classes to track inputs/outputs of modeling protocols.

   See also :class:`modelcif.protocol.Step`.
"""


class Data(object):
    """Some part of the system that is input or output by part of
       the modeling protocol.

       Usually a subclass is passed to :class:`modelcif.protocol.Step`
       to describe the input or output:

        - A database of possible template sequences/structures to construct
          or search (:class:`modelcif.ReferenceDatabase`)
        - A template structure (:class:`modelcif.Template`)
        - The sequence of the target (:class:`modelcif.Entity`)
        - A target-template alignment (:mod:`modelcif.alignment`)
        - Target structure coordinates (:class:`modelcif.model.Model`)

       However, this class can also be used directly to describe other kinds
       of input/output data.

       :param str name: A short name for the data.
       :param str details: A longer description of the data.
    """
    data_content_type = 'other'
    data_other_details = None

    def __init__(self, name, details=None):
        self.name = name
        self.data_other_details = details


class DataGroup(list):
    """A number of :class:`Data` objects that are grouped together.

       This class can be used to group together multiple :class:`Data`
       objects if a given modeling protocol step consumes or generates
       multiple pieces of data. See :class:`modelcif.protocol.Step`. It behaves
       like a regular Python list.
    """
    pass
