import re

from amendmerge import DataSource, html_parser
from amendmerge.ep_report import EpReport
from bs4 import BeautifulSoup, Tag
import warnings

from amendmerge.resolution.html import HtmlResolution
from amendmerge.utils import html_parser
from amendmerge import Html, regex as amre




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




class HtmlEpReportSubFormat(Html, EpReport):

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

            # TODO this restricts resolution search to EP draft resolutions / legislative proposals
            #     possibly extend to other resolutions


            resolution_indices = [i for i, title in enumerate(titles) if re.search(amre.legislative_resolution_title, title, re.IGNORECASE) is not None]

            # # check resolution matches
            # re_resolution = re.compile('legislative\s*resolution|draft\s*decision', re.IGNORECASE)
            #
            # # sometimes amendment tables have their own title
            # re_legislative_prop = re.compile('legislative\s*proposal', re.IGNORECASE)
            #
            # resolution_indices = [i for i, title in enumerate(titles) if re_resolution.search(title) is not None]
            # legislative_prop_indices = [i for i, title in enumerate(titles) if re_legislative_prop.search(title) is not None]
            #
            if len(resolution_indices) == 0:
                warnings.warn("No resolution found in content container when looking for resolutions.")
            elif len(resolution_indices) > 1:
                warnings.warn("More than one resolution found in content container when looking for resolutions.")
            # else:
            #     if len(legislative_prop_indices) > 1:
            #         warnings.warn("More than one legislative proposal found in content container when looking for resolutions.")


            self.resolutions = [HtmlResolution.create(content, report=self, subformat=self.subformat, amend_only_suspect=True) for i, content in
                                enumerate(contents) if i in resolution_indices]


        elif self.subformat.endswith('-new'):
            main_content = self.source.find_all('div', {'class': (lambda x: x and x.startswith('red'))})

            contents_strings = ['']

            # keep all content after h until next h2
            i = 0

            self.resolutions = []

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

                    if i > 0:
                        # check if there is content above the title that may belong to the previous title
                        if title.previous_sibling is not None:
                            above_title = [str(tag) for tag in title.previous_siblings if tag.name is not None]
                            if len(above_title) > 0:
                                # reverse the list, join it to a string and add it to the previous content
                                contents_strings[i-1] = contents_strings[i-1] + ''.join(reversed(above_title))


                    contents_strings[i] += str(title)
                    # find the next h2 as the end of content and get all content in between
                    for tag in title.find_next_siblings():
                        if tag.name == title_tag:
                            contents_strings.append(str(tag))
                            i = i + 1
                        else:
                            contents_strings[i] = contents_strings[i] + str(tag)
                else:
                    # might be a misconstructed html report where the amendemnts are in a separate container
                    # check for amendment indicators in the first 100 characters of the content
                    if re.search(amre.resolution_amendemnts_start, content.get_text().lower().strip()[:100], re.IGNORECASE) is not None:
                        # add to previous content
                        if i > 0:
                            contents_strings[i-1] = contents_strings[i-1] + str(content)

                contents_strings.append('')
                i = i + 1

            # check if part is actually a resolution (parse title)
            # TODO incorporate this into the above loop
            contents_strings_filtered = []
            for contents_string in contents_strings:
                if len(contents_string.strip()) == 0:
                    continue
                else:
                    try:
                        res_title = BeautifulSoup(contents_string, html_parser()).find('h2').get_text('\n')
                        if res_title is not None:
                            if re.search(amre.legislative_resolution_title, str(res_title), re.IGNORECASE) is not None:
                                contents_strings_filtered.append(contents_string)
                    except:
                        warnings.warn("Could not parse title of possible resolution, skipping.")

            if len(contents_strings_filtered) == 0:
                warnings.warn("No resolution found in content container when looking for resolutions.")
            elif len(contents_strings_filtered) > 1:
                warnings.warn("More than one resolution found in content container when looking for resolutions.")


            self.resolutions = [HtmlResolution.create(BeautifulSoup('<div>' + content + '</div>', html_parser()), report=self, subformat=self.subformat) for i, content in enumerate(contents_strings_filtered) if len(content) > 0]


def determine_ep_report_html_subformat(source):
    subformat = ''

    if isinstance(source, str):
        bs = BeautifulSoup(source, html_parser())
    elif isinstance(source, Tag):
        bs = source
    else:
        raise ValueError('source must be a string or bs4.Tag')

    # get list of all ids
    ids = set([x.get('id') for x in bs.findAll()])

    # check if any match _section format
    section_ids = [x for x in ids if hasattr(x, 'startswith') and x.startswith('_section')]

    if len(section_ids) > 0:
        subformat += '202305'

        # check if it's an older case or a newer by looking for classes starting with 'red'
        red_classes = bs.findAll('div', {'class': (lambda x: x and x.startswith('red'))})

        if red_classes is not None and len(red_classes) > 0:
            # new cases in new layout
            subformat += '-new'
        else:
            # old cases in old layout
            subformat += '-old'

    else:
        warnings.warn('Could not determine subformat')

    return subformat
