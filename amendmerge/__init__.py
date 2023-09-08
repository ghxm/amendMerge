from spacy.tokens import Doc
from amendmerge.amendment import Amendment
from eucy.modify import modify_doc
import os
import warnings
from amendmerge.utils import html_parser

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

    """Base class for all data sources."""

    def __init__(self, source,*, type = None, format = None, subtype = None, subformat = None, law = None, amendments = [], **kwargs):

        """

        Parameters
        ----------
        source : str or file-like object
            The source of the data.
        type : str, optional
            The type of the data source. Defaults to None.
        format : str, optional
            The format of the data source. Defaults to None.
        subtype : str, optional
            The subtype of the data source. Defaults to None.
        subformat : str, optional
            The subformat of the data source. Defaults to None.
        law : spacy.tokens.Doc, optional
            The law to be amended. Defaults to None.
        amendments : list, optional
            A list of amendments. Defaults to [].
        kwargs : dict, optional
            Additional keyword arguments. Defaults to {}.


        """

        self.source = None
        self.source_raw = None
        self.type = type
        self.subtype = subtype
        self.format = format
        self.subformat = subformat

        self.source_subtype = subtype
        self.law = law

        self.amendments = amendments

        from bs4 import Tag

        parsed_classes = (Tag) # classes that are already parsed and don't need to be parsed again

        if isinstance(source, parsed_classes):
            self.source_raw = str(source)
            self.source = source
        else:

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

            if self.format is None:
                self.format = self.get_format()

            if self.type is None:
                self.type = self.get_type()

            if self.subtype is None:
                self.subtype = self.get_subtype()

            if self.source_raw is None:
                self.source_raw = self.source

            # check if there is a specific reader for this source format
            if self.format is not None:
                reader = getattr(self, 'read_' + self.format)
                if reader is None:
                    warnings.warn('No reader for source type ' + self.format)
                else:
                    self.source = reader()


        # add all remaining keyword arguments as attributes if they don't exist yet
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

        self.parse()

    def get_format(self):
        return self.format

    def get_subformat(self):
        return self.subformat

    def get_type(self):
        return self.type

    def get_subtype(self):
        return self.subtype

    def read_text(self):
        return self.source

    def read_html(self):

        assert isinstance(self.source_raw, str)

        from bs4 import BeautifulSoup
        bs = BeautifulSoup(self.source_raw, html_parser())

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




class Html:

    def get_format(self):
        return 'html'
