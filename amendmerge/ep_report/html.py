from amendmerge import DataSource
from amendmerge.ep_report import EpReport

def subformat_factory(subformat):

    raise NotImplementedError


class HtmlEpReport(EpReport):

    """Generic class for HTML EP reports. Automatically detects the subformat and returns an instance of the right subclass"""

    def __init__(self, **kwargs):

        # Choose the right subclass for the
        # right type (subformat) of html report
        # and return an instance of that subclass

        return subformat_factory(self.get_subformat())


    def get_subformat (self):
        # try to detect which type of html report this is
        return NotImplementedError

    def get_format(self):
        return 'html'


def HtmlEpReportSubFormat(EpReport):

    """Generic class for HTML subformat variants of EP reports"""

    def __init__(self, **kwargs):

        super(DataSource, self).__init__(**kwargs)

def HtmlSubFormat1(HtmlEpReport):

    raise NotImplementedError
