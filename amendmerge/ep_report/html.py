import re

from amendmerge import DataSource
from amendmerge.ep_report import EpReport
from bs4 import BeautifulSoup
import warnings

from amendmerge.resolution.html import HtmlResolution
from amendmerge.utils import determine_ep_report_html_subformat, html_parser
from amendmerge import Html




class HtmlEpReport(EpReport):

    """Generic class for HTML EP reports. Automatically detects the subformat and returns an instance of the right subclass"""

    @classmethod
    def create(cls, *args, **kwargs):

        source = kwargs.get('source') or args[0]

        assert source is not None, "Need to specify source."


        if kwargs.get('subformat') is None:
            kwargs['subformat'] = determine_ep_report_html_subformat(source)

        if kwargs['subformat'].startswith('202305'):
            return HtmlEpReport202305(*args, **kwargs)




class HtmlEpReportSubFormat(EpReport, Html):

    """Generic class for HTML subformat variants of EP reports because EpReport is a special case of DataSource containing multiple resolutions and can therefore not be used as a parent for subformats directly"""


    def __init__(self, *args, **kwargs):

        self.resolutions = None

        DataSource.__init__(self, *args, **kwargs) # call the parent class constructor because EpReport is a special case of DataSource containing multiple resolutions

class HtmlEpReport202305(HtmlEpReportSubFormat):

    def find_resolutions(self):

        # subformat specific parsing steps
        if self.subformat.endswith('-old'):
            start_hs = self.source.find_all('h2', {'id': (lambda x: x and x.startswith('_section'))})
            contents = [BeautifulSoup('<div>' + str(h) + str(h.findNext('div')) + '</div>', 'lxml').find('div') for h in
                        start_hs]


            # check if part is actually a resolution (parse title)
            titles = [h.get_text().strip() for h in start_hs]

            # check resolution matches
            re_resolution = re.compile('legislative\s*resolution', re.IGNORECASE)

            # sometimes amendment tables haveir own title
            re_legislative_prop = re.compile('legislative\s*proposal', re.IGNORECASE)

            resolution_indices = [i for i, title in enumerate(titles) if re_resolution.search(title) is not None]
            legislative_prop_indices = [i for i, title in enumerate(titles) if re_legislative_prop.search(title) is not None]

            if len(resolution_indices) == 0:
                warnings.warn("No resolution found in content container when looking for resolutions.")
            elif len(resolution_indices) > 1:

                warnings.warn("More than one resolution found in content container when looking for resolutions.")
            else:
                if len(legislative_prop_indices) > 1:
                    warnings.warn("More than one legislative proposal found in content container when looking for resolutions.")

            self.resolutions = [HtmlResolution.create(content, report=self, subformat=self.subformat, amend_only_suspect=True) for i, content in
                                enumerate(contents) if i in resolution_indices + legislative_prop_indices]


        elif self.subformat.endswith('-new'):
            main_content = self.source.find_all('div', {'class': (lambda x: x and x.startswith('red'))})

            contents_strings = ['']

            # keep all content after h until next h2
            i = 0

            # loop over big content containers
            for content in main_content:

                # find the first h2 as the start of content
                title = content.find('h2')

                if title is None:
                    title = content.find(class_='doc_title')

                    if title is not None:
                        title_parent = content.find_parent('table')

                        if title_parent is not None:
                            title = title_parent
                            title_tag = 'table'
                        else:
                            warnings.warn("No title found in content container when looking for resolutions.")
                    else:
                        warnings.warn("No title found in content container when looking for resolutions.")
                else:
                    title_tag = 'h2'

                if title is not None:
                    contents_strings[i] += str(title)
                    # find the next h2 as the end of content and get all content in between
                    for tag in title.findNextSiblings():
                        if tag.name == title_tag:
                            contents_strings.append(str(tag))
                            i = i + 1
                        else:
                            contents_strings[i] = contents_strings[i] + str(tag)

                contents_strings.append('')
                i = i + 1

                # TODO check if part is actually a resolution (parse title)
                self.resolutions = [HtmlResolution.create(BeautifulSoup('<div>' + content + '</div>', html_parser()), report=self, subformat=self.subformat) for i, content in enumerate(contents_strings) if len(content) > 0 and i == 0]



