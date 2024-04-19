"""Classes for linking back to a sequence or structure database."""

import warnings
import ihm.reference
from ihm.reference import Alignment, SeqDif  # noqa: F401


class TargetReference(ihm.reference.Sequence):
    """Point to the sequence of a target :class:`modelcif.Entity` in a sequence
       database. Typically a subclass such as :class:`UniProt` is used,
       although to use a custom database, make a new subclass and provide
       a docstring to describe the database, e.g.::

           class CustomRef(TargetReference):
               "my custom database"

       Compare with :class:`modelcif.ReferenceDatabase`, which describes
       multiple sequences used in template searches or alignment
       construction; this class relates to just the modeled sequence itself.

       See also :attr:`alignments` to describe the correspondence between
       the database and entity sequences.

       :param str code: The name of the sequence in the database.
       :param str accession: The database accession.
       :param int align_begin: Beginning index of the sequence in the database.
              Deprecated; use :attr:`alignments` instead.
       :param int align_end: Ending index of the sequence in the database.
              Deprecated; use :attr:`alignments` instead.
       :param str isoform: Sequence isoform, if applicable.
       :param str ncbi_taxonomy_id: Taxonomy identifier provided by NCBI.
       :param str organism_scientific: Scientific name of the organism.
       :param sequence_version_date: Versioning date, e.g. for UniProtKB
                                     sequences this is usually the date of last
                                     modification from the DT line of an entry.
       :type sequence_version_date: :class:`datetime.date` or
                                    :class:`datetime.datetime`
       :param str sequence_crc64: The CRC64 sum of the original database
                                  sequence.
       :param str sequence: The complete database sequence, as a string of
              one-letter codes. If omitted, will default to the canonical
              sequence of the associated :class:`Entity`.
       :param str details: Longer text describing the sequence.
    """

    name = 'Other'

    def __init__(self, code, accession, align_begin=None, align_end=None,
                 isoform=None, ncbi_taxonomy_id=None,
                 organism_scientific=None, sequence_version_date=None,
                 sequence_crc64=None, sequence=None, details=None):
        super(TargetReference, self).__init__(
            db_name=self.name, db_code=code, accession=accession,
            sequence=sequence, details=details)
        self.align_begin, self.align_end = align_begin, align_end
        self.isoform = isoform
        self.ncbi_taxonomy_id = ncbi_taxonomy_id
        self.organism_scientific = organism_scientific
        self.sequence_version_date = sequence_version_date
        self.sequence_crc64 = sequence_crc64
        if align_begin or align_end:
            warnings.warn(
                "align_begin and align_end are deprecated, and will be "
                "removed in a future python-modelcif release. Specify the "
                "database sequence and provide one or more "
                "modelcif.reference.Alignment objects intead.", stacklevel=2)
        if sequence is None:
            warnings.warn(
                "No sequence provided. The canonical sequence of the Entity "
                "will be used instead.", stacklevel=2)

    code = property(lambda self: self.db_code)

    def _get_other_details(self):
        if (type(self) is not TargetReference
                and self.name == TargetReference.name):
            return self.__doc__.split('\n')[0]

    other_details = property(
        _get_other_details,
        doc="More information about a custom reference type. "
            "By default it is the first line of the docstring.")


class UniProt(TargetReference):
    """Point to the sequence of an :class:`modelcif.Entity` in UniProt.

       These objects are typically passed to the :class:`modelcif.Entity`
       constructor for target sequences (for templates, see
       :class:`TemplateReference`).

       See :class:`TargetReference` for a description of the parameters.
    """
    name = 'UNP'
    other_details = None


class TemplateReference(object):
    """Point to the structure of a :class:`modelcif.Template` in a structure
       database.

       These objects are typically passed to the :class:`modelcif.Template`
       constructor for template sequences (for target sequences, see
       :class:`TargetReference`).

       Typically a subclass such as :class:`PDB` is used,
       although to use a custom database, make a new subclass and provide
       a docstring to describe the database, e.g.::

           class CustomRef(TemplateReference):
               "my custom database"

       :param str accession: The database accession.
       :param db_version_date: Versioning date, e.g. for PDB entries this is
                               usually the value of
                               ``_pdbx_audit_revision_history.revision_date``.
       :type db_version_date: :class:`datetime.date` or
                              :class:`datetime.datetime`
    """
    name = 'Other'

    def __init__(self, accession, db_version_date=None):
        self.accession = accession
        self.db_version_date = db_version_date

    def _get_other_details(self):
        if (type(self) is not TemplateReference
                and self.name == TemplateReference.name):
            return self.__doc__.split('\n')[0]

    other_details = property(
        _get_other_details,
        doc="More information about a custom reference type. "
            "By default it is the first line of the docstring.")


class PDB(TemplateReference):
    """Point to the structure of a :class:`modelcif.Template` in PDB.

       These objects are typically passed to the :class:`modelcif.Template`
       constructor.

       See :class:`TemplateReference` for a description of the parameters.
    """
    name = 'PDB'
    other_details = None


class AlphaFoldDB(TemplateReference):
    """Point to the structure of a :class:`modelcif.Template` in AlphaFold DB.

       These objects are typically passed to the :class:`modelcif.Template`
       constructor.

       See :class:`TemplateReference` for a description of the parameters.
    """
    name = 'AlphaFoldDB'
    other_details = None


class PubChem(TemplateReference):
    """Point to the structure of a :class:`modelcif.Template` in PubChem.

       These objects are typically passed to the :class:`modelcif.Template`
       constructor.

       See :class:`TemplateReference` for a description of the parameters. Use
       the PubChem CID as the accession code.
    """
    name = 'PubChem'
    other_details = None
