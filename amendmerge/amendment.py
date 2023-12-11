# Class amendment
import re
from dataclasses import dataclass, field, InitVar, Field
import pandas as pd
import warnings
from typing import Union, Optional, Dict
from amendmerge.utils import to_numeric, clean_html_text, remove_new_element_spans, remove_new_article_element_spans
import textdistance
from fuzzysearch import find_near_matches
from eucy.utils import find_containing_spans, get_element_text, letter_to_int


class PositionAttribute:
    def __init__(self, value, source, **kwargs):
        self.value = value
        self.source = source

        # set kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __int__(self):

        try:
            return int(self.value)
        except:
            try:
                # look for integers in string
                m = re.search(r'\d+', self.value)

                if m:
                    return int(m.group(0))

                # look for letters in string
                m = re.search(r'[a-z]+', self.value)

                if m:
                    return letter_to_int(m.group(0))

                raise ValueError(f"Could not convert {self.value} to int")


            except:
                raise ValueError(f"Could not convert {self.value} to int")



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


    def to_dict(self, return_value_only = True, include_none = False, convert_to_int = True):

        if convert_to_int and not return_value_only:
            warnings.warn("convert_to_int is True but return_value_only is False. Setting convert_to_int to False.")
            convert_to_int = False

        if include_none:
            dic = {k: v for k, v in self.__dict__.items() if isinstance(v, (PositionAttribute, bool)) or v is None}
        else:
            dic = {k: v for k, v in self.__dict__.items() if isinstance(v, (PositionAttribute, bool)) and (isinstance(v, PositionAttribute) and v.value is not None) or (isinstance(v, bool) and v is not None)}
        if return_value_only:
            if not convert_to_int:
                dic = {k: v.value if isinstance(v, PositionAttribute) else v for k, v in dic.items()}
            else:
                for k, v in dic.items():
                    if isinstance(v, PositionAttribute):
                        try:
                            dic[k] = int(v)
                        except:
                            dic[k] = v.value
                    else:
                        dic[k] = v

        # remove all that start with _
        dic = {k: v for k, v in dic.items() if not k.startswith('_')}

        return dic

    def to_series(self, prefix=''):
        return pd.Series(self.to_dict(return_value_only=True, include_none=False)).add_prefix(prefix=prefix)


    def to_df(self, prefix=''):
        return self.to_series(prefix=prefix).to_frame().T

    def is_empty(self):
        return len(self.to_dict(return_value_only=True, include_none=False)) == 0

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

    def match(self, doc, include_new_elements=False):
        """
        Match the position to the corresponding element in the doc

        Parameters
        ----------
        doc : spacy.tokens.Doc
            The doc to be matched to
        include_new_elements : bool, optional
            Whether to include new elements, by default False (returns the original document elements in their original position)

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

        if include_new_elements:

            if 'citation' in pos_dict:
                return doc.spans['citations'][pos_dict['citation']-1]
            elif 'recital' in pos_dict:
                return doc.spans['recitals'][pos_dict['recital']-1]
            elif 'article' in pos_dict:
                if not any(k in pos_dict for k in ['paragraph', 'subparagraph', 'indent', 'point']):
                    return doc.spans['articles'][pos_dict['article']-1]
                else:
                    raise NotImplementedError(f"Matching of article elements including modified elements not implemented yet.")

        else:

            if 'citation' in pos_dict:
                return remove_new_element_spans(doc.spans['citations'])[pos_dict['citation'] - 1]
            elif 'recital' in pos_dict:
                return remove_new_element_spans(doc.spans['recitals'])[pos_dict['recital'] - 1]

            elif 'article' in pos_dict:
                article_idx = pos_dict.get('article', -1)-1
                paragraph_idx = pos_dict.get('paragraph', 1)-1  # Default to first paragraph
                subparagraph_idx = pos_dict.get('subparagraph', 1)-1  # Default to first subparagraph
                indent_idx = pos_dict.get('indent', -1)-1
                point_idx = pos_dict.get('point', -1)-1

                try:
                    article = doc.spans['articles'][article_idx]
                    elements = remove_new_article_element_spans(doc._.article_elements[article_idx])
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
        from eucy import modify as eumodify

        if not is_eucy_doc(doc):
            raise TypeError("doc must be a euCy doc")

        pos_dict = self.position.to_dict(return_value_only=True, include_none=False)

        if 'annex' in pos_dict or 'title' in pos_dict:
            raise NotImplementedError(f"Matching of annexes and titles not implemented yet.")

        applied = False
        doc_level_mod = False # whether the text has been modified at the doc level rather than at the matched element level
        new_text = None

        if self.position.is_empty():
            warnings.warn(f"Position is empty. Applying amendment at doc level.")

        # apply amendment
        if self.type == 'new':

            if 'citation' in pos_dict:
                element_type = 'citation'
                element_pos = pos_dict['citation']
            elif 'recital' in pos_dict:
                element_type = 'recital'
                element_pos = pos_dict['recital']
            elif 'article' in pos_dict:
                if 'paragraph' in pos_dict:
                    element_type = 'article_element'
                else:
                    element_type = 'article'
                    element_pos = pos_dict['article']

            if element_type == 'article_element':
                # handle article elements

                # loop through pos dict and try to get element position
                for k, element_pos in pos_dict.items():
                    if k not in ['article', 'paragraph', 'subparagraph', 'indent', 'point']:
                        continue
                    parsed_pos = None
                    if isinstance(element_pos, str):
                        try:
                            # try to extract a number from the string
                            m = re.search(r'\d+', element_pos)

                            if m:
                                parsed_pos = int(m.group(0))
                        except:
                            pass

                        if parsed_pos is None:
                            try:
                                # try to extract a number from the string
                                m = re.search(r'[a-z]+', element_pos)

                                if m:
                                    parsed_pos = letter_to_int(m.group(0))
                            except:
                                pass

                        if parsed_pos is None:
                            parsed_pos = 'end'


                    elif isinstance(element_pos, int):
                        parsed_pos = element_pos
                    else:
                        parsed_pos = 'end'

                    if isinstance(parsed_pos, int):
                        parsed_pos = parsed_pos - 1

                        if parsed_pos < 0:
                            parsed_pos = 0

                    pos_dict[k] = parsed_pos


                doc._.add_article_element(self.text,
                                          **{k: v for k, v in pos_dict.items() if k in ['article', 'paragraph', 'subparagraph', 'indent', 'point']},
                                          add_ws = True,
                                          auto_position = True
                                          )

                applied = True



            elif element_pos:
                # handle non-article elements

                if isinstance(element_pos, str):

                    try:
                        # try to extract a number from the string
                        m = re.search(r'\d+', element_pos)

                        if m:
                            add_pos = int(m.group(0))
                        else:
                            add_pos = 'end'
                    except:
                        add_pos = 'end'
                elif isinstance(element_pos, int):
                    add_pos = element_pos
                else:
                    add_pos = 'end'

                doc._.add_element(self.text,
                                      position = add_pos - 1 if isinstance(add_pos, int) and add_pos>0 else add_pos,
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

                    existing_text_simplified = re.sub(r'\s+', ' ', self.existing_text.lower()).strip()
                    matched_pos_text_simplified = re.sub(r'\s+', ' ', matched_pos.text.lower()).strip()

                    if matched_pos_text_simplified == existing_text_simplified:
                        new_text = self.text
                    elif abs(len(existing_text_simplified)-len(matched_pos_text_simplified)) < 8:
                        # existing_text and matched_pos.text are most likely the same but with some minor differences
                        # so we try to replace the existing text with the amendment text completely
                        new_text = self.text
                    elif textdistance.damerau_levenshtein.normalized_distance(existing_text_simplified, matched_pos_text_simplified) < 0.1:
                        # existing_text and matched_pos.text are most likely the same but with some minor differences
                        # so we replace the existing text with the amendment text completely
                        new_text = self.text
                    elif self.existing_text.lower().strip() in matched_pos.text.lower().strip():
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

                        fm = find_near_matches(self.existing_text.strip(), matched_pos.text, max_l_dist=5)

                        if len(fm) > 0:
                            # sort by dist
                            fm = sorted(fm, key=lambda x: x.dist)

                            # get best match
                            fm = fm[0]

                            # get existing_text string pos in o_text
                            start = fm.start
                            end = fm.end

                            if delete:
                                # delete existing text
                                new_text = matched_pos.text[:start] + matched_pos.text[end:]
                            else:
                                # replace existing_text with amendment text
                                new_text = matched_pos.text[:start] + self.text + matched_pos.text[end:]


            if not applied and not new_text and text_match_fallback:

                max_l_dist = int(len(self.existing_text.strip())*0.02)

                if max_l_dist < 8:
                    max_l_dist = 8

                # TODO how to deal with badly formatted proposal texts?
                fm = find_near_matches(self.existing_text.strip(), doc.text, max_l_dist=max_l_dist)

                if len(fm) > 0:
                    # sort by dist
                    fm = sorted(fm, key=lambda x: x.dist)

                    # get best match
                    fm = fm[0]

                    # try to match fm to span / position
                    matched_poss = find_containing_spans(doc, fm.start, fm.end, include_article_elements=False) # TODO handle paragraphs

                    if len(matched_poss) > 0:

                        # TODO implement normal matched pod routine if pos was matched

                        # if there has been a pos match
                        matched_pos = matched_poss[0]

                        # get existing_text string pos in match text
                        start = fm.start - matched_pos.start_char
                        end = fm.end - matched_pos.start_char

                        if delete:
                            # delete existing text
                            new_text = matched_pos.text[:start] + matched_pos.text[end:]
                        else:
                            # replace existing_text with amendment text
                            new_text = matched_pos.text[:start] + self.text + matched_pos.text[end:]

                    else:
                        warnings.warn(
                            f"Could not match position {str(self.position.to_dict())} to doc. Replacing doc text instead.")
                        # replace existing_text with amendment text
                        new_text = doc.text[:fm.start] + self.text + doc.text[fm.end:]
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
                                               deletion_threshold=None)
                    applied = True

        if applied:
            if modify or doc_level_mod:
                eumodify.modify_doc(doc, eu_wrapper=eu_wrapper)
            return None
        else:
            raise Exception(f"Could not apply amendment {str(self.to_dict())} to doc (missing implementation or existing text not present in doc).")


    def to_dict(self, return_value_only = True, include_none = False, include_position = True, convert_to_int = True):
        # NOTE return_value_only only for future compatibility (possible expansion of Amendent to hold original and processed values similar to PositionAttribute)

        amm_dict = {}

        if include_position:
            amm_dict = self.position.to_dict(return_value_only = return_value_only, include_none = include_none, convert_to_int = convert_to_int)

        if include_none:
            amm_dict.update({k: v for k, v in self.__dict__.items() if (not isinstance(v, (object)) or v is None) and k != 'position'})
        else:
            amm_dict.update({k: v for k, v in self.__dict__.items() if (not isinstance(v, (object)) and v is not None) and k != 'position'})

        # remove all that start with _
        amm_dict = {k: v for k, v in amm_dict.items() if not k.startswith('_')}

        return amm_dict

    def to_series(self, convert_to_int = True):
        return pd.Series(self.to_dict(return_value_only=True, include_none=False, convert_to_int=convert_to_int))

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

    def to_dict(self):
        return [amendment.to_dict() for amendment in self]

    def to_df(self):
        return pd.DataFrame.from_records([amendment.to_dict() for amendment in self])

    def edit_distance(self, method = 'DamerauLevenshtein', qval = None):
        return sum([amendment.edit_distance(method = method, qval = qval) for amendment in self])


