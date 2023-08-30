from spacy.tokens import Doc
from amendmerge.amendment import Amendment
from eucy.modify import modify_doc
import os
import warnings

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


# High-level data Source class that has the required methods for the pipeline
# to work with it
class DataSource:

    def __init__(self, source, type_ = None, format = None, subtype = None, subformat = None, law = None, amendments = [], **kwargs):

        self.source = None
        self.source_raw = None
        self.type_ = type_
        self.source_format = format

        self.source_subtype = subtype
        self.law = law

        self.amendments = amendments

        if hasattr(source, 'read'):  # It's a file-type object.
            source = source.read()
        elif len(source) <= 256:
            is_file = False
            try:
                is_file = os.path.exists(source)
            except Exception as e:
                pass
            if is_file:
                raise ValueError('source must be a file-like object or a string containing e.g. HTML markup, not a path')

        self.source = source

        if self.source_format is None:
            self.source_format = self.get_format()

        if self.type is None:
            self.source_type = self.get_type()

        if self.source_subtype is None:
            self.source_subtype = self.get_subtype()

        if self.source_raw is None:
            self.source_raw = self.source

        # check if there is a specific reader for this source type
        if self.source_type is not None:
            reader = getattr(self, 'read_' + self.source_type)
            if reader is None:
                warnings.warn('No reader for source type ' + self.source_type)
            else:
                self.source = reader()

        # parse the source
        if self.source_format is not None:
            parser = getattr(self, 'parse_' + self.source_format)
            if parser is None:
                warnings.warn('No parser for source format ' + self.source_format)
            else:
                self.source = parser()

        self.parse()

    def get_format(self):
        return None

    def get_subformat(self):
        return None

    def get_type(self):
        return None

    def get_subtype(self):
        return None

    def read_text(self):
        return self.source

    def read_html(self):

        assert isinstance(self.source_raw, str)

        from bs4 import BeautifulSoup
        bs = BeautifulSoup(self.source_raw, 'html.parser')

        return bs

    def read_doc(self):
        raise NotImplementedError

    def read_pdf(self):
        raise NotImplementedError

    def parse(self):

        """ Generic parsing function to be implemented by subclasses.
            Should parse the source and set the following attributes:
            - self.amendments: a list of amendments
        """


        raise NotImplementedError('parse() must be implemented by subclasses of DataSource')

    def amendments(self):
        return self.amendments

