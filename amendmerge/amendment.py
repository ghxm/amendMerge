# Class amendment

from dataclasses import dataclass, field, InitVar, Field
import pandas as pd
import warnings
from typing import Union, Optional, Dict
from amendmerge.utils import to_numeric


class PositionAttribute:
    def __init__(self, value, source, **kwargs):
        self.value = value
        self.source = source

        # set kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)



@dataclass
class Position:
    """
    Class for positions in a document
    """
    title: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    recital: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    citation: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    article: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    paragraph: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    subparagraph: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    point: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    subpoint: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    indent: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    annex: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    part: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    section: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    table: Optional[Union[int, str, bool]] = None
    row: Optional[Union[int, str]] = field(default=None, metadata={"descriptor": PositionAttribute})
    new: Optional[bool] = field(default=None, metadata={"doc": "Whether the position is new (i.e. not in the original document)"})
    amended_position: Optional['Position'] = field(default=None, metadata={"doc": "The position in the amended document"})
    extra_args: InitVar[Optional[Dict]] = field(default=None)


    def __post_init__(self,  extra_args: Optional[Dict]):

        if extra_args:
            for key, value in extra_args.items():
                setattr(self, key, value)

    def __setattr__(self, name, value):
        #print(f"Setting attribute {name} to {value}")
        field_info: Field = self.__dataclass_fields__.get(name)
        descriptor_class = field_info.metadata.get("descriptor") if field_info else None
        if descriptor_class and value is not None:
            try:
                num_val = to_numeric(value)
            except:
                num_val = value
            super().__setattr__(name, descriptor_class(value=num_val, source=value))
        else:
            super().__setattr__(name, value)

    def to_dict(self, return_value_only = True, include_none = False):
        if include_none:
            dic = {k: v for k, v in self.__dict__.items() if isinstance(v, (PositionAttribute, bool)) or v is None}
        else:
            dic = {k: v for k, v in self.__dict__.items() if isinstance(v, (PositionAttribute, bool)) and (isinstance(v, PositionAttribute) and v.value is not None) or (isinstance(v, bool) and v is not None)}
        if return_value_only:
            dic = {k: v.value if isinstance(v, PositionAttribute) else v for k, v in dic.items()}
        return dic

    def to_series(self, prefix=''):
        return pd.Series(self.to_dict(return_value_only=True, include_none=False)).add_prefix(prefix=prefix)


    def to_df(self, prefix=''):
        return self.to_series(prefix=prefix).to_frame().T

    def exists(self, doc):
        """
        Check if the position exists in the doc

        Parameters
        ----------
        doc : spacy.tokens.Doc
            The doc to be checked

        Returns
        -------
        bool
            Whether the position exists in the doc

        """

        if self.match(doc):
            return True
        else:
            return False

    def match(self, doc):
        """
        Match the position to the corresponding element in the doc

        Parameters
        ----------
        doc : spacy.tokens.Doc
            The doc to be matched to

        Returns
        -------
        spacy.tokens.Span
            The matched span

        """

        from eucy.utils import is_eucy_doc

        if not is_eucy_doc(doc):
            raise TypeError("doc must be a euCy doc")

        pos_dict = self.to_dict(return_value_only = True, include_none = False)

        # TODO handle title citations
        # TODO handle annexes

        if 'annex' in pos_dict or 'title' in pos_dict:
            raise NotImplementedError(f"Matching of annexes and titles not implemented yet.")

        if 'citation' in pos_dict:
            return doc.spans['citations'][pos_dict['citation']]
        elif 'recitals' in pos_dict:
            return doc.spans['citations'][pos_dict['citation']]
        elif 'article' in pos_dict:
            article_idx = pos_dict.get('article', -1)
            paragraph_idx = pos_dict.get('paragraph', 0)  # Default to first paragraph
            subparagraph_idx = pos_dict.get('subparagraph', 0)  # Default to first subparagraph
            indent_idx = pos_dict.get('indent', -1)
            point_idx = pos_dict.get('point', -1)

            try:
                article = doc.spans['articles'][article_idx]
                elements = doc._.article_elements[article_idx]
            except IndexError:
                return None

            if all(k not in pos_dict for k in ['paragraph', 'subparagraph', 'indent', 'point']):
                return article

            paragraph = elements['pars'][paragraph_idx] if 0 <= paragraph_idx < len(elements['pars']) else None

            # TODO always return subparagraph even if only paragraph is specified?
            if 'subparagraph' in pos_dict:
                subparagraph = elements['subpars'][paragraph_idx][
                    subparagraph_idx] if paragraph and 0 <= subparagraph_idx < len(
                    elements['subpars'][paragraph_idx]) else None
            else:
                subparagraph = None

            if 0 <= indent_idx:
                try:
                    if subparagraph:
                        return elements['indents'][paragraph_idx][subparagraph_idx][indent_idx]
                    else:
                        return elements['indents'][paragraph_idx][0][indent_idx]
                except IndexError:
                    pass

            if 0 <= point_idx:
                try:
                    if subparagraph:
                        return elements['points'][paragraph_idx][subparagraph_idx][point_idx]
                    else:
                        return elements['points'][paragraph_idx][0][point_idx]
                except IndexError:
                    pass

            return subparagraph or paragraph or article

        raise NotImplementedError(f"Matching of position {self.to_dict()} not implemented yet.")






