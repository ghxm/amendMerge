from .conftest import request_procedure_reference
from amendmerge import amend_law
from amendmerge.amendment import AmendmentList, Amendment, Position
from amendmerge.utils import save_differences_from_strings
import textdistance
import os
from eucy.eucy import EuWrapper
import spacy

nlp = spacy.blank("en")
eu_wrapper = EuWrapper(nlp)

def test_amendment_sample():

    proposal = """
                Proposal for a
            
            REGULATION OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL
            
            amending Regulation (EU, EURATOM) No 883/2013, as regards the secretariat of the Supervisory Committee of the European Anti-Fraud Office (OLAF)
            
            THE EUROPEAN PARLIAMENT AND THE COUNCIL OF THE EUROPEAN UNION,
            
            Having regard to the Treaty on the Functioning of the European Union, and in particular Article 325 thereof,
            
            Having regard to the Treaty establishing the European Atomic Energy Community, and in particular Article 106a thereof,
            
            Having regard to the proposal from the European Commission,
            
            After transmission of the draft legislative act to the national parliaments,
            
            Having regard to the opinion of the Court of Auditors,
            
            Acting in accordance with the ordinary legislative procedure,
            
            Whereas:
            
            (1)
            
            The Supervisory Committee of the European Anti-Fraud Office ('the Office') is tasked with regularly monitoring the implementation by the Office of its investigative function, in order to reinforce the Office's independence.
            
            (2)
            
            The framework for the implementation of the budgetary appropriations relating to the Members of the Supervisory Committee should be set up in a way which avoids any appearance of a possible interference of the Office in their duties. Regulation (EC, EURATOM) No 883/2013 should be adapted in order to allow for such a framework. The secretariat of the Supervisory Committee should be provided directly by the Commission, independently from the Office. The Commission should refrain from interfering with the functions of the Supervisory Committee.
            
            (3)
            
            Where the Office appoints a Data Protection Officer in accordance with Article 10(4) of Regulation 883/2013, that Data Protection Officer should continue to be competent for the processing of data by the secretariat of the Supervisory Committee.
            
            (4)
            
            Confidentiality obligations for the staff of the secretariat of the Supervisory Committee should continue to apply.
            
            (5)
            
            The European Data Protection Supervisor has been consulted in accordance with Article 28(2) of Regulation (EC) No 45/2001 and delivered an opinion on….,
            
            HAVE ADOPTED THIS REGULATION:
            
            Article 1
            
            Regulation (EU, EURATOM) No 883/2013 is amended as follows:
            
            (1)
            
            Article 10 is amended as follows:
            
            (a)
            
            in paragraph 4, the following subparagraph is added:
            
            "The Data Protection Officer shall be competent for the processing of data by the Office and the secretariat of the Supervisory Committee."
            
            (b)
            
            in paragraph 5, the second subparagraph is replaced by the following:
            
            "In accordance with the Staff Regulations, the staff of the Office and the staff of the secretariat of the Supervisory Committee shall refrain from any unauthorised disclosure of information received in the exercise of their functions, unless that information has already been made public or is accessible to the public, and shall continue to be bound by that obligation after leaving the service."
            
            (2)
            
            In Article 15(8), the last sentence is replaced by the following:
            
            "Its secretariat shall be provided by the Commission, independently from the Office and in close cooperation with the Supervisory Committee. The Commission shall refrain from interfering with the functions of the Supervisory Committee."
            
            
            Article 2
            
            This Regulation shall enter into force on the [first day of the month following that of its publication in the
            
            Official Journal of the European Union. It shall apply as from 1 January 2017.
            
            This Regulation shall be binding in its entirety and directly applicable in all Member States.
            
            Done at Brussels,
            
            For the European Parliament
            
            For the Council
            
            The President
            
            The President
    """

    proposal = eu_wrapper(proposal)

    amendments = AmendmentList([
        Amendment(
            position = Position(
                recital=1
            ),
            existing_text = "(1) The Supervisory Committee of the European Anti-Fraud Office ('the Office') is tasked with regularly monitoring the implementation by the Office of its investigative function, in order to reinforce the Office's independence.",
            text = "deleted"
            ),
        Amendment(
            position = Position(
                recital=2
            ),
            existing_text = "(2) The framework for the implementation of the budgetary appropriations relating to the Members of the Supervisory Committee should be set up in a way which avoids any appearance of a possible interference of the Office in their duties. Regulation (EC, EURATOM) No 883/2013 should be adapted in order to allow for such a framework. The secretariat of the Supervisory Committee should be provided directly by the Commission, independently from the Office. The Commission should refrain from interfering with the functions of the Supervisory Committee.",
            text = "(2) Test test test test.",
            )
    ])

    amended_text = amend_law(proposal, amendments, modify_iteratively = False, return_doc = True)

    assert len(amended_text.spans['recitals']) == len(proposal.spans['recitals']) - 1
    assert amended_text.spans['recitals'][0].text.strip() == "(2) Test test test test."

def test_amendment_hand_dist(ep_report, amended_proposals, proposal_docs, request):

    logdir = 'tests/logs/'

    procedure_reference = request_procedure_reference(request)

    # Test full procedure from EP report to amended text (compare with hand-modified text)
    resolution = ep_report.get_ep_draft_resolution()

    if resolution.amendment_type != 'amendments_table':
        print('Not eligible for this test')
        return

    # TODO account for possibly wrong hand coding (check comment column in ep_reports_hand_coded.csv)

    proposal = proposal_docs[procedure_reference]

    ep_modified_text = amend_law(proposal, resolution, modify_iteratively = False, return_doc = False)


    # create log directory
    if not os.path.exists(f'{logdir}/{procedure_reference}'):
        os.makedirs(f'{logdir}/{procedure_reference}')

    # log texts
    with open(f'{logdir}/{procedure_reference}/amendmerge.txt', 'w') as f:
        f.write(ep_modified_text)

    with open(f'{logdir}/{procedure_reference}/handcoded.txt', 'w') as f:
        f.write(amended_proposals[procedure_reference])

    # log differences
    save_differences_from_strings(amended_proposals[procedure_reference], ep_modified_text, f'{logdir}/{procedure_reference}/diff.txt')

    # compare to modified text from hand-annotated results
    n_dist = textdistance.damerau_levenshtein.normalized_distance(amended_proposals[procedure_reference], ep_modified_text)

    assert n_dist < 0.00001
