import ma.data


class AlignmentMode(ma.data.Data):
    data_content_type = 'target-template alignment'

    def __init__(self, name, software=None):
        ma.data.Data.__init__(self, name)
        self.software = software
        self.segments = []


class Global(AlignmentMode):
    mode = "global"


class AlignmentType(object):
    type = "other"


class Pairwise(AlignmentType):
    type = "target-template pairwise alignment"
    other_details = None


class Segment(object):
    def __init__(self, gapped_sequences, score=None):
        self.gapped_sequences = gapped_sequences
        self.score = score


class Score(object):
    type = "other"

    def __init__(self, value):
        self.value = value


class BLASTEValue(Score):
    type = "BLAST e-value"
    other_details = None
