import re

from amendmerge import DataSource
import warnings

class EpReport(DataSource):

    def __init__(self, *args, resolutions = [], **kwargs):

        self.resolutions = resolutions

        DataSource.__init__(self, *args, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs):



        if kwargs['format'] == 'html':
            from amendmerge.ep_report.html import HtmlEpReport

            return HtmlEpReport.create(*args, **kwargs)
        else:
            raise ValueError('Unknown format: ' + format)


    def get_type(self):
        return 'ep_report'

    def parse(self):

        if not self.resolutions or self.resolutions and len(self.resolutions) == 0:
            self.find_resolutions()

        try:
            self.sanity_check_resolutions()
        except AssertionError as e:
            warnings.warn('Resolution sanity check failed:' + str(e))


    def find_resolutions(self):

        """Find all resolutions in the report and return a list of Resolution objects.
        This method must be implemented in a subclass"""

        raise NotImplementedError("This method must be implemented in a subclass")

    def get_ep_draft_resolution(self):

        """Function to identify and return the EP draft resolution from the report.
            Currently, looks for titles indicating a draft resolution and if none are found
            defaults to the first resolution in the list."""


        for resolution in self.resolutions:
            if re.search('draft.*resolution|legislative.*resolution', str(resolution.title), re.IGNORECASE) is not None:
                return resolution

        for resolution in self.resolutions:
            if not 'opinion' in str(resolution.title).lower() and re.search('draft.+|legislative.*proposal', str(resolution.text), re.IGNORECASE) is not None:
                return resolution

        try:
            return self.resolutions[0]
        except (IndexError, AttributeError):
            return None

    def sanity_check_resolutions(self):

        assert isinstance(self.resolutions, list), "Resolutions must be a list."

        merged_sources = []

        for i, resolution in enumerate(self.resolutions):

            resolution.merged_amendment_source = False

            from amendmerge.resolution import Resolution
            assert isinstance(resolution, Resolution), "Resolutions must be of type Resolution."

            # check if a resolution does not have any amendment source but should have one
            assert resolution.amendment_type is not None, "Resolution must have an amendment type."

            if resolution.amendment_type.startswith('amendment'):

                if (resolution.amendment_type == 'amendments_table' and not resolution.has_no_amendment_table()) or \
                        (resolution.amendment_type == 'amendments_text' and not resolution.has_no_amended_text()):
                    continue
                elif resolution.amendment_type == 'amendments_table' and resolution.has_no_amendment_table() and not resolution.has_no_amended_text():
                    resolution.amendment_type = 'amendments_text'
                elif resolution.amendment_type == 'amendments_text' and resolution.has_no_amended_text() and not resolution.has_no_amendment_table():
                    resolution.amendment_type = 'amendments_table'
                else:

                    if len(self.resolutions) == 1:
                        warnings.warn("Resolution has no amendment source.")
                    else:

                        merged_sources = []

                        # look 1 above/below for lonely amendment sources and combine them
                        for i_ in range(i-1, i+2):

                            try:
                                if i_ < 0 or i_-1 >= len(self.resolutions) or i == i_ or self.resolutions[i_] in merged_sources:
                                    continue
                            except IndexError:
                                continue

                            if self.resolutions[i_].has_no_text() and not self.resolutions[i_].has_no_amendment_source():
                                # merge source to lonely text
                                resolution.amendment_type = self.resolutions[i_].amendment_type

                                if resolution.amendment_type == 'amendments_table':
                                    resolution.amendment_table = self.resolutions[i_].amendment_table
                                elif resolution.amendment_type == 'amendments_text':
                                    resolution.amended_text = self.resolutions[i_].amended_text

                                self.resolutions[i_].merged_amendment_source = True

                                merged_sources.append(self.resolutions[i_])

                        # delete merged sources
        self.resolutions = [resolution for resolution in self.resolutions if resolution not in merged_sources]












