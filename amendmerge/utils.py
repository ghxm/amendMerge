import warnings

from bs4 import BeautifulSoup, element
import os
import re
from collections import OrderedDict
from word2number import w2n
import difflib

def remove_new_element_spans (spans):
    return [s for s in spans if not is_new_element_span(s)]

def is_new_element_span (span):
    return (span.has_extension('new_element') and span._.new_element)

def remove_new_article_element_spans (article_elements):

    old_article_elements = {
        'pars': [],
        'subpars': [],
        'points': [],
        'indents': [],
    }

    for par_i, par in enumerate(article_elements['pars']):
        if is_new_element_span(par):
            continue
        else:
            old_article_elements['pars'].append(par)
            old_article_elements['subpars'].append([])
            old_article_elements['points'].append([])
            old_article_elements['indents'].append([])

        for subpar_i, subpar in enumerate(article_elements['subpars'][par_i]):
            if is_new_element_span(subpar):
                continue
            else:
                old_article_elements['subpars'][par_i].append(subpar)
                old_article_elements['points'][par_i].append([])
                old_article_elements['indents'][par_i].append([])



            for point_i, point in enumerate(article_elements['points'][par_i][subpar_i]):
                if is_new_element_span(point):
                    continue
                else:
                    old_article_elements['points'][par_i][subpar_i].append(point)

            for indent_i, indent in enumerate(article_elements['indents'][par_i][subpar_i]):
                if is_new_element_span(indent):
                    continue
                else:
                    old_article_elements['indents'][par_i][subpar_i].append(indent)

    return old_article_elements


def clean_html_text(text):

    if not isinstance(text, str):
        return text

    # remove linebreaks where unnecessary
    text = re.sub(r'\n(?![\r\n])', ' ', text)

    # remove double spaces
    text = re.sub(r'[ ]+', ' ', text)

    return text.strip()


def is_number_word(s):
    try:
        w2n.word_to_num(s.lower())
        return True
    except ValueError:
        return False

def number_word_to_int(s):
    if not is_number_word(s):
        raise ValueError("Input is not a number word")
    return w2n.word_to_num(s.lower())

def is_number_word_ordinal(s):
    try:
        number_word_ordinal_to_int(s.lower())
        return True
    except ValueError:
        return False



ordinal_cardinal = {
    'first': 'one',
    'second': 'two',
    'third': 'three',
    'fourth': 'four',
    'fifth': 'five',
    'sixth': 'six',
    'seventh': 'seven',
    'eighth': 'eight',
    'ninth': 'nine',
    'tenth': 'ten',
    'eleventh': 'eleven',
    'twelfth': 'twelve',
}

def ordinal_to_cardinal(s):

    def replace_suffix(match):
        return match.group(1)

    for key in ordinal_cardinal:
        if key in s:
            return s.replace(key, ordinal_cardinal[key])

    s = re.sub(r'\b(\w+)(st|nd|rd|th)\b', replace_suffix, s, flags=re.IGNORECASE)
    return s

def number_word_ordinal_to_int(s):

    return w2n.word_to_num(ordinal_to_cardinal(s.lower()))


dict_nth = {
    'first': 1,
    'second': 2,
    'third': 3,
    'fourth': 4,
    'fifth': 5,
    'sixth': 6,
    'seventh': 7,
    'eighth': 8,
    'ninth': 9,
    'tenth': 10,
    'eleventh': 11,
    'twelfth': 12,
    'thirteenth': 13,
    'fourteenth': 14,
    'fifteenth': 15,
    'sixteenth': 16,
    'seventeenth': 17,
    'eighteenth': 18,
    'nineteenth': 19,
    'twentieth': 20,
    'twenty-first': 21,
    'twenty-second': 22,
    'twenty-third': 23,
    'twenty-fourth': 24,
    'twenty-fifth': 25
}

dict_roman = {
    'i': 1,
    'ii': 2,
    'iii': 3,
    'iv': 4,
    'v': 5,
    'vi': 6,
    'vii': 7,
    'viii': 8,
    'ix': 9,
    'x': 10,
    'xi': 11,
    'xii': 12,
    'xiii': 13,
    'xiv': 14,
    'xv': 15,
    'xvi': 16,
    'xvii': 17,
    'xviii': 18,
    'xix': 19,
    'xx': 20,
    'xxi': 21,
    'xxii': 22,
    'xxiii': 23,
    'xxiv': 24,
    'xxv': 25
}


def letter_to_int (letter):
    letter = letter.lower().strip()
    return ord(letter)-96

def int_to_letter(num):
    return chr (96+num)


def roman_to_int(s):

    s = s.upper()

    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    num = 0

    for i in range (len (s) - 1):
        if roman[s[i]] < roman[s[i + 1]]:
            num += roman[s[i]] * -1
            continue

        num += roman[s[i]]

    num += roman[s[-1]]

    return num




def int_to_roman(num):

    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])


