from spacy.tokens import Doc
from amendmerge import DataSource
from amendmerge.ep_report import EpReport
from amendmerge.resolution import Resolution
from amendmerge.amendment import Amendment, AmendmentList
import os
import warnings
from amendmerge.utils import html_parser

def amend_law(doc, amendments, modify_iteratively = False, return_doc = False):

    """
    Amend a law with a list of amendments.

    Parameters
    ----------
    doc : spacy.tokens.Doc
        The law to be amended.
    amendments : Report, Resolution, Amendment, list, AmendmentList
        A list of amendments or a single amendment or a Report or Resolution object containing amendments.

    Returns
    -------
    spacy.tokens.Doc
        The amended law.
    """

    from eucy.modify import modify_doc

    amended_text = None
    resolution = None

    assert isinstance(doc, Doc)

    if isinstance(amendments, DataSource):
        if isinstance(amendments, Resolution):
            resolution = amendments

            try:
                amendments = amendments.get_amendments()
            except Exception as e:
                amendments = None
        elif isinstance(amendments, EpReport):
            resolution = amendments.get_ep_draft_resolution()
            try:
                amendments = resolution.get_amendments()
            except Exception as e:
                amendments = None
    elif isinstance(amendments, Amendment):
        amendments = [amendments]
    elif isinstance(amendments, (list, AmendmentList)):
        pass
    else:
        raise TypeError('amendments must be a Report, Resolution, an Amendment, a list of Amendments, or an AmendmentList')

    if amendments:
        for amendment in amendments:
            assert isinstance(amendment, Amendment)

            amendment.apply(doc, modify = modify_iteratively)
    elif resolution:
        if resolution.amendment_type == 'amendments_text':
            amended_text = resolution.amended_text
        else:
            warnings.warn('No amendments found in supplied resolution.')

    if amended_text and return_doc:
        from eucy import eu_wrapper
        import spacy

        nlp = spacy.blank("en")
        eu_wrapper = eu_wrapper(nlp)

        doc = eu_wrapper(amended_text)

    if not modify_iteratively:
        doc = modify_doc(doc)

    if return_doc:
        return doc
    else:
        if amended_text:
            return amended_text
        return doc.text


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

        from bs4 import Tag

        if isinstance(self.source_raw, str):

            from bs4 import BeautifulSoup
            bs = BeautifulSoup(self.source_raw, html_parser())

            return bs

        elif isinstance(self.source_raw, Tag):
            return self.source_raw

        else:
            raise ValueError('source_raw must be a string or a BeautifulSoup object')

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
