class Data(object):
    data_content_type = 'other'
    data_other_details = None

    def __init__(self, name, details=None):
        self.name = name
        self.data_other_details = details
