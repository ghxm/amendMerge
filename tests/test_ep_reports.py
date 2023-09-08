import pytest
from .conftest import ep_report_result_by_id, ep_report_request_id
import pandas as pd


def test_resolution_amendment_type(ep_report, ep_reports_results, request):

    report_id = ep_report_request_id(request)
    result = ep_report_result_by_id(report_id, ep_reports_results)

    # TODO handle cases where amendment_type is not present in hc data
    # TODO once implemented make sure the correct resolution is compared

    if pd.isna(result['report_type'].values[0]):
        return

    assert ep_report.resolutions[0].amendment_type == result['report_type'].values[0]


# TODO test number of amendments









import os
# read in all reports from the repo
repo = '/Users/maxhaag/data/ep_committee_reports/raw/20230524'
reports = [x for x in os.listdir(repo) if x.endswith('.html')]

@pytest.mark.parametrize('filename', reports)
def _test_no_exceptions(filename):
    from amendmerge.ep_report.html import HtmlEpReport

    for report in reports:
        html = open(repo + '/' + report, 'r').read()
        HtmlEpReport.create(source='html')
