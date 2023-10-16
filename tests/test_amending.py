import pytest
from .conftest import request_procedure_reference
from amendmerge import amend_law
import textdistance

def test_amendments_dist(ep_report, amended_proposals, proposal_docs, request):

    procedure_reference = request_procedure_reference(request)

    # Test full procedure from EP report to amended text (compare with hand-modified text)
    resolution = ep_report.get_ep_draft_resolution()

    if resolution.amendment_type != 'amendments_table':
        print('Not eligible for this test')
        return

    # TODO account for possibly wrong hand coding (check comment column in ep_reports_hand_coded.csv)

    proposal = proposal_docs[procedure_reference]

    ep_modified_text = amend_law(proposal, resolution, modify_iteratively = False, return_doc = False)

    # compare to modified text from hand-annotated results
    n_dist = textdistance.damerau_levenshtein.normalized_distance(amended_proposals[procedure_reference], ep_modified_text)

    assert n_dist < 0.1
