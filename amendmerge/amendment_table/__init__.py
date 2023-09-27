from amendmerge import DataSource
class AmendmentTable(DataSource):

    def __init__(self, *args, amendments = [],  **kwargs):

        self.amendments = amendments


        DataSource.__init__(self, *args, **kwargs)


    @classmethod
    def create(cls, *args, **kwargs):
        raise NotImplementedError("AmendmentTable should not be instantiated directly.")

    def get_amendments(self):
        return self.amendments

    def get_type(self):
        return 'amendment_table'

    def get_amendment_num(self):
        return len(self.amendments)
