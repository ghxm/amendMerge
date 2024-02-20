# Test the funcationality of the package as a whole on a set of EP reports.

import pytest
from .conftest import ep_report_result_by_id, ep_report_request_id


def test_resolution_amendment_type(ep_report, ep_reports_results, request):

    report_id = ep_report_request_id(request)
    result = ep_report_result_by_id(report_id, ep_reports_results)

    if pd.isna(result['report_type'].values[0]):
        return

    assert ep_report.get_ep_draft_resolution().amendment_type == result['report_type'].values[0]

    if ep_report.get_ep_draft_resolution().amendment_type == 'amendments_text':
        assert ep_report.get_ep_draft_resolution().amended_text is not None
        assert len(ep_report.get_ep_draft_resolution().amended_text) > 0


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

# get report ids for actual law-making procedure reports
import pandas as pd
ep_reports_meta = pd.read_csv('tests/data/ep_reports_meta.csv')

def sort_report_reference(s):
    # extraxt year and report number
    year = s.split('/')[-1]
    report_number = s.split('/')[-2].split('-')[1]

    return int(year + report_number)

# create a temp column for sorting
ep_reports_meta['sort_report_reference'] = ep_reports_meta['ep_report_reference'].apply(sort_report_reference)

# sort by ep_procedure_reference and ep_report_reference within ep_procedure_reference
ep_reports_meta = ep_reports_meta.sort_values(by=['ep_procedure_reference', 'sort_report_reference'], ascending=[True, True])

# remove temp column
ep_reports_meta = ep_reports_meta.drop(columns=['sort_report_reference'])

# keep only the first row for each ep_procedure_reference
ep_reports_meta = ep_reports_meta.drop_duplicates(subset=['ep_procedure_reference'], keep='first')

filename_to_report_id = lambda s: s[0] + s[2] + '-' + s.split('-')[3].split('_')[0] + '/' + s.split('-')[2] if s.startswith('A-') else s

# keep only COD reports
ep_reports_meta_cod = ep_reports_meta[ep_reports_meta['ep_procedure_reference'].str.contains('COD', na=False)]

# keep only reports that are in ep_reports_meta_cod
reports_cod = [x for x in reports if filename_to_report_id(x) in ep_reports_meta_cod['ep_report_reference'].values]

@pytest.mark.parametrize('filename', reports)
def _test_no_exceptions(filename):
    from amendmerge.ep_report.html import HtmlEpReport

    for report in reports:
        html = open(repo + '/' + report, 'r').read()
        HtmlEpReport.create(html)

@pytest.mark.parametrize('filename', reports_cod)
def test_amendment_type_handling(filename):
    # Ensure that the amendment type is correctly identified and that the corresponding attribute is set
    from amendmerge.ep_report.html import HtmlEpReport

    html = open(repo + '/' + filename, 'r').read()
    report = HtmlEpReport.create(source=html)
    if report.get_ep_draft_resolution().amendment_type == 'amendments_table':
        assert report.get_ep_draft_resolution().amendment_table is not None
        assert len(report.get_ep_draft_resolution().get_amendments()) > 0
    elif report.get_ep_draft_resolution().amendment_type == 'amendments_text':
        assert report.get_ep_draft_resolution().amended_text is not None
        assert len(report.get_ep_draft_resolution().amended_text) > 0
    else:
        print('Not eligible for this test')


@pytest.mark.parametrize('filename', reports_cod)
def test_position_parsing(filename):
    from amendmerge.ep_report.html import HtmlEpReport

    html = open(repo + '/' + filename, 'r').read()
    report = HtmlEpReport.create(source=html)
    if report.get_ep_draft_resolution().amendment_type == 'amendments_table' and report.get_ep_draft_resolution().amendment_table is not None:
        # make sure positions are not empty
        amendments = report.get_ep_draft_resolution().get_amendments()

        assert len(amendments) > 0

        for amendment in amendments:
            assert not amendment.position.is_empty()
