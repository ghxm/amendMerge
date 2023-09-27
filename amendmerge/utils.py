import warnings

from bs4 import BeautifulSoup, element
import os
import re
from collections import OrderedDict


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


def is_numeric (s):
    try:
        float(s)
        return True
    except:
        return False



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
