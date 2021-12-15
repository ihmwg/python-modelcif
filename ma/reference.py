"""Classes for linking back to a sequence database."""

class TargetReference(object):
    """Point to the sequence of a target :class:`ma.Entity` in a sequence
       database. Typically a subclass such as :class:`UniProt` is used,
       although this can be subclassed to point to a custom database.

       :param str code: The name of the sequence in the database.
       :param str accession: The database accession.
       :param int align_begin: Beginning index of the sequence in the database.
              If omitted, it will be assumed that the Entity corresponds to
              the full database sequence.
       :param int align_end: Ending index of the sequence in the database.
              If omitted, it will be assumed that the Entity corresponds to
              the full database sequence.
       :param str isoform: Sequence isoform, if applicable.
       :param str ncbi_taxonomy_id: Taxonomy identifier provided by NCBI.
       :param str organism_scientific: Scientific name of the organism.
    """

    name = 'Other'

    def __init__(self, code, accession, align_begin=None, align_end=None,
                 isoform=None, ncbi_taxonomy_id=None,
                 organism_scientific=None):
        self.code, self.accession = code, accession
        self.align_begin, self.align_end = align_begin, align_end
        self.isoform = isoform
        self.ncbi_taxonomy_id = ncbi_taxonomy_id
        self.organism_scientific = organism_scientific


class UniProt(TargetReference):
    """Point to the sequence of an :class:`ma.Entity` in UniProt.

       These objects are typically passed to the :class:`ma.Entity`
       constructor for target sequences.

       See :class:`TargetReference` for a description of the parameters.
    """
    name = 'UNP'
    other_details = None


class TemplateReference(object):
    """Point to the structure of a :class:`ma.Template` in a structure
       database. Typically a subclass such as :class:`PDB` is used,
       although this can be subclassed to point to a custom database.

       :param str accession: The database accession.
    """
    name = 'Other'

    def __init__(self, accession):
        self.accession = accession


class PDB(TemplateReference):
    """Point to the structure of a :class:`ma.Template` in PDB.

       These objects are typically passed to the :class:`ma.Template`
       constructor.

       See :class:`TemplateReference` for a description of the parameters.
    """
    name = 'PDB'
    other_details = None
