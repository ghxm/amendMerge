import re
from bs4 import BeautifulSoup
import copy
from amendmerge.utils import html_parser, bs_set, clean_html_text
from amendmerge.resolution import Resolution
from amendmerge.amendment_table.html import HtmlAmendmentTable
from amendmerge import Html, DataSource
import warnings
from collections import OrderedDict



class HtmlResolution(Resolution, Html):

    """Generic class for HTML resolutions"""

    def __init__(self, *args,  start = None, **kwargs):

            self.start = start
            self.amendments_before_text = None

            super().__init__(*args, **kwargs)


    @classmethod
    def create(cls, *args, **kwargs):

        from amendmerge.ep_report.html import determine_ep_report_html_subformat

        source = kwargs.get('source') or args[0]

        assert source is not None, "Need to specify source."


        if kwargs.get('subformat') is None:
            kwargs['subformat'] = determine_ep_report_html_subformat(source)

        if kwargs['subformat'].startswith('202305'):
            return HtmlResolution202305(*args, **kwargs)
        else:
            raise ValueError('Unknown subformat: ' + kwargs['subformat'])

    def find_amendment_type(self):

        if not hasattr(self, 'text') or self.text is None:
            self.find_text()

        text = self.text[:1800]

        self.amendment_type = None

        if re.search('simplified\s*procedure', text, re.MULTILINE|re.IGNORECASE) is not None:
            self.amendment_type = 'simplified_procedure'
        elif re.search('reject[s]+\s*the\s*Co[m]+i[s]+ion.*proposal', text, re.MULTILINE|re.IGNORECASE) is not None:
            self.amendment_type = 'reject_com_proposal'
        elif re.search('rejects\s*the\s*Council\s*', text, re.MULTILINE|re.IGNORECASE) is not None:
            self.amendment_type = 'reject_cou_position'
        elif re.search('(?:taking[\s]*over[\s]*the[\s]*Commission[\s]*proposal)|(?:approves\s*the\s*commission\s*proposal)(;|\s*as\s*adapted)', self.text, re.MULTILINE|re.IGNORECASE) is not None:
            if re.search('proposal\s*as\s*adapted', text, re.MULTILINE|re.IGNORECASE) is not None:
                self.amendment_type = 'taking_over_com_proposal_adapted'
            else:
                self.amendment_type = 'taking_over_com_proposal'
        elif re.search('(?:[Aa][p]+[r]*[o]*[v]*[e]*[s]*\s*.{0,20}[t]*[h]*[e]*\s*[Cc][o]+[m]+[i]+[s]+[i]*[o]+[n]*\s*[p]+[o]+[s]*[i]*[t]+[i]*[o]*[n]*)',self.text, re.MULTILINE | re.IGNORECASE) is not None:
            self.amendment_type = 'approve_com_position'
        elif re.search('(?:[Aa][p]+[r]*[o]*[v]*[e]*[s]*\s*.{0,20}[t]*[h]*[e]*\s*[j][o]+[i]*[n]*[t]*\s*[t]+[e]+[x]*[t]*)', self.text, re.MULTILINE | re.IGNORECASE) is not None:
            self.amendment_type = 'approve_joint_text'
        elif re.search('(?:[Aa][p]+[r]*[o]*[v]*[e]+[s]*\s*.{0,20}[t]*[h]*[e]*\s*[Cc][o]+[u]+[n]+[c]*[i]*[l]*\s*[Pp]*[o]*[s]*[i]*[t]*[i]*[o]*[n]*)',self.text, re.MULTILINE | re.IGNORECASE) is not None:
            self.amendment_type = 'approve_cou_position'
        else:
            amendments_before = False
            if hasattr(self, 'amendments_before_text') and self.amendments_before_text:
                amendments_before = True
                elements_outside_resolution_text = [e for e in self.get_elements_before_text(n=-1)]
                elements_outside_resolution_text = elements_outside_resolution_text[:4]
            else:
                elements_outside_resolution_text = self.get_elements_after_text(n=3)

            if re.search(r'^\s*[\(]*Amendment\s+', '\n'.join([e.get_text(strip=True, separator='\n') for e in elements_outside_resolution_text]), re.MULTILINE|re.IGNORECASE) is not None:

                next_text = None

                for i, el in enumerate(elements_outside_resolution_text):

                    if len(el.get_text().strip()) < 15 \
                        or (amendments_before and re.search('following\s*amendments', el.get_text().strip(), re.MULTILINE|re.IGNORECASE) is not None):
                        continue
                    else:
                        next_text =  "\n".join([e.get_text().strip() for e in elements_outside_resolution_text[i:]])
                        break

                if next_text is None:
                    next_text = "\n".join([e.get_text().strip() for e in elements_outside_resolution_text])

                if re.search(r'^\s*Amendments\s*by', next_text[0:20], re.MULTILINE|re.IGNORECASE) is not None or \
                        re.search(r'^\s*Amendments\s*by', next_text[0:130], re.MULTILINE|re.IGNORECASE) is not None and re.search(r'^\s*(text\s*proposed|proposed\s*text)', next_text[0:130], re.MULTILINE|re.IGNORECASE) is None:
                    self.amendment_type = 'amendments_text'
                else:
                    self.amendment_type = 'amendments_table'
            else:
                self.amendment_type = 'amendments_text'

        if self.amendment_type is None:
            warnings.warn("No amendment type found for resolution.")

    def get_elements_after_text(self, n):
        raise NotImplementedError("This method must be implemented in a subclass")

    def get_elements_before_text(self, n):
        raise NotImplementedError("This method must be implemented in a subclass")



