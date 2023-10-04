import warnings
import re
from bs4 import BeautifulSoup, Tag
import pandas as pd
from collections import OrderedDict

from amendmerge import Html, html_parser, regex as amre
from amendmerge.amendment import Amendment, Position
from amendmerge.amendment_table import AmendmentTable
from amendmerge.utils import is_numeric, dict_nth, dict_roman, bs_set, to_numeric



class HtmlAmendmentTable(AmendmentTable, Html):

    """Class for amendment tables in HTML format."""

    @classmethod
    def create(cls, *args, **kwargs):

        source = kwargs.get('source') or args[0]
        assert source is not None, "Need to specify source."

        if kwargs.get('subformat') is None:
            kwargs['subformat'] = determine_amendment_table_html_subformat(source)

        if kwargs['subformat'].startswith('202305'):
            if kwargs['subformat'].endswith('-old'):
                return HtmlAmendmentTable202305Old(*args, **kwargs)
            elif kwargs['subformat'].endswith('-new'):
                source = HtmlAmendmentTable202305Old.new_to_old(source)
                # adjust subformat to match corrected table
                kwargs['subformat'] = '202305-new-old'

                if 'source' in kwargs:
                    kwargs['source'] = source
                else:
                    args = (source,) + args[1:]

                return HtmlAmendmentTable202305Old(*args, **kwargs)



class HtmlAmendmentTable202305Old(HtmlAmendmentTable):

    """Class for old amendment tables in HTML format.
    Old tables are tables that have <tr> rows in a <table>."""

    def __init__(self, *args, **kwargs):

        if  kwargs.get('subformat') is None:
            kwargs['subformat'] = determine_amendment_table_html_subformat(kwargs.get('source') or args[0])

        HtmlAmendmentTable.__init__(self, *args, **kwargs)


    @staticmethod
    def new_to_old(source):

        if isinstance(source, str):
            bs = BeautifulSoup(source, html_parser())
        elif isinstance(source, Tag):
            bs = source
        else:
            raise ValueError('source must be a string or bs4.Tag')

        tags = bs.findAll(recursive=False)

        table_html = '''
        <table class="table table-borderless">
            <tbody>
        '''

        p_list = []

        # loop over all tags to find paragraphs and tables
        for i, tag in enumerate(tags):
            if tag.name == 'p':
                p_list.append(tag)
                # check if next tag is a div (table) again or the start of a new amendment
                if (i < len(tags) - 1) and (tags[i + 1].name == 'div' or \
                        re.search('^.{,2}\s*(Ame*nd.{,1}ment\s*.{0,2}[0-9])', tags[i+1].get_text(' ', strip=True), re.IGNORECASE|re.MULTILINE)):
                    table_html += '''
                    <tr>
                        <td colspan="2" class="text-center">
                    ''' + '\n'.join(str(p) for p in p_list) + '\n' + '''
                        </td>
                    </tr>
                    '''
                    p_list = []
            elif tag.name == 'div':
                subtab_rows = tag.findAll('tr')
                table_html += '\n'.join(str(tr) for tr in subtab_rows) + '\n'

        classes = []

        # check if there was already a 'thetable' element w existing classes
        if bs.find('div', {'id': 'thetable'}) is not None:

            # save classes
            classes = bs.find('div', {'id': 'thetable'}).get('class')

        # add new classes
        [classes.append(x) for x in ['table-responsive', 'table-fixed', '202305-new-old'] if x not in classes]

        # remove old classes
        classes = [x for x in classes if x not in ['202305-new']]

        return BeautifulSoup(
            '<div id = "thetable" class="' + ' '.join(classes) + '">' + table_html + '</div>',
            'lxml').find('div', {'id': 'thetable'})

    def parse(self):

        parsed_table = HtmlAmendmentTable202305OldParser(self)

        try:
            self.amendments = parsed_table.amendments
            self.table_rows = parsed_table.rows
        except Exception as e:
            warnings.warn('Could not parse amendment table: ' + str(e))
            self.amendments = None




