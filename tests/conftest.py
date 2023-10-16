import pytest
import pandas as pd
import os
from bs4 import BeautifulSoup
from amendmerge.ep_report.html import HtmlEpReport

ep_report_request_id = lambda request: request.node.callspec.params['ep_report_html']
request_procedure_reference = lambda request: ep_report_request_id(request).split('_A')[0]


def ep_report_result_by_id(id, results=None):
    """Hand-annotated results fixture"""

    # subset results to cases where the id is a substring of the report_id field
    if results is None:
        results = ep_reports_results()

    # subset to cases where report_id is a substring of id
    result = results[results['report_id'].apply(lambda x: x in id)]

    assert len(result) == 1, "more than one result for id {}".format(
        id)

    return result


@pytest.fixture
def ep_reports_results():
    """ Hand-coded data on EP reports """

    reports_results = pd.read_csv('tests/data/ep_reports_hand_coded.csv')

    return reports_results


ep_reports_html_filenames = [f for f in os.listdir('tests/data/ep_reports_html') if f.endswith('.html')]

@pytest.fixture(params=ep_reports_html_filenames)
def ep_report_html(request):
    """ EP reports in html format """

    with open('tests/data/ep_reports_html/' + request.param, 'r') as f:
        report_html = f.read()

    return report_html

@pytest.fixture
def ep_report_bs(ep_report_html):
    """ EP reports in BeautifulSoup format """

    report_bs = BeautifulSoup(ep_report_html, 'html.parser')

    return report_bs

@pytest.fixture
def ep_report(ep_report_bs):
    """ EP reports in amendMerge format """

    report = HtmlEpReport.create(source=ep_report_bs)

    return report

@pytest.fixture
def amended_proposals():
    """ Amended texts """

    # get all files from data/proposals_amended
    amended_proposals = [f for f in os.listdir('tests/validation_merged/proposals_amended') if f.endswith('.txt')]

    # read texts into dict
    amended_texts = {}

    for f in amended_proposals:
        with open('tests/validation_merged/proposals_amended/' + f, 'r') as p:
            amended_texts[f.replace('.txt', '')] = p.read()


    return amended_texts

@pytest.fixture
def proposal_docs():
    """ Original proposals as euCy-processed docs """

    import spacy
    from eucy.eucy import EuWrapper

    nlp = spacy.blank("en")
    eu_wrapper = EuWrapper(nlp)

    proposals = [f for f in os.listdir('tests/validation_merged/proposals_original') if f.endswith('.txt')]

    # read texts/docs into dict
    proposal_docs = {}

    for f in proposals:
        with open('tests/validation_merged/proposals_original/' + f, 'r') as p:

            proposal_docs[f.replace('.txt', '')] = eu_wrapper(p.read())

    return proposal_docs