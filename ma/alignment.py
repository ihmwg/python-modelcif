"""Classes to handle alignments between template structure(s)
   and target sequence(s).

   To create an alignment, first declare a class for the given kind of
   alignment by deriving from subclasses of :class:`AlignmentMode`
   (e.g. :class:`Global`) and :class:`AlignmentType` (e.g. :class:`Pairwise`).
   For example, a typical pairwise global alignment could be declared using::

       class Alignment(ma.alignment.Global, ma.alignment.Pairwise):
           pass
"""

import ma.data


class Identity(object):
    """Percent sequence identity between the template sequence and the target
       sequence being modeled.
       Use the correct subclass that corresponds to the denominator used
       when calculating the identity, for example
       :class:`ShorterSequenceIdentity`, or if the denominator is not covered
       here, subclass this class and set the ``other_details`` attribute to
       describe the denominator, e.g.::

           class CustomIdentity(Identity):
               other_details = "my custom sequence identity denominator"

       :param float value: The percent sequence identity value.
    """
    denominator = "Other"

    def __init__(self, value):
        self.value = value


class ShorterSequenceIdentity(Identity):
    """Sequence identity calculated using the length of the shorter sequence
       as the denominator.
       See :class:`Identity` for more information."""
    other_details = None
    denominator = "Length of the shorter sequence"


class AlignedPositionsIdentity(Identity):
    """Sequence identity calculated using the number of aligned positions
       (including gaps) as the denominator.
       See :class:`Identity` for more information."""
    other_details = None
    denominator = "Number of aligned positions (including gaps)"


class Pair(object):
    """A single pairwise alignment between a single target and template chain.
       See :class:`AlignmentMode`. An alignment consists of one of more of
       these pairs.

       :param template: The template segment that is aligned, i.e. the
              seq_id range for the template and the sequence (including gaps)
              of one-letter codes.
       :type template: :class:`TemplateSegment`
       :param target: The target segment that is aligned.
       :type target: :class:`ihm.AsymUnitSegment`
       :param identity: The sequence identity between target and template.
       :type identity: :class:`Identity`
       :param score: A measure of the quality of the alignment.
       :type score: :class:`Score`
    """
    def __init__(self, template, target, identity, score):
        self.template, self.target, self.score = template, target, score
        self.identity = identity


class AlignmentMode(ma.data.Data):
    """Base class for all alignments. Actual alignments should derive
       from both a subclass of this class (e.g. :class:`Global`) and a
       subclass of :class:`AlignmentType`.

       :param str name: A short description of this alignment.
       :param pairs: List of individual target-template alignments.
       :type pairs: List of :class:`Pair` objects
       :param software: The software that was used to build the alignment.
       :type software: :class:`ma.Software` or :class:`ma.SoftwareGroup`
    """
    data_content_type = 'target-template alignment'

    def __init__(self, name, pairs, software=None):
        ma.data.Data.__init__(self, name)
        self.pairs = pairs
        self.software = software


class Global(AlignmentMode):
    """Base class for global alignments. See :class:`AlignmentMode` for
       more details."""
    mode = "global"


class AlignmentType(object):
    """Base class for all alignment types. Actual alignments should derive
       from both a subclass of this class (e.g. :class:`Pairwise`) and a
       subclass of :class:`AlignmentMode`.
    """
    type = "other"


class Pairwise(AlignmentType):
    """An alignment between a single target and template.
       See :class:`AlignmentType` for more details."""
    type = "target-template pairwise alignment"
    other_details = None


class Score(object):
    """Base class for a quality score for a given target-template alignment.
       Usually a derived class such as :class:`BLASTEValue` is used, and
       passed to :class:`Pair` objects.

       :param float value: The actual score value.
    """
    type = "other"

    def __init__(self, value):
        self.value = value


class BLASTEValue(Score):
    """BLAST e-value for an alignment. See :class:`Score` for more details."""
    type = "BLAST e-value"
    other_details = None