def determine_amendment_table_html_subformat(source):

    subformat = None

    if isinstance(source, str):
        bs = BeautifulSoup(source, html_parser())
    elif isinstance(source, Tag):
        bs = source
    else:
        raise ValueError('source must be a string or bs4.Tag')

    # try to get read out the table classes
    table_classes = [x.get('class') for x in bs.findAll('table') if x.get('class') is not None]

    if len(table_classes) > 0:
        if table_classes[0] == '202305-new':
            if 'table-fixed' in table_classes:
                subformat = '202305-new-old'
            else:
                subformat = '202305-new'
        elif table_classes[0] == '202305-old':
            subformat = '202305-old'

    if subformat is None:
        warnings.warn('Could not determine subformat')

    return subformat

class HtmlAmendmentTableParser:

    def _parse_rows(self):

        """Make sense of the rows and determine the amendments."""

        amendments = []

        # make sure each of the rows has at least a position and an amendment
        for i, row in enumerate(self.rows):
            try:
                amendments.append(self._parse_row(row))
            except ValueError as e:
                warnings.warn('Could not parse row: ' + str(e))

        #amendments = [row for row in amendments if row is not None]

        return amendments


    def _parse_row(self, row):

        """Make sense of the row and determine the amendment.

        Parameters
        ----------
        row : list
            List of bs4.Tag objects representing the <tr> elements of the row.

        Returns
        -------
        An Amendment object.

        """


        if len(row) < 2:
            raise ValueError('Row must have at least two elements.')

        # check if there's are position rows
        header_pos_trs = [tr for tr in row if tr['type'] in ['header_pos', 'header']]

        # amm_trs = [tr for tr in row if tr['type'] == 'amendment' or tr['type'] == 'amendment_add']

        # justification_trs = [tr for tr in row if 'justification' in tr['type']]

        # other_trs = [tr for tr in row if tr['type'] in ['other', None]]


        # POSITION
        positions = []
        position_dict = {}

        amended_act_position_found = False

        for pos_tr in header_pos_trs:


            tr_text = pos_tr.get_text('\n', strip=True)

            # cut off amendment number
            tr_text = re.sub(r'^.{,2}\s*(Ame*nd.{,1}ment\s*.{0,2}[0-9]+)', '', tr_text, flags=re.IGNORECASE|re.MULTILINE)

            # cut off amended acts
            amended_act_pos_match = re.search(r'(^|-).{,2}\s*(Regulation|Directive|Decision|Recommendation).*', tr_text, re.IGNORECASE|re.MULTILINE|re.DOTALL)

            # remove text after amended act
            if amended_act_pos_match is not None:
                tr_text = tr_text.replace(amended_act_pos_match.group(0), '')
                amended_act_position_found = True

            pos = self._parse_position(tr_text)

            if pos is not None:
                positions.append(pos)

            # check if amended act position has been found and skip the rest
            # (in case the position is split in multiple trs)
            if amended_act_position_found:
                break

        # combine position dicts in to a single dict without overwriting

        for pos in positions:
            position_dict = dict(list(position_dict.items()) + list(pos.items()))

        # TODO parse AMENDMENT

        return position_dict # TODO debugging only, remove this


        # TOOD not that amendment relates to amnded act (maybe add as an additional position in amendment object in order not to get confused which is which?)
        # return Amendment(position = Position(**position_dict))




    def _parse_position(self, text):

        """Match a position (e.g. article 1, paragraph 2, point 3, etc.)
        using regex and return a dict with Position object-style arguments."""

        matches = self._match_position_full(text, allow_multiple=True)
        position_dict = {}

        # TODO handle annexes specifically

        for element, m in matches:

            position_num = None

            # inspect group 1
            num_pre = m.group('num_pre')

            if element is None:
                # inspect group 2
                element = m.group('element')
                if element is not None:
                    element_type = self._match_position_element_type(element)
                else:
                    element_type = None
            else:
                element_type = element

            num_post = m.group('num_post')

            if element_type and element_type == 'title':
                num_pre = None
                num_post = 0

            if all([num_pre, num_post]):
                warnings.warn('Both pre and post number are given for position: ' + m.group(0))
            elif num_pre is None and num_post is None:
                warnings.warn('Neither pre nor post number are given for position: ' + m.group(0))
            else:
                if num_pre is not None:
                    position_num = num_pre
                elif num_post is not None:
                    position_num = num_post

            if position_num is not None:
                # TODO handle cases like 'Recital 9 a (new)'
                #  possibly in Position class by providing a 'new' attribute
                try:
                    position_num = to_numeric(position_num)
                except ValueError:
                    position_num = position_num

            if element_type is not None:
                position_dict[element_type] = position_num

        return position_dict





    def _match_position_full(self, text, allow_multiple = False):

        """Match a full position (e.g. article 1, paragraph 2, point 3, etc.) using regex and return the element type and match.

        Parameters
        ----------
        text : str
            The text to be matched.
        allow_multiple : bool, optional
            Whether to allow multiple matches. Defaults to False.

        Returns
        -------
        list or tuple

        """

        matches = []

        for key, regex in amre.position_elements_numbers.items():
            match = re.search(regex, text, re.IGNORECASE) # TODO might need to re.finditer to catch multiple number matches like Article 1 3
            if match is not None:
                if not allow_multiple:
                    return (key, match)
                else:
                    matches.append((key, match))

        if allow_multiple:
            return matches
        else:
            return None


    def _match_position_element_type(self, text, allow_multiple = False):

        """Match a position type (e.g. article, paragraph, point, recital, etc.) to a regex."""

        keys = []

        # for all key, regex pairs in amre, check for matches and return the key
        for key, regex in amre.position_elements.items():
            if re.search(regex, text, re.IGNORECASE) is not None:
                if not allow_multiple:
                    return key
                else:
                    keys.append(key)

        if allow_multiple:
            return keys
        else:
            return None

    def _match_position_num(self, text, type = None, allow_multiple = False, return_int = True):

        """
        Match a position number (e.g. 1, 2, 3, etc.) and return it.
        """

        """Match a position type (e.g. article, paragraph, point, recital, etc.) to a regex."""


        # match numbers for that type using amre.position_elements_numbers[type]
        if type is not None:
            match = re.search(amre.position_elements_numbers[type], text, re.IGNORECASE)
            if match is not None:
                return match
        else:
            matches = []
            # try all types
            for type in amre.position_elements_numbers.keys():
                match = re.search(amre.position_elements_numbers[type], text, re.IGNORECASE)
                if match is not None:
                    if not allow_multiple:
                        return match
                    else:
                        matches.append(match)
        if allow_multiple:
            return matches
        else:
            return None











