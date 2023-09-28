import warnings
import re
from bs4 import BeautifulSoup, Tag
import pandas as pd

from amendmerge import Html, html_parser
from amendmerge.amendment_table import AmendmentTable
from amendmerge.utils import is_numeric, dict_nth, dict_roman



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

        for i, tag in enumerate(tags):
            if tag.name == 'p':
                p_list.append(tag)
                # check if next tag is a div (table)
                if i < len(tags) - 1 and tags[i + 1].name == 'div':
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
        [classes.append(x) for x in ['table-responsive', 'table-fixed'] if x not in classes]

        return BeautifulSoup(
            '<div id = "thetable" class="' + ' '.join(classes) + '">' + table_html + '</div>',
            'lxml').find('div', {'id': 'thetable'})

    def parse(self):

        try:
            parsed_table = HtmlAmendmentTable202305OldParser(self)
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


class HtmlAmendmentTable202305OldParser:

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
            return self._get_previous(type='row')[-1]
        elif type == 'row':
            # get last non-empty row
            for row in reversed(self.rows):
                if len(row) > 0:
                    return row
        else:
            raise ValueError('type must be tr or row')


    def _is_start_of_new_row(self, tr_type):
        # check last element of current row
        current_row = self._get_current_row()

        if tr_type in ['header', 'col_header', 'header_pos']:
            # if we already saw an amendment in the current row, then this is probably the start of a new row
            if any([x in ['amendment', 'other'] for x in [x['type'] for x in current_row]]):
                return True
        else:
            return False

    def parse(self):

        # get the table rows
        if self.source.name == 'div':
            bs = self.source.find('table')
        elif self.source.name == 'table':
            bs = self.source
        else:
            raise ValueError('source must be a table or div')

        trs = bs.find_all('tr', recursive=self.determine_tr_search_recursiveness())

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


        self._parse_rows()

    def _parse_rows(self):
        # TODO
        pass



    def _determine_tr_type(self, tr):

        if self.table_style == 'new-old':
            tr_text = tr.get_text(' ', strip=True)
        else:
            tr_text = tr.get_text(strip=True)

        if tr_text == '':
            return 'empty'
        elif re.search('^Amendment\s*[0-9]', tr_text) is not None:
            return 'header'
        elif re.search(r'^.{,2}recital|citation|article|paragraph|point|title|annex|section', tr_text.lower().strip()) is not None:
            return 'header_pos'
        elif re.search(r'Amendment(s\s*by\s*Parliament)*$', tr_text) is not None:
            return "col_header"
        elif re.search(r'Justification', tr_text) is not None:
            return "header_justification"
        elif (self._get_previous(type='tr')['type'] == "header_justification") or (
                self._get_previous(type='tr')['type'] == "justification" and int(tr.td['colspan']) == 3):
            return "justification"
        elif (self._get_previous(type='tr')['type'] == "col_header") or (
                self._get_previous(type='tr')['type'] in ['header', 'header_pos']): # EXPERIMENTAL removed and re.search(r'(^Present)|(^Text proposed)', tr_text) check
            return "amendment"
        elif self._get_previous(type='tr')['type'] == "amendment" or self._get_previous(type='tr')['type'] == "amendment_add":
            return "amendment_add"
        elif (self._get_previous(type='tr')['type'] == "pos") or (self._get_previous(type='tr')['type'] == "amm_raw"):
            return "other"
        else:
            warnings.warn('Could not determine type of tr: ' + tr_text)

            return None















