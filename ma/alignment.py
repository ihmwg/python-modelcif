import ma.data


class Identity(object):
    """Percent sequence identity between the template sequence and the target
       sequence being modeled.
       Use the correct subclass that corresponds to the denominator used
       when calculating the identity, for example
       :class:`ShorterSequenceIdentity`, or if the denominator is not covered
       here, subclass this class and set the ``other_details`` attribute to
       describe the denominator.

       :param float value: The percent sequence identity value.
    """
    denominator = "Other"

    def __init__(self, value):
        self.value = value


class ShorterSequenceIdentity(Identity):
    """Sequence identity calculated using the length of the shorter sequence
       as the denominator."""
    other_details = None
    denominator = "Length of the shorter sequence"


class AlignedPositionsIdentity(Identity):
    """Sequence identity calculated using the numnber of aligned positions
       (including gaps) as the denominator."""
    other_details = None
    denominator = "Number of aligned positions (including gaps)"


class Pair(object):
    def __init__(self, template, target, identity, score):
        self.template, self.target, self.score = template, target, score
        self.identity = identity


class AlignmentMode(ma.data.Data):
    data_content_type = 'target-template alignment'

    def __init__(self, name, pairs, software=None):
        ma.data.Data.__init__(self, name)
        self.pairs = pairs
        self.software = software


class Global(AlignmentMode):
    mode = "global"


class AlignmentType(object):
    type = "other"


class Pairwise(AlignmentType):
    type = "target-template pairwise alignment"
    other_details = None


class Segment(object):
    def __init__(self, template, template_seq, target, target_seq, scores=[]):
        self.template, self.template_seq = template, template_seq
        self.target, self.target_seq = target, target_seq
        self.scores = scores


class Score(object):
    type = "other"

    def __init__(self, value):
        self.value = value


class BLASTEValue(Score):
    type = "BLAST e-value"
    other_details = None
