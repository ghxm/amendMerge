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

        bs = self.source

        table_style = None

        if self.subformat.endswith('new-old'):
            table_style = 'new-old'
        elif self.subformat.endswith('-old'):
            table_style = 'old'
        else:
            raise ValueError('Unknown subformat for class '+ type(self).__name__ + ': ' + self.subformat)

        try:
            if table_style is None:
                if 'table-fixed' in bs.attrs['class']:
                    table_style = 'new-old'
                elif 'old-table-old' in bs.attrs['class']:
                    table_style = 'old-old'
                elif 'table-old' in bs.attrs['class'] and not 'table-new' in bs.attrs['class']:
                    table_style = 'old'
                else:
                    table_style = 'new'
        except:
            warnings.warn('Could not identify table style')

        if table_style == 'new':
            raise Exception('New table style not implemented')

        if bs.name == 'div':
            bs = bs.find('table')



        list_amno = []
        list_pos = []

        list_pos_title = []
        list_pos_citation = []
        list_pos_recital = []
        list_pos_article = []
        list_pos_paragraph = []
        list_pos_subpar = []
        list_pos_point = []
        list_pos_subpoint = []
        list_pos_indent = []
        list_pos_annexno = []
        list_pos_part = []
        list_pos_annex = []

        list_pos_annex_num = []
        list_pos_annex_subnum = []
        list_pos_annex_alpha = []
        list_pos_annex_subalpha = []

        list_amendedpos = []
        list_amtype = []
        list_text = []
        list_amendment = []
        list_justification = []
        list_ammraw = []

        # Loop over table rows
        list_tr_type = [""]

        tr_recursive = False

        if table_style == 'old-old':
            tr_recursive = True
        elif table_style == 'old':
            tr_recursive = False
        elif table_style == 'new-old':
            tr_recursive = True


        for tr in bs.find_all('tr', recursive=tr_recursive):

            amno = ""
            pos = ""
            amendedpos = ""
            amtype = ""
            text = ""
            amendment = ""
            justification = ""
            tr_type = ""
            amm_raw = ""
            tr_ignore = False
            new_row = False

            # Check the type of row (Position, Column header, text, justification, ...)

            if table_style == 'new-old':
                tr_text = tr.get_text(' ', strip=True)
            else:
                tr_text = tr.get_text(strip=True)

            if (tr_text == ""):  # or (re.search(r'^_+$', tr_text) is not None) or (re.search(r'\*OJ', tr_text) is not None): # @TODO: Remove manually from amendments
                tr_ignore = True

            if tr_ignore is False:
                if re.search(r'^Amendment\s*[0-9]', tr_text) is not None:
                    tr_type = "pos"
                    new_row = True
                elif re.search(r'Amendment(s\s*by\s*Parliament)*$', tr_text) is not None:
                    tr_type = "col_header"
                elif re.search(r'Justification', tr_text) is not None:
                    tr_type = "col_header_justification"
                elif (list_tr_type[-1] == "col_header_justification") or (
                    list_tr_type[-1] == "justification" and int(tr.td['colspan']) == 3):
                    tr_type = "justification"
                elif (list_tr_type[-1] == "col_header") or (
                    list_tr_type[-1] == "pos" and re.search(r'(^Present)|(^Text proposed)', tr_text)):
                    tr_type = "amendment"
                elif list_tr_type[-1] == "amendment" or list_tr_type[-1] == "amendment_add":
                    tr_type = "amendment_add"
                elif (list_tr_type[-1] == "pos") or (list_tr_type[-1] == "amm_raw"):
                    tr_type = "amm_raw"

                else:
                    # do some other checks and if fails, then print warning mewssage
                    warnings.warn("Row type not recognized:" + "\n" + tr_text)

                # Check whether type != type of the previous row

                if (tr_type == list_tr_type[
                    -1]) and tr_type != "amendment_add" and tr_type != "amm_raw" and tr_type != "":
                    warnings.wanr("Two consecutive rows of type " + tr_type)

                list_tr_type.append(tr_type)

            # add new row if new amendment found (new_row == True)

            if new_row == True:  # could also be if tr_type == "pos"
                # create new row; append lists
                list_amno.append(amno)
                list_pos.append(pos)

                list_pos_title.append("")
                list_pos_citation.append("")
                list_pos_recital.append("")
                list_pos_article.append("")
                list_pos_paragraph.append("")
                list_pos_subpar.append("")
                list_pos_point.append("")
                list_pos_subpoint.append("")
                list_pos_indent.append("")
                list_pos_annexno.append("")
                list_pos_part.append("")
                list_pos_annex.append("")

                list_pos_annex_num.append("")
                list_pos_annex_subnum.append("")
                list_pos_annex_alpha.append("")
                list_pos_annex_subalpha.append("")

                list_amendedpos.append(amendedpos)
                list_amtype.append(amtype)
                list_text.append(text)
                list_amendment.append(amendment)
                list_ammraw.append(amm_raw)
                list_justification.append(justification)

            # Row specific operations / Fill rows

            if tr_type == "pos":

                try:

                    if table_style == 'new-old':
                        tr_text_temp = tr.get_text('\n', strip=True)
                        tr_text_temp = tr_text_temp.replace(u'\xa0', u' ')
                        if re.search('mendment.*\n.*[0-9]', tr_text_temp) is not None:
                            tr_text_temp = tr_text_temp.replace('\n', ' ', 1)
                    else:
                        tr_text_temp = tr.get_text()


                    # Pos
                    list_amno[-1] = re.search(r'[0-9]+$', tr_text_temp.splitlines()[0].strip())[0]

                    try:
                        list_pos[-1] = tr_text_temp.splitlines()[2]
                        list_amendedpos[-1] = "\n".join(tr_text_temp.splitlines()[3:])  # get the amended act if
                    except Exception as e:
                        if re.search(r'Proposal for a', tr_text_temp.splitlines()[1]) is None:  # for the odd case where "Proposal for a regulation is not in the Position header"
                            list_pos[-1] = tr_text_temp.splitlines()[1]
                            list_amendedpos[-1] = "\n".join(tr_text_temp.splitlines()[2:])  # get the amended act if

                        else:
                            raise (e)

                    list_amtype[-1] = "new" if re.search("new", list_pos[-1]) is not None else "modify"

                except Exception as e:

                    print("\tSomething went wrong:")
                    print(tr)
                    raise e

                # Identify positions

                # @TODO do pos identification in a later step, focus on parsing the table here

                ## Cases (cf. notes file)
                # - Title
                # - Recital 27a
                # - Recital -1
                # - Article 5
                # - Paragraph?
                # - Point ba
                # - Annex

                # pos_title

                # Citations
                try:
                    list_pos_citation[-1] = re.search(r'(?<=[Cc]itation)[\s]*[0-9]{1,3}[\s]*[a-z]{0,2}', list_pos[-1])[
                        0].strip()
                except:
                    pass

                # Recitals
                try:
                    list_pos_recital[-1] = \
                    re.search(r'(?<=[Rr]ecital)[\s]*[-]*[\s]*[0-9]{1,3}[\s]*[a-z]{0,2}', list_pos[-1])[0].strip()
                except:
                    pass

                # Articles
                try:
                    list_pos_article[-1] = \
                    re.search(r'(?<=[Aa]rticle)[\s]*[-]* *[0-9]{1,3}[\s]*[a-z]{0,2}', list_pos[-1])[0].strip()

                    list_pos_article[-1] = re.sub(r'[^0-9]', "", list_pos_article[-1])

                except:
                    pass

                # Paragraphs
                try:
                    list_pos_paragraph[-1] = re.search(
                        r'(?:(?<=[Pp]aragraph)[\s]*[0-9]{1,3}[\s]*[a-z]{0,2})|(?:(first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|eleventh|twelth)(?=\s*[Pp]aragraph))',
                        list_pos[-1])[0].strip()

                    # old regex (?:(?<=[^A-Za-z][Pp]aragraph)[\s]*[0-9]{1,3}[\s]*[a-z]{0,2})|(?:(first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|eleventh|twelth)(?=\s*[Pp]aragraph))

                    if re.search(r'[a-zA-Z]{5,}', list_pos_paragraph[-1]) is not None:
                        list_pos_paragraph[-1] = str(dict_nth[list_pos_paragraph[-1]])

                    if list_pos_paragraph[-1] != "" and list_pos_article[
                        -1] == "":  # if only the paragraph is given, assume article 1

                        list_pos_article[-1] = 1

                except:
                    pass

                # Subparagraphs
                try:
                    list_pos_subpar[-1] = re.search(
                        r'(?:(?<=[Ss]ubparagraph)[\s]*[0-9]{1,3}[\s]*[a-z]{0,2})|(?:(first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|eleventh|twelth)(?=\s*[Ss]ubparagraph))',
                        list_pos[-1])[0].strip()

                    if re.search(r'([0-9a-z]{1,3})\s*([a-z]{1,3})', list_pos_subpar[-1]) is not None:
                        list_pos_subpar[-1] = re.search(r'([0-9a-z]{1,3})\s*([a-z]{1,3})', list_pos_subpar[-1])[2]

                    if re.search(r'[a-zA-Z]{5,}', list_pos_subpar[-1]) is not None:

                        list_pos_subpar[-1] = str(dict_nth[list_pos_subpar[-1]])

                    elif re.search(r'[a-zA-Z]', list_pos_subpar[-1]) is not None:

                        list_pos_subpar[-1] = str(
                            ord(list_pos_subpar[-1][-1].lower()) - 96)  # convert from alphabetic to numeric

                    if list_pos_subpar[-1] != "" and list_pos_paragraph[
                        -1] == "":  # if only the subparagraph is given, assume paragraph 1

                        list_pos_paragraph[-1] = 1

                except:
                    pass

                # Points (also subpoints, if listed as points)
                try:

                    re_point_search = re.findall(
                        r'(?<=[^A-Za-z][Pp]oint)[\s]*[-]*[\s]*(?:[0-9]{1,3}[.]*[0-9]*|[a-zA-Z]{1,2})[\s]*[a-z]{0,2}',
                        list_pos[-1])  # space before point to not capture subpoints

                    if len(re_point_search) > 1:  # if point 1 - point 1.2 style

                        if re_point_search[-2].strip() in re_point_search[
                            -1].strip():  # if point 1 - point 1.2; split into point and subpoint

                            list_pos_point[-1] = re_point_search[-2].strip()
                            list_pos_subpoint[-1] = re_point_search[-1].strip()

                            list_pos_subpoint[-1] = re.sub(r'^s*' + list_pos_point[-1], "", list_pos_subpoint[-1])

                        else:  # if point 1 - point a

                            list_pos_point[-1] = re_point_search[-2].strip()
                            list_pos_subpoint[-1] = re_point_search[-1].strip()

                    else:

                        list_pos_point[-1] = re_point_search[0].strip()

                    if (len(list_pos_point[-1]) > 1) & (is_numeric(list_pos_point[
                                                                       -1]) is False):  # check for subpoints such as "Article 1 - Paragraph 1 - point 4 a"

                        re_point_search2 = re.findall(r'(?:[-]*[0-9]|[a-z]|[A-Z])+', list_pos_point[-1])

                        if len(re_point_search2) > 1:
                            list_pos_point[-1] = re_point_search2[0]
                            list_pos_subpoint[-1] = re_point_search2[1]

                    if is_numeric(list_pos_point[-1]) is False:  # if the point position is not given in numbers

                        # discern between roman numerals and non roman numerals
                        if list_pos_point[-1].lower() in dict_roman.keys():

                            list_pos_point[-1] = str(dict_roman[list_pos_point[-1].lower()])

                        else:

                            list_pos_point[-1] = str(
                                ord(list_pos_point[-1][-1].lower()) - 96)  # convert from alphabetic to numeric
                except:
                    pass

                # Subpoints (if explicitly stated in position text)
                try:
                    if list_pos_subpoint[-1] == "":
                        list_pos_subpoint[-1] = \
                        re.search(r'(?<=[Ss]ubpoint)[\s]*(?:[0-9]{1,3}|[a-z]{1,4})[\s]*[a-z]{0,2}', list_pos[-1])[
                            0].strip()

                    if is_numeric(list_pos_point[-1]) is False:  # if the point position is not given in numbers

                        # discern between roman numerals and non roman numerals
                        if list_pos_subpoint[-1].lower() in dict_roman.keys():

                            list_pos_subpoint[-1] = str(dict_roman[list_pos_subpoint[-1].lower()])

                        else:

                            list_pos_subpoint[-1] = str(
                                ord(list_pos_subpoint[-1][-1].lower()) - 96)  # convert from alphabetic to numeric

                except:
                    pass

                # Indents

                try:
                    list_pos_indent[-1] = re.search(
                        r'(?:(?<=[Ii]ndent)[\s]*[-]*[\s]*(?:[0-9]{1,3}|[a-zA-Z]{1,3})[\s]*[a-z]{0,2})|(?:(first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|eleventh|twelth)(?=\s*indent))',
                        list_pos[-1])[0].strip()

                    if is_numeric(list_pos_subpoint[-1]) is False:  # if the point position is not given in numbers

                        if list_pos_indent[-1].lower() in dict_nth.keys():

                            list_pos_indent[-1] = str(dict_nth[list_pos_indent[-1].lower()])

                        elif list_pos_indent[-1].lower() in dict_roman.keys():

                            list_pos_indent[-1] = str(dict_roman[list_pos_indent[-1].lower()])

                        else:

                            list_pos_indent[-1] = str(
                                ord(list_pos_indent[-1][-1].lower()) - 96)  # convert from alphabetic to numeric



                except:
                    pass

                # Annexes

                try:
                    list_pos_annexno[-1] = \
                    re.search(r'(?<=[Aa][nNnNeExX]{4})[\s]*[\s]*(?:[0-9]{1,3}|[a-zA-Z]{1,4})[\s]*[a-z]{0,2}',
                              list_pos[-1])[0].strip()

                    # roman numerals or only annex
                    if is_numeric(list_pos_annexno[-1]) is False:  # if the point position is not given in numbers

                        # discern between roman numerals and non roman numerals
                        if list_pos_annexno[-1].lower() in dict_roman.keys():

                            list_pos_annexno[-1] = str(dict_roman[list_pos_annexno[-1].lower()])

                        else:

                            list_pos_annexno[-1] = str(
                                ord(list_pos_annexno[-1][-1].lower()) - 96)  # convert from alphabetic to numeric

                except:
                    pass

                try:
                    list_pos_part[-1] = \
                    re.search(r'(?<=[Pp]art)[\s]*[-]*[\s]*(?:[0-9]{1,3}|[a-zA-Z]{1,3})[\s]*[a-z]{0,2}', list_pos[-1])[
                        0].strip()

                    if is_numeric(list_pos_part[-1]) is False:  # if the point position is not given in numbers

                        # discern between roman numerals and non roman numerals
                        if list_pos_part[-1].lower() in dict_roman.keys():

                            list_pos_part[-1] = str(dict_roman[list_pos_part[-1].lower()])

                        else:

                            list_pos_part[-1] = str(
                                ord(list_pos_part[-1][-1].lower()) - 96)  # convert from alphabetic to numeric

                except:
                    pass

                try:
                    list_pos_annex[-1] = 1 if re.search(r'[Aa][nNnNeExX]{4}', list_pos[-1]) is not None else 0

                except:
                    pass

                if (list_pos_annex[-1] == 1) & (list_pos_annexno[-1] == ""):
                    list_pos_annexno[-1] = str(1)

                # Further annex-specific locations

                if list_pos_annex[-1] == 1:

                    annexposmatch = re.findall(
                        r'(?:(?:point|paragraph|[0-9])\s*(?:([0-9]{1,3})\.{0,1}([0-9]{0,3})\s*([a-z]{0,1}))|(?:(?:point|paragraph|[0-9])\s*((?:[a-z]{1}|[0-9]{0,2}))\s*([a-z0-9]{0,1})))+',
                        list_pos[-1])

                    if annexposmatch is not None:

                        for match in annexposmatch:
                            list_pos_annex_num[-1] = match[0] if (match[0] != "" and list_pos_annex_num[-1] == "") else \
                            list_pos_annex_num[-1]  # Regex group 0 captures numbers
                            list_pos_annex_subnum[-1] = match[1] if (
                                    match[1] != "" and list_pos_annex_subnum[-1] == "") else list_pos_annex_subnum[
                                -1]  # captures subnumbers (1.X)
                            list_pos_annex_alpha[-1] = match[2] if (
                                    match[2] != "" and list_pos_annex_alpha[-1] == "") else list_pos_annex_alpha[
                                -1]  # captures alphabetic (x)
                            list_pos_annex_alpha[-1] = match[3] if (
                                    match[3] != "" and list_pos_annex_alpha[-1] == "") else list_pos_annex_alpha[
                                -1]  # captures alphabetic (x)
                            list_pos_annex_subalpha[-1] = match[4] if (
                                    match[4] != "" and list_pos_annex_subalpha[-1] == "") else list_pos_annex_subalpha[
                                -1]  # captures subalphabetic (ax)

                    # Convert alphabetic
                    list_pos_annex_alpha[-1] = str(ord(list_pos_annex_alpha[-1][-1].lower()) - 96) if \
                    list_pos_annex_alpha[-1] != "" else list_pos_annex_alpha[
                        -1]  # convert from alphabetic to numeric
                    list_pos_annex_subalpha[-1] = str(ord(list_pos_annex_subalpha[-1][-1].lower()) - 96) if \
                    list_pos_annex_subalpha[-1] != "" else list_pos_annex_subalpha[
                        -1]  # convert from alphabetic to numeric


            elif tr_type == "justification":

                list_justification[-1] = tr.get_text()

            elif tr_type == "amendment" or tr_type == "amendment_add" or tr_type == "amm_raw":

                # separate left (to be amended) and right column (amendment text)

                # remove headers (if present)

                # re.sub(r'')

                td_count = 0




                # old way of identifying columns
                for td in tr.find_all('td'):

                    if td.find('td') is None:  # lowest level td-tags only

                        td_width = None
                        td_width_unit = None

                        # if class w-X is present, set td_width to X and td_width_unit to % (default)
                        if td.has_attr('class') and re.search(r'w-[0-9]+', td['class'][0]) is not None:

                            try:
                                td_width = int(re.search(r'(?<=w-)[0-9]+', td['class'][0]).group(0))
                                td_width_unit = '%'
                            except:
                                td_width = None
                                td_width_unit = None

                        if td_width is None or td_width_unit is None:
                            try:
                                td_width_code = re.search(r'([0-9]+(?:\.[0-9]+)*)([%a-z]+)*', td['width'])  # try to access attribute directly
                                td_width = float(td_width_code.group(1))
                                td_width_unit = td_width_code.group(2)


                            except:

                                try:
                                    td_width_code = re.search(r'(?<=width:)([0-9]+(?:\.[0-9]+)*)([%a-z]+)*', td['style'])  # if above fails, try to find width in style code
                                    td_width = float(td_width_code.group(1))
                                    td_width_unit = td_width_code.group(2)
                                except:
                                    td_width = 0  # if above fails, set td_width to 0 (skip)
                                    td_width_unit = None

                            # check for defective (layout) rows
                            if td_width_unit is not None and td_width == 0.0 and table_style in ['old', 'old-old']:
                                defective_row = True

                                # check if it is an actual column or just a separator (row)
                                if len(td.find_parent('tr').find_all('td')) < 3:
                                    continue
                                else:
                                    if td_width_unit == 'pt':
                                        td_width = 200
                                    elif td_width_unit == '%':
                                        td_width = 50

                        if td_width_unit is not None and td_width is not None and ((td_width_unit == "%" and td_width > 15 and td_width < 100) or (td_width_unit == "pt" and td_width > 150 and td_width < 250)):  # make sure its not a separator column

                            td_count = td_count + 1

                            if divmod(td_count, 2)[1] == 0:  # right column

                                list_amendment[-1] = str(list_amendment[-1]) + "\n" + re.sub('^[\s]*Amendment[\s]*', "",
                                                                                             td.get_text().strip())

                            else:  # left column

                                # remove 'Text proposed by Commission' or 'Present Text'

                                list_text[-1] = str(list_text[-1]) + "\n" + re.sub(
                                    '(?:^[\s]*Text proposed by the [Cc]ommission[\s]*)|(?:^[\s]*Present [Tt]ext[\s]*)',
                                    "", td.get_text().strip())

                    elif tr_type == "amm_raw":

                        list_ammraw[-1] = str(list_ammraw[-1]) + "\n" + td.get_text().strip()

                if re.search(r'(?<=[Aa]rticle)[\s]*-[0-9]{1,3}', list_pos[
                    -1]) is not None:  # if Article pos includes a minus, remove it from the amendment text (causes confusion for further procesing)

                    list_amendment[-1] = re.sub(r'^\s*[Aa]rticle[\s]*-[0-9]{1,3}[\s]*[a-z]{0,1}', "",
                                                list_amendment[-1], flags=re.MULTILINE)

                if re.search(r'citation', list_pos[-1], flags=re.IGNORECASE) and (
                    "amendment" in tr_type):  # if amendment is a citation, remove the - from the beginning of the line

                    list_amendment[-1] = re.sub(r'^[^\S\n\r]*\-\s*', "", list_amendment[-1], flags=re.MULTILINE)

        # TODO return an object of type AmendmentList here
        data = pd.DataFrame(list(zip(list_amno, list_amtype, list_pos,
                                     list_pos_title, list_pos_citation, list_pos_recital, list_pos_article,
                                     list_pos_paragraph, list_pos_subpar, list_pos_point, list_pos_subpoint,
                                     list_pos_indent, list_pos_annexno, list_pos_part, list_pos_annex,
                                     list_pos_annex_num, list_pos_annex_subnum, list_pos_annex_alpha,
                                     list_pos_annex_subalpha,
                                     list_amendedpos, list_text, list_amendment, list_ammraw, list_justification)),
                            columns=["no", "type", "pos",
                                     "pos_title", "pos_citation", "pos_recital", "pos_article", "pos_paragraph",
                                     "pos_subpar", "pos_point", "pos_subpoint", "pos_indent", "pos_annexno", "pos_part",
                                     "pos_annex",
                                     "pos_annex_num", "pos_annex_subnum", "pos_annex_alpha", "pos_annex_subalpha",
                                     "amendedpos", "text", "amendment", "amm_raw", "justification"]).to_dict('records')

        self.amendments = data




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
