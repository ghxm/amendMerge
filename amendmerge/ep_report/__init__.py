from amendmerge import DataSource

class EpReport(DataSource):

    def get_type(self):
        return 'ep_report'

    def parse(self):

        # define steps thats need to be taken to parse any EP report

        raise NotImplementedError