class Amendment:

    """
    Class for amendments
    """

    def __init__(self,
                 text = None,
                 existing_text = None,
                 position=None,
                 num = None,
                 type = None,
                 justification = None,
                 amm_raw = None,
                 **kwargs):

        """
        Initialize an amendment object

        Parameters
        ----------
        text : str, optional
            The text of the amendment, by default None
        existing_text : str, optional
            The existing text of the amendment, by default None
        position : Position, optional
            The position of the amendment, by default None
        num : int, optional
            The number of the amendment, by default None
        type : str, optional
            The type of the amendment, may be "new", "replace" or "delete", by default None
        justification : str, optional
            The justification of the amendment, by default None
        amm_raw : str, optional
            The raw source of the amendment, by default None
        """

        # set attributes
        self.text = text
        self.existing_text = existing_text
        self.position = position
        self.num = num
        self.type = type
        self.justification = justification
        self.amm_raw = amm_raw

        # set kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.type is None:
            self.determine_type()

    def __setattr__(self, key, value):
        if key in ['text', 'existing_text']:
            if str(value) == '':
                value = None
        super().__setattr__(key, value)

        if key != 'type' and all([hasattr(self, attr) for attr in ['text', 'existing_text', 'position']]):
            self.determine_type() # re-determine type

    def determine_type(self):
        if self.text is None or ((len(self.text)<20 and 'delete' in self.text.lower())):
            self.type = 'delete'
        elif self.existing_text is None or (self.position and self.position.new):
            self.type = 'new'
        else:
            self.type = 'replace'

    def apply(self, doc, modify = False, text_match_fallback = True):
        """
        Apply the amendment to a spacy doc

        Parameters
        ----------
        doc : spacy.tokens.Doc
            The doc to be amended
        modify : bool, optional
            Whether to modify the doc after applying the amendment, by default False

        Returns
        -------
        spacy.tokens.Doc

        """

        # apply amendment
        if self.type == 'new':
            # TODO hier weiter
            raise NotImplementedError
        elif self.type == 'replace':
            # TODO if can't find existing text by position, try to find it by text, send a warning
            raise NotImplementedError
        elif self.type == 'delete':
            # TODO if can't find existing text by position, try to find it by text, send a warning
            raise NotImplementedError

    def to_df(self, prefix = ''):

        # get object attributes except for the ones that are objects themselves
        attr_dict = {prefix + k: v for k, v in self.__dict__.items() if not isinstance(v, object)}

        # try to add the object as a dataframe
        for item in self.__dict__.items():
            if isinstance(item[1], object):

                try:
                    attr_dict.update({item[0]: item[1].to_df()})
                except:
                    warnings.warn(f'Could not convert {str(item[0])} to dataframe')

        # TODO add to_dict and to_series methods and call this (see Position.to_df())


class AmendmentList(list):
    def __init__(self, initial_data):
        for item in initial_data:
            item = self._convert_to_amendment(item)
            self._type_check(item)
        super().__init__(initial_data)

    def _type_check(self, item):
        if not isinstance(item, Amendment):
            raise TypeError("Item must be of type Amendment")

    def _convert_to_amendment(self, item):
        if isinstance(dict, str):
            return Amendment(**item)
        return item

    def append(self, item):
        item = self._convert_to_amendment(item)
        self._type_check(item)
        super().append(item)

    def extend(self, items):
        items = [self._convert_to_amendment(item) for item in items]
        for item in items:
            self._type_check(item)
        super().extend(items)

    def insert(self, index, item):
        item = self._convert_to_amendment(item)
        self._type_check(item)
        super().insert(index, item)

    def to_df(self):
        return pd.DataFrame([amendment.to_dict() for amendment in self])