class HtmlResolution202305(HtmlResolution):


    def find_title(self):

        """Identify the title element of the resolution and set the `title` attribute."""

        if not hasattr(self, 'start') or self.start is None:
            self.find_start()

        if self.start is not None:
            self.title = self.start.get_text().strip()

        else:
            self.title = None
            warnings.warn("No title found for resolution.")



    def find_start(self):

        """Find the start of the resolution and set the `resolution_start` attribute."""

        start = self.source.find('h2', {'id': (lambda x: x and x.startswith('_section'))})
        if start is None:
            start = self.source.find('tr', class_='doc_title')
            if start is not None:
                start = start.find_parent('table')

        if start is None:
            warnings.warn("No start found for resolution.")

        self.start = start

    def find_text(self):

        """Find the resolution text and set the `text` attribute."""

        if not hasattr(self, 'start') or self.start is None:
            self.find_start()

        assert self.start is not None, "Need to find resolution start first."

        title_tag = self.start.name

        if self.subformat.endswith('-new'):

            self.text_start = self.start

            # list to store resolution text tags in
            res_text_tags = [self.start]

            for i, tag in enumerate(self.start.find_next_siblings(recursive=False)):
                if tag.name == title_tag:
                    break
                elif tag.get_text().strip().lower().startswith('amendment') or 'text-center' in tag.get('class', []):
                    break
                else:
                    res_text_tags.append(tag)

        else:

            res_text_tags = []

            self.text_start = self.start

            if hasattr(self, 'title') and self.title is not None:
                if re.compile('legislative\s*proposal.*draft\s*legislative\s*resolution', re.IGNORECASE).search(
                        self.title) is not None:
                    # there might be an amendment table before the resolution text

                    # get the full raw text of the source
                    source_text = self.source.get_text()

                    # search for the title and check whether it is followed by 'Amendment' within the next 650 characters
                    if re.search(self.title + r'.{0,650}Amendment\s*[0-9]', source_text,
                              re.IGNORECASE | re.DOTALL) is not None:

                        self.amendments_before_text = True

                        # look for strong tags with text regex 'legislative\s*resolution'
                        text_start = self.source.find('strong', text=re.compile('legislative\s*resolution', re.IGNORECASE))

                        if not text_start:
                            text_start = self.source.find('p|div',
                                                          text=re.compile('legislative\s*resolution', re.IGNORECASE))

                        if text_start:

                            self.text_start = text_start.find_parent('p')

                            res_start = self.text_start

                            # add text_start and all remaining siblings to res_text_tags
                            res_text_tags = [res_start]

                            [res_text_tags.append(tag) for tag in res_start.find_next_siblings(recursive=False)]

            if len(res_text_tags) == 0:
                # normal case/backup: amendments are after the resolution text
                res_div = self.start.find_next_sibling('div')

                res_text_tags = [self.start]

                for i, tag in enumerate(res_div.findAll(recursive=False)):
                    if tag.name == 'h2':
                        break
                    elif tag.name == 'table' \
                         or hasattr(tag, 'class') and 'table-responsive' in tag.get('class', []) \
                         or tag.get_text().strip().lower().startswith('amendment'):
                        break
                    else:
                        res_text_tags.append(tag)



        self.text = '\n'.join([tag.get_text(separator=' ') for tag in res_text_tags])

        self.text_elements = res_text_tags

    def get_elements_before_text(self, n=-1):
        """Find the elements before the resolution text and return a list of elements.

        Parameters
        ----------
        n: int
            Number of elements to return. Default is all (-1).
        """

        if not hasattr(self, 'text_elements') or self.text_elements is None or self.text_start is None:
            self.find_text()
        if not hasattr(self, 'start') or self.start is None:
            self.find_start()

        if self.start == self.text_start:
            return []

        return list(reversed(list(self.text_start.find_previous_siblings(recursive=False))[:n]))


    def get_elements_after_text(self, n=1):

        """Find the elements after the resolution text and return a list of elements.

        Parameters
        ----------
        n: int
            Number of elements to return. Default is all (-1).

        """

        # TODO why not just go off text_start + text_elements length?

        if not hasattr(self, 'text_elements') or self.text_elements is None:
            self.find_text()
        if not hasattr(self, 'start') or self.start is None:
            self.find_start()

        if self.subformat.endswith('-new'):

            for i, tag in enumerate(self.start.find_next_siblings(recursive=False)):
                if tag.name == 'h2':
                    break
                elif tag.get_text().strip().lower().startswith('amendment') or 'text-center' in tag.get('class', []):
                    break
                else:
                    continue

            if n < 0:
                return list(self.start.find_next_siblings(recursive=False))[i:]
            else:
                return list(self.start.find_next_siblings(recursive=False))[i:i + n]

        else:

            res_div = self.start.find_next_sibling('div')

            i = None

            for i, tag in enumerate(res_div.findAll(recursive=False)):
                if tag.name == 'h2':
                    break
                elif tag.name == 'table' \
                        or hasattr(tag, 'class') and 'table-responsive' in tag.get('class', []) \
                        or tag.get_text().strip().lower().startswith('amendment'):
                    break


            if n < 0:
                if i:
                    return list(res_div.findAll(recursive=False))[i:]
            else:
                if i:
                    return list(res_div.findAll(recursive=False))[i:i + n]

            return res_div.findAll(recursive=False)

    def find_amended_text(self):

        # get the number of tags taken up by the resolution text
        res_text_tag_num = len(self.text_elements)-1 # TODO remove one 'ere or keep full length?

        # find resolution start tag
        resolution_start = self.start

        # get all tags after resolution text
        if self.subformat.endswith('-new'):
            res_text_tags = resolution_start.find_next_siblings(recursive = False)[res_text_tag_num:]
        else:
            res_text_tags = resolution_start.find_next_sibling('div').findAll(recursive=False)[res_text_tag_num:]

        amended_text_html = '<div>'

        done_at_found = False
        after_done_at_counter = 0

        # iterate over tags and add them to amended_text_html until done_at is found (this is done because in some cases the next section is not clearly marked)
        for tag in res_text_tags:
            if re.search('^\s*.{0,1}done\s*at', tag.get_text().strip(), re.IGNORECASE) is not None:
                done_at_found = True
                amended_text_html += str(tag)
            else:
                amended_text_html += str(tag)

                # adds two more tags after done_at is found
                if done_at_found:
                    after_done_at_counter += 1
                    if after_done_at_counter == 2:
                        break

        # TODO find a solution that keeps the annex
        warnings.warn('Possible annexes or other sections after resolution text not included in amended text.')

        amended_text_html += '</div>'

        self.amended_text_bs = BeautifulSoup(amended_text_html, html_parser()).find('div')

        # return text
        self.amended_text = clean_html_text('\n'.join([tag.get_text(separator=' ') for tag in self.amended_text_bs.findAll(recursive=False)]))


    def find_amendment_table(self):

        # Find table
        bs = copy.copy(self.source)


        # TODO cases where table is above the resolution text (e.g. A4-1999/0040)

        if self.subformat.endswith('-old'):
            try:
                # there are cases (e.g. A6-0080/2007) where a single table is actually contained in multiple tables
                # so we need to find all tables
                tables = bs.find_all('div', {'class': (lambda x: x and 'table-responsive' in x)})
                trs = [table.find_all('tr', recursive=True) for table in tables]

                # also get elements in between tables in correct position

                for i, table in enumerate(tables):
                    insert_pos = 0

                    if i == len(tables) - 1:
                        break
                    for tag in table.find_next_siblings():
                        if tag.name == 'table' or (tag.name == 'div' and 'table-responsive' in tag.get('class', [])):
                            break
                        else:
                            # insert it at the beginning of the next table
                            trs[i + 1].insert(insert_pos, tag)
                            insert_pos += 1

                # flatten list but don't include dupliate trs
                #trs = list(OrderedDict.fromkeys([tr for sublist in trs for tr in sublist]))

                # flatten list
                trs = [tr for sublist in trs for tr in sublist]

                trs = [tr for tr in trs if not tr.find('tr')] # keep only lowest level trs

                trs = bs_set(trs)

                amendment_table = BeautifulSoup('<table id = "thetable" class="202305-old">' + '\n'.join([str(tr) if tr.name=='tr' else '<tr>' + str(tr) + '</tr>' for tr in trs ]) + '</table>', html_parser()).find('table', {'id': 'thetable'})

            except:
                amendment_table = None
        else:
            try:
                first_row = bs.find('div',  {'class': (lambda x: x and 'table-responsive' in x)}) # bs.find('div', {'class': 'table-responsive'})

                for p in first_row.findAllPrevious('p'):
                    if 'amendment' in p.text.strip().lower():
                        table_start_p = p
                        break

                # for prev in table_start_p.parent.findAllPrevious(recursive = False):
                #    prev.extract()

                tags = table_start_p.findNextSiblings(recursive = False)

                amendment_table = BeautifulSoup('<div id = "thetable" class="202305-new">' + str(table_start_p) + '\n'.join([str(tag) for tag in tags]) + '</div>', html_parser()).find('div', {'id': 'thetable'})
            except:
                amendment_table = None

        # TODO instatiate amendment table object
        if amendment_table is not None:
            self.amendment_table = HtmlAmendmentTable.create(amendment_table, report=self, subformat=self.subformat)
        else:
            warnings.warn("No amendment table found for resolution.")
            self.amendment_table = None
