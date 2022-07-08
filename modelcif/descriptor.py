"""Classes to describe the chemistry of custom chemical components.

   If a given :class:`ihm.ChemComp` is not defined in either the wwPDB
   chemical component dictionary (CCD) or the ModelArchive CCD, its
   chemistry can be described with one or more of these objects. They
   are passed as the ``descriptors`` argument when creating a new
   :class:`ihm.ChemComp`.
"""


class Descriptor(object):
    """Base class for all descriptors.
       This class is generally not used directly; instead, a subclass
       such as :class:`IUPACName` or :class:`InChI` is employed.

       :param str value: The actual name or identifier describing
              the chemistry.
       :param str details: Additional details about this descriptor.
       :param software: The software used to generate the descriptor, if any.
       :type software: :class:`modelcif.Software`
    """

    def __init__(self, value, details=None, software=None):
        self.value, self.details = value, details
        self.software = software

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__, repr(self.value))


class CanonicalSMILES(Descriptor):
    """Simplified Molecular-Input Line-Entry System (SMILES) computed from
       chemical structure devoid of isotopic and stereochemical information."""
    type = 'Canonical SMILES'


class IsomericSMILES(Descriptor):
    """Simplified Molecular-Input Line-Entry System (SMILES) computed from
       chemical structure containing isotopic and stereochemical information.

       SMILES written with isotopic and chiral specifications are collectively
       known as isomeric SMILES."""
    type = 'Isomeric SMILES'


class IUPACName(Descriptor):
    """Chemical name computed from chemical structure that uses International
       Union of Pure and Applied Chemistry (IUPAC) nomenclature standards."""
    type = 'IUPAC Name'


class InChI(Descriptor):
    """International Chemical Identifier (InChI) computed from chemical
       structure using the International Union of Pure and Applied Chemistry
       (IUPAC) standard."""
    type = 'InChI'


class InChIKey(Descriptor):
    """International Chemical Identifier hash (InChIKey) computed from
       chemical structure using the International Union of Pure and Applied
       Chemistry (IUPAC) standard."""
    type = 'InChI Key'


class PubChemCID(Descriptor):
    """PubChem Compound ID."""
    type = 'PubChem CID'
