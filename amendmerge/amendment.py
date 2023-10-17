# Class amendment
import re
from dataclasses import dataclass, field, InitVar, Field
import pandas as pd
import warnings
from typing import Union, Optional, Dict
from amendmerge.utils import to_numeric, clean_html_text


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
            return doc.spans['citations'][pos_dict['citation']-1]
        elif 'recital' in pos_dict:
            return doc.spans['recitals'][pos_dict['recital']-1]
        elif 'article' in pos_dict:
            article_idx = pos_dict.get('article', -1)-1
            paragraph_idx = pos_dict.get('paragraph', 1)-1  # Default to first paragraph
            subparagraph_idx = pos_dict.get('subparagraph', 1)-1  # Default to first subparagraph
            indent_idx = pos_dict.get('indent', -1)-1
            point_idx = pos_dict.get('point', -1)-1

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
            if str(value).strip() == '':
                value = None

        value = clean_html_text(value)

        # remove footnotes
        if isinstance(value, str):
            value = re.sub(r'[-_]{3,}.*', '', value, re.DOTALL)

        super().__setattr__(key, value)

        if key != 'type' and all([hasattr(self, attr) for attr in ['text', 'existing_text', 'position']]):
            self.determine_type() # re-determine type

    def edit_distance(self, method = 'DamerauLevenshtein', qval = None):
        """
        Calculate the edit distance between the existing text and the amendment text

        Parameters
        ----------
        method : str
            The edit distance method to be used can be any class name from the textdistance package
        qval : int, optional
            The qval to be used for the edit distance method, by default None

        Returns
        -------
        int
            The edit distance between the existing text and the amendment text

        """

        import textdistance

        dist_meth = getattr(textdistance, method)

        if self.type == 'delete':
            return dist_meth(qval=qval).distance(self.existing_text, '')
        elif self.type == 'new':
            return dist_meth(qval=qval).distance('', self.text)
        else:
            return dist_meth(qval=qval).distance(self.existing_text, self.text)

    def determine_type(self):
        if self.text is None or ((len(self.text)<20 and 'delete' in self.text.lower())):
            self.type = 'delete'
        elif self.existing_text is None or (self.existing_text and len(self.existing_text.strip())<2) or (self.position and self.position.new):
            self.type = 'new'
        else:
            self.type = 'replace'

    def apply(self, doc, modify = False, text_match_fallback = True, eu_wrapper=None):
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

        from eucy.utils import is_eucy_doc
        from eucy import modify

        if not is_eucy_doc(doc):
            raise TypeError("doc must be a euCy doc")

        pos_dict = self.position.to_dict(return_value_only=True, include_none=False)

        if 'annex' in pos_dict or 'title' in pos_dict:
            raise NotImplementedError(f"Matching of annexes and titles not implemented yet.")

        applied = False
        doc_level_mod = False # whether the text has been modified at the doc level rather than at the matched element level
        new_text = None

        # apply amendment
        if self.type == 'new':

            if 'citation' in pos_dict:
                element_type = 'citation'
                element_pos = pos_dict['citation']
            elif 'recital' in pos_dict:
                element_type = 'recital'
                element_pos = pos_dict['recital']
            elif 'article' in pos_dict:
                element_type = 'article'
                element_pos = pos_dict['article']

            # TODO handle paragraphs (also check how they occur in amendment tables)
            #   by getting start and end is from article_elements

            if element_pos:

                if isinstance(element_pos, str):

                    try:
                        # try to extract a number from the string
                        m = re.search(r'\d+', element_pos)

                        if m:
                            add_pos = int(m.group(0))
                    except:
                        add_pos = 'end'
                elif isinstance(element_pos, int):
                    add_pos = element_pos
                else:
                    add_pos = 'end'

                doc._.add_element(self.text,
                                      position = add_pos,
                                      element_type = element_type)


                # check the position and identify the new part
                applied = True

        elif self.type in ['replace', 'delete']:

            delete = self.type == 'delete'

            try:
                matched_pos = self.position.match(doc)
            except:
                matched_pos = None


            if matched_pos:

                if delete and all(k not in pos_dict for k in ['paragraph', 'subparagraph', 'indent', 'point']):
                    # if the whole element is to be deleted, delete it
                    matched_pos._.delete()
                    applied = True
                else:

                    if matched_pos.text.lower().strip() == self.existing_text.lower().strip():
                        matched_pos._.replace_text(self.text,
                                                   keep_ws=True,
                                                   deletion_threshold=10)
                        applied = True
                    elif abs(len(self.existing_text.strip())-len(matched_pos.text.strip())) < 8:
                        # existing_text and matched_pos.text are most likely the same but with some minor differences
                        # so we try to replace the existing text with the amendment text completely
                        new_text = self.text
                    elif self.existing_text.lower() in matched_pos.text.lower().strip():
                        # if existing text is part of text in doc, replace the existing text with the amendment text
                        # try simple replacement

                        new_text = matched_pos.text.replace(self.existing_text.strip(), self.text.strip())

                        if new_text == matched_pos.text:
                            # if simple replacement does not work, try to identify string pos using regex search

                            new_text = None
                            m = re.search(self.existing_text.strip(), matched_pos.text, re.IGNORECASE)

                            if m:
                                # get existing_text string pos in o_text
                                start = m.start()
                                end = m.end()

                                # replace existing_text with amendment text
                                new_text = matched_pos.text[:start] + self.text + matched_pos.text[end:]
                    else:
                        # try to fuzzymatch within matched_pos
                        from fuzzysearch import find_near_matches

                        fm = find_near_matches(self.existing_text.strip(), matched_pos.text, max_l_dist=5)

                        if len(fm) > 0:
                            # sort by dist
                            fm = sorted(fm, key=lambda x: x.dist)

                            # get best match
                            fm = fm[0]

                            # get existing_text string pos in o_text
                            start = fm.start
                            end = fm.end

                            # replace existing_text with amendment text
                            new_text = matched_pos.text[:start] + self.text + matched_pos.text[end:]


            if not applied and not new_text and text_match_fallback:
                warnings.warn(f"Could not match position {str(self.position.to_dict())} to doc. Trying to match text instead.")

                from fuzzysearch import find_near_matches

                max_l_dist = len(self.existing_text.strip())//300

                if max_l_dist < 8:
                    max_l_dist = 8


                # TODO how to deal with badly formatted proposal texts?
                fm = find_near_matches(self.existing_text.strip(), doc.text, max_l_dist=max_l_dist)

                if len(fm) > 0:
                    # sort by dist
                    fm = sorted(fm, key=lambda x: x.dist)

                    # get best match
                    fm = fm[0]

                    # get existing_text string pos in o_text
                    start = fm.start
                    end = fm.end

                    # replace existing_text with amendment text
                    new_text = matched_pos.text[:start] + self.text + matched_pos.text[end:]
                    doc_level_mod = True

            if new_text:
                if doc_level_mod:
                    doc._.replace_text(new_text,
                                        keep_ws=True,
                                        deletion_threshold=None)
                    applied = True

                else:
                    matched_pos._.replace_text(new_text,
                                               keep_ws=True,
                                               deletion_threshold=10)
                    applied = True

        if applied:

            if modify or doc_level_mod:
                modify.modify_doc(doc, eu_wrapper=eu_wrapper)
            return None
        else:
            raise Exception(f"Could not apply amendment {str(self.to_dict())} to doc (missing implementation or existing text not present in doc).")


    def to_dict(self, return_value_only = True, include_none = False, include_position = True):
        # NOTE return_value_only only for future compatibility (possible expansion of Amendent to hold original and processed values similar to PositionAttribute)

        amm_dict = {}

        if include_position:
            amm_dict = self.position.to_dict(return_value_only = return_value_only, include_none = include_none)

        if include_none:
            amm_dict.update({k: v for k, v in self.__dict__.items() if (not isinstance(v, (object)) or v is None) and k != 'position'})
        else:
            amm_dict.update({k: v for k, v in self.__dict__.items() if (not isinstance(v, (object)) and v is not None) and k != 'position'})

        return dict

    def to_series(self):
        return pd.Series(self.to_dict(return_value_only=True, include_none=False))

    def to_df(self):
        return self.to_series().to_frame().T

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
        if isinstance(item, (dict, str)):
            return Amendment(**item)
        elif isinstance(item, Amendment):
            return item
        else:
            raise TypeError("Item must be of type Amendment or convertible to Amendment")

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

    def edit_distance(self, method = 'DamerauLevenshtein', qval = None):
        return sum([amendment.edit_distance(method = method, qval = qval) for amendment in self])


