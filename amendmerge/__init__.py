from spacy.tokens import Doc
from amendmerge.amendment import Amendment
from eucy.modify import modify_doc

def amend_law(doc, amendments, modify_iteratively = False):
    """
    Amend a law with a list of amendments.

    Parameters
    ----------
    doc : spacy.tokens.Doc
        The law to be amended.
    amendments : list
        A list of amendments.

    Returns
    -------
    spacy.tokens.Doc
        The amended law.
    """

    assert isinstance(doc, Doc)
    assert isinstance(amendments, list)

    for amendment in amendments:
        assert isinstance(amendment, Amendment)

        amendment.apply(doc, modify = modify_iteratively)

    if not modify_iteratively:
        doc = modify_doc(doc)

    return doc
