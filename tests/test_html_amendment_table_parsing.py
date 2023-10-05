

import pytest
from amendmerge.amendment_table.html import HtmlAmendmentTableParser

position_texts_dicts = [
    ("Proposal for a regulation – amending act\nTitle",
    {
        'title': 0
    }),
    ("Proposal for a regulation – amending act\nRecital 1",
    {
        'recital': 1
    },
    "Proposal for a regulation – amending act\nArticle 1 – point 5",
    {
        'article': 1,
        'point': 5
    }),
    ("Proposal for a regulation – amending act\nArticle 1 – point 5 subparagraph 2",
    {
        'article': 1,
        'point': 5,
        'subparagraph': 2
    }),
    ("Proposal for a regulation – amending act\nArticle 1 – point 5 subparagraph 2 indent 1",
    {
        'article': 1,
        'point': 5,
        'subparagraph': 2,
        'indent': 1
    }),
    ("Proposal for a regulation – amending act\nAnnex",
    {
        'annex': 0
    }),
    ("Amendment 48\nArticle 18, subparagraph 1 a (new)",
    {
        'article': 18,
        'subparagraph': '1 a',
        'new': True
    }),
    ("Article 3 – paragraph 1 – point aa (new)",
     {
            'article': 3,
            'paragraph': 1,
            'point': 'aa',
            'new': True
        }),
    ("Article 3 – paragraph 1 – point an a (new)",
     {
            'article': 3,
            'paragraph': 1,
            'point': 'an a',
            'new': True
        }),

]



@pytest.mark.parametrize('position_text_dict', position_texts_dicts)
def test_position_parsing_from_text(position_text_dict):

    position_text = position_text_dict[0]
    position_dict = position_text_dict[1]

    assert HtmlAmendmentTableParser._parse_position(position_text) == position_dict

def test_position_parsing_from_html():

    # TODO

    pass