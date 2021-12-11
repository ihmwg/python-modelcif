import ma.data


class Pair(object):
    def __init__(self, template, target, score):
        self.template, self.target, self.score = template, target, score


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
        self.target, self.target_seq = target, target, seq
        self.scores = scores


class Score(object):
    type = "other"

    def __init__(self, value):
        self.value = value


class BLASTEValue(Score):
    type = "BLAST e-value"
    other_details = None
