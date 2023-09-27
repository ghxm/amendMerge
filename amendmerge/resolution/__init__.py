from amendmerge import DataSource
import warnings

class Resolution(DataSource):

    def __init__(self,*args, amendment_type = None, parse_amendment_table = True, **kwargs):

        self.amendment_type = amendment_type
        self.parse_amendment_table = parse_amendment_table
        self.text = None
        self.amendment_table = None
        self.amended_text = None

        super().__init__(*args, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs):
        raise NotImplementedError("Resolution should not be instantiated directly.")


    def get_type(self):
        return 'resolution'

    def get_amendment_num(self):
        if self.amendment_type == 'amendments_table':
            if self.amendment_table is not None and isinstance(self.amendment_table.amendments, list):
                return len(self.amendment_table.amendments)
            else:
                return None

        elif self.amendment_type == 'amendments_text':

            # TODO return number of amendments in amended text
            warnings.warn("Amendment number for type amendments_text not implemented yet.")
            return None
        else:
            warnings.warn("Amendment number not available for amendment type " + self.amendment_type)
            return None

    def parse(self):

        self.find_title()

        # define steps that need to be taken to parse any EP report
        self.find_text()

        if self.amendment_type is None:
            self.find_amendment_type()

        if self.amendment_type == 'amendments_table':
            if self.parse_amendment_table:
                self.find_amendment_table()
        elif self.amendment_type == 'amendments_text':
            self.find_amended_text()
            #self.amended_text_amendments_n = self.get_amended_text_amendments_n()
        elif self.amendment_type in ['simplified_procedure', 'taking_over_com_proposal', 'reject_com_proposal']:
            self.amendments = []


    def find_amendment_type(self):

        """Find the type of the amendment and return a string.
        This method must be implemented in a subclass"""

        raise NotImplementedError("This method must be implemented in a subclass")

    def find_amendent_table(self):
        raise NotImplementedError("This method must be implemented by the subclass.")

    def find_text(self):
        raise NotImplementedError("This method must be implemented by the subclass.")

    def find_amended_text(self):
        raise NotImplementedError("This method must be implemented by the subclass.")

    def get_amended_text_amendments_n(self):
        raise NotImplementedError("This method must be implemented by the subclass.")

    def has_no_text(self):

        return self.text is None or len(self.text.strip()) < 500

    def has_no_amendment_table(self):

        am_tab = self.amendment_table

        if am_tab is None:
            return True
        else:
            if hasattr(am_tab, 'get_text'):
                am_tab = am_tab.get_text(strip=True)
            return am_tab is None

    def has_no_amended_text(self):

        return self.amended_text is None or len(self.amended_text.strip()) < 500

    def has_no_amendment_source(self):

        return self.has_no_amendment_table() and self.has_no_amended_text()

    def has_type_source_mismatch(self):

            return (self.amendment_type == 'amendments_table' and self.has_no_amendment_table() and not self.has_no_amended_text()) \
                or (self.amendment_type == 'amendments_text' and self.has_no_amended_text() and not self.has_no_amendment_table())

    def get_amendments(self):

        # TODO depending on the amendment type, return a list of amendments
        # TODO if amendment type is amendments_table but amendments is None, parse the table and return a list of amendments

        raise NotImplementedError("Yet.")
