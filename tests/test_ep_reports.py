# Test the funcationality of the package as a whole on a set of EP reports.

import pytest
from .conftest import ep_report_result_by_id, ep_report_request_id
import pandas as pd


def test_resolution_amendment_type(ep_report, ep_reports_results, request):

    report_id = ep_report_request_id(request)
    result = ep_report_result_by_id(report_id, ep_reports_results)

    if pd.isna(result['report_type'].values[0]):
        return

    assert ep_report.get_ep_draft_resolution().amendment_type == result['report_type'].values[0]


# TODO test number of amendments
def test_resolution_amendment_num(ep_report, ep_reports_results, request):

    report_id = ep_report_request_id(request)
    result = ep_report_result_by_id(report_id, ep_reports_results)

    if pd.isna(result['amendments_num'].values[0]):
        print('Not eligible for this test')
        return

    if ep_report.get_ep_draft_resolution().amendment_type == 'amendments_table': # this test only works for amendment tables
        assert len(ep_report.get_ep_draft_resolution().amendment_table.table_rows) == result['amendments_num'].values[0]
    else:
        print('Not eligible for this test')
        return



import os
# read in all reports from the repo
repo = '/Users/maxhaag/data/ep_committee_reports/raw/20230524'
reports = [x for x in os.listdir(repo) if x.endswith('.html')]

@pytest.mark.parametrize('filename', reports)
def test_no_exceptions(filename):
    from amendmerge.ep_report.html import HtmlEpReport

    for report in reports:
        html = open(repo + '/' + report, 'r').read()
        HtmlEpReport.create(source='html')