def is_roman (s):
    return re.match(r'(?:(?-i:[IVXLCDM]+)|[IVXLCDM]{3,6})$', s, re.IGNORECASE) is not None


def is_numeric (s):
    try:
        float(s)
        return True
    except:
        return False

def to_numeric (s):

    if is_numeric(s):
        try:
            return int(s)
        except:
            return float(s)
    elif s in dict_nth:
        return dict_nth[s]
    elif s in dict_roman:
        return dict_roman[s]
    elif is_roman(s):
        return roman_to_int(s)
    elif is_number_word_ordinal(s):
        return number_word_ordinal_to_int(s)
    elif is_number_word(s):
        return number_word_to_int(s)
    elif s.isupper() and len(s.strip()) == 1:
        return letter_to_int(s)
    else:
        raise ValueError("Cannot convert {} to numeric".format(s))


def _determine_input_format (input):
    if isinstance(input, str):
        # check if string is html code
        if re.search("<(.)>.?|<(.*) />", input.strip()[0:1000]) is not None:
            return "html"
        # check if path
        elif os.path.exists(input):
            return "path"
        else:
            return "text"
    elif isinstance(input, (BeautifulSoup, element.Tag)):
        return "html-bs"


def combine_consecutive_tags(bs_or_list, tag_name, match_attributes = [], find_attributes = {}):

    if isinstance(bs_or_list, BeautifulSoup):
        bs = bs_or_list
        tags = bs.find_all(tag_name, find_attributes)

    elif isinstance(bs_or_list, list):
        tags = bs_or_list

    else:
        raise ValueError("bs_or_list must be of type BeautifulSoup or list")

    if len(tags) == 0:
        return bs_or_list


    for tag in tags:
        if tag.decomposed:
            continue
        for s_tag in tag.find_next_siblings():
            if s_tag.name == tag.name and len(match_attributes) > 0:
                if all([s_tag.get(attr) == s_tag.get(attr) for attr in match_attributes]):

                    try:
                        new_string = tag.string + s_tag.string
                    except:
                        new_string = tag.text + s_tag.text

                    if new_string not in tag.find_parent().text: # because some tags (span) can occur in the same parent inbetween text
                        break

                    tag.string = new_string
                    s_tag.decompose()
            else:
                break


    if isinstance(bs_or_list, list):
        return [e for e in bs_or_list if not e.decomposed]

    if isinstance(bs_or_list, BeautifulSoup):

        return bs_or_list


def html_parser(order=['lxml', 'html.parser']):

    # check if installed and return the first one that is
    for parser in order:
        try:
            bs = BeautifulSoup('', parser)

            if parser != 'lxml':

                warnings.warn('Using {} as html parser. Install lxml for better performance.'.format(parser))

            return parser
        except:
            pass


def bs_set(elements):

    if not isinstance(elements, list) and not isinstance(elements, element.ResultSet):
        raise ValueError('elements must be either a list or a bs4.element.ResultSet')

    elements_unique = []
    for el in elements:
        if el.get('seen'):
            continue
        # give each element a seen attribute
        el['seen'] = True
        elements_unique.append(el)

    # remove seen attribute to not interfere with other functions
    for el in elements:
        del el['seen']

    return elements_unique


def combine_matches_to_string(matches, add_space=True, keep_inbetween=False):
    if not isinstance(matches, list):
        raise ValueError("matches must be a list")

    if len(matches) == 0:
        return ""

    text = matches[0].string
    matches = [m.span() for m in matches]
    if not matches:
        return ""

    combined = ""
    last_end = 0

    for start, end in matches:
        if keep_inbetween:
            combined += text[last_end:end]
        else:
            if start >= last_end:
                combined += text[start:end]
            else:
                combined += text[last_end:end]

        if add_space and not keep_inbetween:
            combined += " "

        last_end = end

    #if keep_inbetween:
    #    combined += text[last_end:]

    return combined.strip() if add_space and not keep_inbetween else combined


def determine_text_td_num(tr):

    """Determine the number of columns in a html table row."""

    tds = tr.find_all('td')
    if len(tds) > 0:
        return len([td for td in tds if len(td.get_text(strip=True)) > 0])
    else:
        ths = tr.find_all('th')
        if len(ths) > 0:
            return len([th for th in ths if len(th.get_text(strip=True)) > 0])
        else:
            return 0


# Modify the function to accept file contents directly as strings rather than file paths.
def save_differences_from_strings(file1_content, file2_content, output_path):
    # Split the file contents into lines
    file1_lines = file1_content.splitlines(keepends=True)
    file2_lines = file2_content.splitlines(keepends=True)

    # Create a Differ object
    differ = difflib.Differ()

    # Calculate the difference
    diff = list(differ.compare(file1_lines, file2_lines))

    # if the output path dir does not exist, create it
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    # Write the differences to the output file
    with open(output_path, 'w') as file_out:
        for line in diff:
            file_out.write(line)

    return output_path

