import ma.data


class AlignmentMode(ma.data.Data):
    data_content_type = 'target-template alignment'

    def __init__(self, name, software=None):
        ma.data.Data.__init__(self, name)
        self.software = software


class Global(AlignmentMode):
    mode = "global"


class AlignmentType(object):
    type = "other"


class Pairwise(AlignmentType):
    type = "target-template pairwise alignment"
    other_details = None
