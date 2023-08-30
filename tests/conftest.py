import pytest
import pandas as pd
import os
from bs4 import BeautifulSoup

ep_report_request_id = lambda request: request.node.callspec.params['ep_report_html']


def ep_report_result_by_id(id, results=None):
    """Hand-annotated results fixture"""

    # subset results to cases where the id is a substring of the report_id field
    if results is None:
        results = ep_reports_results()

    result = results[results['report_id'].str.contains(id)]

    assert len(result) == 1, "more than one result for id {}".format(
        id)

    res = result.to_dict()

    return res


@pytest.fixture
def ep_reports_results():
    """ Hand-coded data on EP reports """

    reports_results = pd.read_csv('tests/data/ep_reports_hand_coded.csv')

    return reports_results


ep_reports_html_filenames = [f for f in os.listdir('tests/data/ep_reports_html') if f.endswith('.html')]

@pytest.fixture(params=ep_reports_html_filenames)
def ep_report_html(request):
    """ EP reports in html format """

    with open('tests/data/ep_reports_html' + request.param + '.html', 'r') as f:
        report_html = f.read()

    return report_html

@pytest.fixture
def ep_report_bs(ep_report_html):
    """ EP reports in BeautifulSoup format """

    report_bs = BeautifulSoup(ep_report_html, 'html.parser')

    return report_bs

# TODO DataSource (report) objects ficture
