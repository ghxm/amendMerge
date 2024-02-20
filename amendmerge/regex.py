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
    'article': r'(?P<element>[Aa]rticle[s]*)',
    'paragraph': r'(?P<element>\b[Pp]aragraph[s]*)',
    'subparagraph': r'(?P<element>[Ss]ubparagraph[s]*)',
    'point': r'(?P<element>\b[Pp]oint[s]*)',
    'subpoint': r'(?P<element>[Ss]ubpoint[s]*)',
    'indent': r'(?P<element>[Ii]ndent[s]*)',
    'annex': r'(?P<element>[Aa][nNnNeExX]{4}[es]*)',
    'part': r'(?P<element>[Pp]art[s]*)',
    'row': r'(?P<element>[Rr]ow[s]*)',
    #'annex_position': r'(?P<element>point|paragraph)',
}

# Existing base numbers and tens
base_numbers = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thir', 'four', 'fif', 'six', 'seven', 'eight', 'nine']
tens = ['twen', 'thir', 'for', 'fif', 'six', 'seven', 'eigh', 'nine']

# Existing written numbers
written_numbers = r'\b(?:' + '|'.join(base_numbers) + r')\b'
written_tens = r'\b(?:' + '|'.join(tens) + r')ty\b'
written_compounds = r'\b(?:' + '|'.join(tens) + r')ty[- ]?(?:' + '|'.join(base_numbers[1:10]) + r')\b'

# Existing ordinals
ordinals_base = r'\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\b'
ordinals_teens = r'\btwelfth\b|\b(?:thir|for|fif|six|seven|eigh|nine)teenth\b'
ordinals_tens = r'\b(?:twen|thir|for|fif|six|seven|eigh|nine)tieth\b'

# Updated ordinals_compounds to capture "twenty-first" etc.
ordinals_compounds = r'\b(?:' + '|'.join(tens) + r')tieth[- ]?(?:' + '|'.join(base_numbers[1:10]) + r')\b|\b(?:' + '|'.join(tens) + r')ty[- ](?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth)\b'

article_paragraph_indicator = '\(\s*[0-9]+[a-zA-Z]*\s*\)'

position_numbers = {
    'roman': r'\b(?:(?-i:[IVXLCDM])|([IVXLCDM]){3,6})\b',
    'arabic': r'\-*\d+(\.\d+)?(?:[a-zA-Z]*\s*[a-z]{0,2}){0,1}(?:\(?\s*[0-9]+[a-zA-Z]*\s*\)?)*(?=[^a-z]|$)',
    'word': f'{written_numbers}|{written_tens}|\\b(?:' + '|'.join(tens) + r')[- ]?ty[- ]?(?:' + '|'.join(
        base_numbers[1:10]) + r')\b',
    'word_ordinal': f'{ordinals_base}|{ordinals_teens}|{ordinals_tens}|{ordinals_compounds}',
    #'single_cap_letter': r'\b[A-Z](?=[^A-Za-z])',
    'letters': r'(?<=[^a-z])(?:\(\s*[a-zA-Z]\s*\)|\(\s*[a-zA-Z]\s+[a-zA-Z]\s*\)|-*[a-zA-Z]{1,2})(?=[^a-z]|$)'
}

position_numbers['all'] = f"{position_numbers['roman']}|{position_numbers['arabic']}|{position_numbers['word']}|{position_numbers['word_ordinal']}"
position_numbers['all_w_letters'] = position_numbers['all'] + f"|{position_numbers['letters']}"

position_numbers['all_post'] =  f"{position_numbers['roman']}|{position_numbers['arabic']}|{position_numbers['word']}"
position_numbers['all_w_letters_post'] = position_numbers['all_post'] + f"|{position_numbers['letters']}"

position_elements_numbers = {}

numbers_pre = '(?P<num_pre>' + position_numbers['word_ordinal'] + ')*\s*'

for element in position_elements:
    if element in ['paragraph', 'subparagraph', 'point', 'subpoint', 'indent', 'part']:
        numbers_post = '(?P<num_post>\(?\s*[a-zA-Z]\s+[a-zA-Z]\s*\)?|\(?' + position_numbers['all_w_letters_post'] + r'\)?)'
        numbers_post_post = ''
    elif element in ['article']:
        # account for cases like Article 1(7a)
        numbers_post = '(?P<num_post>' + position_numbers['all_post'] + '(?:\(?\s*[0-9]+[a-zA-Z]*\s*\)?))*'
        numbers_post_post = '(?P<num_post_post>[\s\(]+\s*[0-9a-zA-Z]{1,2}\s*[\s\)]+)*'
    else:
        numbers_post = '(?P<num_post>' + position_numbers['all_post'] + ')*'
        numbers_post_post = ''

    position_elements_numbers[element] = numbers_pre + position_elements[element] +'\s*-*?\s*' + r'((?:' +  numbers_post + r'(?:\s*,\s*|\s+and\s+)?)+)*\s*' + numbers_post_post +  '(?P<new>\s*.{,3}\s*\(*new\)*)*'



legislative_resolution_title = r'draft.*resolution|legislative.*resolution|draft\s*decision|legislative\s*proposal'


procedure_reference = r'[0-9]{4}\/[0-9]+[A-Z]{0,1}\([A-Z]{2,4}\)'