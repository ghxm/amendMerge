import pytest
from .conftest import ep_report_request_id
from amendmerge import amend_law

def test_amendments_dist(docs, ep_report, amended_proposals, propoal_docs, request):

    # TODO hier weiter

    # Test full procedure from EP report to amended text (compare with hand-modified text)
    resolution = ep_report.get_ep_draft_resolution()

    doc = # TODO

    modified_text = amend_law(doc, resolution, modify_iteratively = False, return_doc = False)

    # TODO compare to modified text from hand-annotated results