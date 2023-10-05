#
# position_elements = {
#     'title': 'title',
#     'citation': r'(?<=[Cc]itation)[\s]*[0-9]{1,3}[\s]*[a-z]{0,2}',
#     'recital': r'(?<=[Rr]ecital)[\s]*[-]*[\s]*[0-9]{1,3}[\s]*[a-z]{0,2}',
#     'article': r'(?<=[Aa]rticle)[\s]*[-]* *[0-9]{1,3}[\s]*[a-z]{0,2}',
#     'paragraph': r'(?:(?<=[Pp]aragraph)[\s]*[0-9]{1,3}[\s]*[a-z]{0,2})|(?:(first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|eleventh|twelth)(?=\s*[Pp]aragraph))',
#     'subparagraph': r'(?:(?<=[Ss]ubparagraph)[\s]*[0-9]{1,3}[\s]*[a-z]{0,2})|(?:(first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|eleventh|twelth)(?=\s*[Ss]ubparagraph))',
#     'point': r'(?<=[^A-Za-z][Pp]oint)[\s]*[-]*[\s]*(?:[0-9]{1,3}[.]*[0-9]*|[a-zA-Z]{1,2})[\s]*[a-z]{0,2}',
#     'subpoint': r'(?<=[Ss]ubpoint)[\s]*(?:[0-9]{1,3}|[a-z]{1,4})[\s]*[a-z]{0,2}',
#     'indent': r'(?:(?<=[Ii]ndent)[\s]*[-]*[\s]*(?:[0-9]{1,3}|[a-zA-Z]{1,3})[\s]*[a-z]{0,2})|(?:(first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth|eleventh|twelth)(?=\s*indent))',
#     'annex': r'(?<=[Aa][nNnNeExX]{4})[\s]*[\s]*(?:[0-9]{1,3}|[a-zA-Z]{1,4})[\s]*[a-z]{0,2}',
#     'part': r'(?<=[Pp]art)[\s]*[-]*[\s]*(?:[0-9]{1,3}|[a-zA-Z]{1,3})[\s]*[a-z]{0,2}',
#     'annex_position': r'(?:(?:point|paragraph|[0-9])\s*(?:([0-9]{1,3})\.{0,1}([0-9]{0,3})\s*([a-z]{0,1}))|(?:(?:point|paragraph|[0-9])\s*((?:[a-z]{1}|[0-9]{0,2}))\s*([a-z0-9]{0,1})))+',
# }

position_elements = {
    'title': r'(?P<element>[Tt]itle)',
    'citation': r'(?P<element>[Cc]itation)',
    'recital': r'(?P<element>[Rr]ecital)',
    'article': r'(?P<element>[Aa]rticle)',
    'paragraph': r'(?P<element>\b[Pp]aragraph)',
    'subparagraph': r'(?P<element>[Ss]ubparagraph)',
    'point': r'(?P<element>\b[Pp]oint)',
    'subpoint': r'(?P<element>[Ss]ubpoint)',
    'indent': r'(?P<element>[Ii]ndent)',
    'annex': r'(?P<element>[Aa][nNnNeExX]{4})',
    'part': r'(?P<element>[Pp]art)',
    #'annex_position': r'(?P<element>point|paragraph)',
}


base_numbers = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven',
                'twelve', 'thir', 'four', 'fif', 'six', 'seven', 'eight', 'nine']
tens = ['twen', 'thir', 'for', 'fif', 'six', 'seven', 'eigh', 'nine']

written_numbers = r'\b(?:' + '|'.join(base_numbers) + r')\b'
written_tens = r'\b(?:' + '|'.join(tens) + r')ty\b'
written_compounds = r'\b(?:' + '|'.join(tens) + r')ty[- ]?(?:' + '|'.join(base_numbers[1:10]) + r')\b'

ordinals_base = r'\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\b'
ordinals_tens = r'\b(?:twen|thir|for|fif|six|seven|eigh|nine)tieth\b'
ordinals_compounds = r'\b(?:twen|thir|for|fif|six|seven|eigh|nine)tieth[- ]?(?:' + '|'.join(base_numbers[1:10]) + r')\b'

position_numbers = {
    'roman': r'\b(?:(?-i:[IVXLCDM])|([IVXLCDM]){3,6})\b',
    'arabic': r'\-*\d+(\.\d+)?(?:[a-zA-Z]*\s*[a-z]{0,2}){0,1}(?=[^a-z]|$)',
    'word': f'{written_numbers}|{written_tens}|\\b(?:' + '|'.join(tens) + r')[- ]?ty[- ]?(?:' + '|'.join(
        base_numbers[1:10]) + r')\b',
    'word_ordinal': f'{ordinals_base}|{ordinals_tens}|\\b(?:twen|thir|for|fif|six|seven|eigh|nine)tieth[- ]?(?:' + '|'.join(
        base_numbers[1:10]) + r')\b',
    'letters': r'(?<=[\s0-9])(?:\(-*[a-zA-Z]{1,2}\)|-*[a-zA-Z]{1,2})\s?(?:\(-*[a-zA-Z]{1,2}\)|-*[a-zA-Z]{1,2})*'
}

position_numbers['all'] = f"{position_numbers['roman']}|{position_numbers['arabic']}|{position_numbers['word']}|{position_numbers['word_ordinal']}"
position_numbers['all_w_letters'] = position_numbers['all'] + f"|{position_numbers['letters']}"

position_elements_numbers = {}

numbers_pre = '(?P<num_pre>' + position_numbers['word_ordinal'] + ')*\s*'

for element in position_elements:
    if element in ['paragraph', 'subparagraph', 'point', 'subpoint', 'indent']:
        numbers_post =  '\s*-*?\s*' + '(?P<num_post>' + position_numbers['all_w_letters'] + ')*'
    else:
        numbers_post =  '\s*-*?\s*' + '(?P<num_post>' + position_numbers['all'] + ')*'

    position_elements_numbers[element] = numbers_pre + position_elements[element] + numbers_post +  '(?P<new>\s*.{,3}\s*\(*new\)*)*'