class HtmlAmendmentTable202305OldParser(HtmlAmendmentTableParser):

    def __init__(self, amendment_table):

        if not isinstance(amendment_table, AmendmentTable):
            raise ValueError('amendment_table must be of type AmendmentTable')

        self.source = amendment_table.source
        self.table_style = None

        self.rows = []
        self.amendments = []

        if amendment_table.subformat.endswith('new-old'):
            self.table_style = 'new-old'
        elif amendment_table.subformat.endswith('-old'):
            self.table_style = 'old'
        else:
            raise ValueError('Unknown subformat for class ' + type(self).__name__ + ': ' + amendment_table.subformat)

        if self.table_style is None:
            if 'table-fixed' in self.source.attrs['class']:
                table_style = 'new-old'
            elif 'old-table-old' in self.source.attrs['class']:
                table_style = 'old-old'
            elif 'table-old' in self.source.attrs['class'] and not 'table-new' in self.source.attrs['class']:
                table_style = 'old'

        if self.table_style is None:
            table_style = 'old'
            warnings.warn('Could not determine table style. Defaulting to old.')
        elif self.table_style == 'new':
            # throw an error because we don't know how to handle new tables
            raise ValueError('Unknown table style for class ' + type(self).__name__ + ': ' + str(self.source.attrs['class']))

        self.parse()
    def determine_tr_search_recursiveness(self):

        tr_recursive = False

        if self.table_style == 'old-old':
            tr_recursive = True
        elif self.table_style == 'old':
            tr_recursive = False
        elif self.table_style == 'new-old':
            tr_recursive = True

        return tr_recursive

    def _add_new_row(self, tr = None):
        if tr is not None:
            self.rows.append([tr])
        else:
            self.rows.append([])

    def _add_to_current_row(self, tr):
        # add tr to last row
        self.rows[-1].append(tr)

    def _get_current_row(self):
        return self.rows[-1]

    def _get_previous(self, type='tr'):
        if type == 'tr':
            prev_row = self._get_previous(type='row')
            if prev_row:
                return prev_row[-1]
            else:
                return None
        elif type == 'row':
            # get last non-empty row
            for row in reversed(self.rows):
                if len(row) > 0:
                    return row
            return None
        else:
            raise ValueError('type must be tr or row')


    def _is_start_of_new_row(self, tr_type):
        # check last element of current row
        current_row = self._get_current_row()

        if tr_type in ['header', 'col_header', 'header_pos']:
            # if we already saw an amendment in the current row, then this is probably the start of a new row
            if any([x in ['amendment', 'other', 'empty_img'] for x in [x['type'] for x in current_row]]):
                return True
        else:
            return False

    def _td_count(self, tr):
        return len(tr.find_all('td'))

    def parse(self):

        # get the table rows
        if self.source.name == 'div':
            bs = self.source.find('table')
        elif self.source.name == 'table':
            bs = self.source
        else:
            raise ValueError('source must be a table or div')

        trs = bs.find_all('tr', recursive=self.determine_tr_search_recursiveness())

        # remove duplicate trs
        #trs = list(OrderedDict.fromkeys(trs))

        trs = [tr for tr in trs if not tr.find('tr')]  # keep only lowest level trs

        trs = bs_set(trs)

        self.rows = [[]] # initialize rows with empty list of lists

        for i, tr in enumerate(trs):

            # make sure we're not looping over duplicate content
            if tr in [x for row in self.rows for x in row]:
                continue

            try:
                # type should not be set yet
                tr['type']
                continue
            except KeyError:
                pass

            tr['type'] = self._determine_tr_type(tr)

            if i>2 and self._is_start_of_new_row(tr['type']):
                self._add_new_row(tr)
            else:
                self._add_to_current_row(tr)


        self.amendments = self._parse_rows()




    def _determine_tr_type(self, tr):

        if self.table_style == 'new-old':
            tr_text = tr.get_text(' ', strip=True)
        else:
            tr_text = tr.get_text(strip=True)

        if tr_text == '':
            if tr.find('img') is not None:
                return 'empty_img'
            else:
                return 'empty'
        elif re.search('^.{,2}\s*(Ame*nd.{,1}ment\s*.{0,2}[0-9])', tr_text.strip(), re.IGNORECASE) is not None:
            return 'header'
        elif re.search(r'(?:^.{,2}(?:Text\s*proposed\s*by)|(?:Proposed\s*text))|(?:Amendment[s]*(s\s*by\s*Parliament)*$)', tr_text.strip(), re.IGNORECASE) is not None:
            # check if it might be a single column col header (tex proposed and amendment in separate rows)
            if sum([re.search(r'(?:^.{,2}(?:Text\s*proposed\s*by)|(?:Proposed\s*text))', tr_text.strip(), re.IGNORECASE) is not None, re.search(r'(?:Amendment[s]*(s\s*by\s*Parliament)*$)', tr_text.strip(), re.IGNORECASE) is not None]) == 1:
                return "col_header_single"
            else:
                return "col_header"
        elif re.search(r'Justification', tr_text) is not None:
            return "header_justification"
        elif self._get_previous() and ((self._get_previous(type='tr')['type'] == "header_justification") or (
                self._get_previous(type='tr')['type'] == "justification" and (self._td_count(tr) > 0 and int(tr.td['colspan']) >= 2))):
            return "justification"
        elif self._get_previous() and  (self._get_previous(type='tr')['type'] and (self._get_previous(type='tr')['type'].startswith("col_header")) or (
                self._get_previous(type='tr')['type'] in ['header', 'header_pos']) or self._td_count(tr)>1): # EXPERIMENTAL removed and re.search(r'(^Present)|(^Text proposed)', tr_text) check
            return "amendment"
        elif  self._get_previous() and (self._get_previous(type='tr')['type'] == "amendment" or self._get_previous(type='tr')['type'] == "amendment_add"):
            return "amendment_add"
        elif re.search(r'^[^"\'`´“"]{,2}(recital|citation|article|paragraph|point|title|annex|section)', tr_text.lower().strip(), re.MULTILINE) is not None:
            return 'header_pos'
        elif  self._get_previous() and ((self._get_previous(type='tr')['type'] == "header_pos") or (self._get_previous(type='tr')['type'] == "amm_raw")):
            return "other"
        else:
            warnings.warn('Could not determine type of tr: ' + tr_text)

            return None















