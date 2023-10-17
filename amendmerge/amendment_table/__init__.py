from amendmerge import DataSource
from amendmerge.amendment import AmendmentList
class AmendmentTable(DataSource):

    def __init__(self, *args, amendments = [],  **kwargs):

        self.amendments = AmendmentList(amendments)


        DataSource.__init__(self, *args, **kwargs)


    @classmethod
    def create(cls, *args, **kwargs):
        raise NotImplementedError("AmendmentTable should not be instantiated directly.")

    def get_amendments(self):

        if isinstance(self.amendments, AmendmentList):
            return self.amendments
        elif isinstance(self.amendments, list):
            return AmendmentList(self.amendments)
        else:
            return self.amendments

    def get_type(self):
        return 'amendment_table'

    def get_amendment_num(self):
        return len(self.amendments)
