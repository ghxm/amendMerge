

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
    ("Article 4 – paragraph 2 – point a – point i",
     {
            'article': 4,
            'paragraph': 2,
            'point': 'a',
            'subpoint': 'i' # TODO: subpoint
        }),
    ("(Amendment 3)\nThirteenth recital",
        {
            'recital': 13
        }),
    ("Twenty-first recital",
        {
            'recital': 21
        }),
    ("Twenty first recital",
     {
         'recital': 21
     }),
    ("Article 2, point (e a) (new)",
     {
         'article': 2,
         'point': '(e a)',
         'new': True
     }),
    ("Article 2, points (v e) and (v f) (new)",
     {
         'article': 2,
         'point': '(v e) and (v f)',
            'new': True
        }),
    ("Article 12, paragraphs 1 and 2",
     {
         'article': 12,
         'paragraph': '1 and 2'
     }),
    ("Annex V – Part B – paragraph 1 – table – row 2 b (new)",
     {
            'annex': 5,
            'part': 2,
            'paragraph': 1,
            'table': True,
            'row': '2 b',
            'new': True
        }),
    ("Article 1, fourth paragraph yaday yada",
     {
         'article': 1,
         'paragraph': 4
     }),
    ("Annex, Part A, point 1, subparagraph 1 a (new)",
     {
         'annex': 0,
         'part': 1,
         'point': 1,
         'subparagraph': '1 a',
         'new': True}),
    ("Annex, Part B, points 2 a and 2 b (new)",
     {
         'annex': 0,
         'part': 2,
         'point': '2 a and 2 b',
         'new': True}),
    ("Article 3, paragraph 2, points (a), (b) and (c)",
     {
         'article': 3,
         'paragraph': 2,
         'point': '(a), (b) and (c)'}),

]



@pytest.mark.parametrize('position_text_dict', position_texts_dicts)
def test_position_parsing_from_text(position_text_dict):

    position_text = position_text_dict[0]
    position_dict = position_text_dict[1]

    assert HtmlAmendmentTableParser._parse_position(position_text) == position_dict

def test_position_parsing_from_html():

    # TODO

    pass

