"""Validate consistency of regenerated local artifacts, without network access."""
from pathlib import Path
import csv
import json
import zipfile
import hashlib

ROOT=Path(__file__).resolve().parent


def main():
    summary=json.loads((ROOT/'MASTER_RUN_METADATA.json').read_text())
    with (ROOT/'MASTER_RESULTS.csv').open(newline='') as file:rows=list(csv.DictReader(file))
    assert len(rows)==summary['top_level_source_records']
    assert len({r['record_id'] for r in rows})==len(rows)
    assert sum(r['status']=='quarantined' for r in rows)==summary['quarantined_excerpt_records']
    with (ROOT/'MANUAL_FAILURE_REVIEW.csv').open(newline='') as file:reviews=list(csv.DictReader(file))
    assert len(reviews)==summary['selected_review_cases']==30
    assert len({r['record_id'] for r in reviews})==30
    assert sum(r['review_group']=='Wrong completed answer' for r in reviews)==5
    assert sum(r['review_group']=='Unfinished response' for r in reviews)==25
    assert 'contributor' not in reviews[0]
    assert all(r['evidence_excerpt'] and r['draft_notes'] for r in reviews)
    with (ROOT/'analysis/ALL_CANDIDATE_FAILURES.csv').open(newline='') as file:candidates=list(csv.DictReader(file))
    assert len(candidates)==summary['strict_failure_candidates']
    assert all(r['source_quality']!='quarantined_excerpt' for r in reviews)
    assert all(r['record_id'] in {x['record_id'] for x in rows} for r in reviews)
    with (ROOT/'analysis/REVIEW_FIRST_30.csv').open(newline='') as file:first=list(csv.DictReader(file))
    assert first==reviews
    confirmed=sum(r['human_verified'].lower()=='true' and bool(r['human_notes'].strip()) and bool(r['reviewer_name'].strip()) for r in reviews)
    assert confirmed==summary['participant_reviews_confirmed']
    assert summary['strict_completed_stored_matches']+summary['strict_failure_candidates']==summary['usable_stored_response_records']
    friend=summary.get('friend2_prompt_variant_evidence',{})
    if friend.get('available'):
        assert sum(c['attempt_records'] for c in friend['cells'])==friend['extension']['source_records']
        assert sum(c['returned_item_responses'] for c in friend['cells'])==friend['extension']['returned_records']
        assert sum(c['strict_completed_exact'] for c in friend['cells'])==friend['extension']['strict_completed_exact']
        assert sum(c['attempt_records'] for c in friend['phase2_cells'])==friend['phase2']['source_records']
        assert sum(c['returned_records'] for c in friend['phase2_cells'])==friend['phase2']['returned_records']
        assert sum(c['truncation_flag_disagreements'] for c in friend['phase2_cells'])==friend['phase2_truncation_flag_disagreements']
    source_by_id={r['record_id']:r for r in rows}
    with (ROOT/'analysis/COMBINED_PRIMARY_FINDINGS.csv').open(newline='') as file:primary=list(csv.DictReader(file))
    assert len(primary)==21 and sum(int(r['records']) for r in primary)==63
    assert sum(int(r['completed_with_target']) for r in primary)==20
    assert sum(int(r['unfinished']) for r in primary)==43
    for group in primary:
        items=[source_by_id[rid] for rid in group['record_ids'].split(',')]
        assert all(r['task']==group['task'] and r['intervention']==group['condition'] for r in items)
        assert int(group['records'])==len(items)==3
        assert int(group['completed_with_target'])==sum(r['completed_visible_target_contains']=='True' for r in items)
    with (ROOT/'analysis/KEY_ERROR_EVIDENCE.csv').open(newline='') as file:key_errors=list(csv.DictReader(file))
    assert len(key_errors)==5
    for case in key_errors:
        row=source_by_id[case['record_id']]
        assert row['finish_reason']=='stop' and row['strict_correct']=='False'
        assert case['expected']==row['expected'] and case['observed'] in row['raw_text']
        assert row['oracle_matches_expected']=='True'
    for filename in ['MASTER_RESULTS.csv','MASTER_RAW_RESPONSES.jsonl','MASTER_API_ERRORS.csv','MASTER_ERROR_ANALYSIS.csv','MASTER_RUN_METADATA.json','MANUAL_FAILURE_REVIEW.csv']:
        assert (ROOT/filename).read_bytes()==(ROOT/'results/master'/filename).read_bytes()
    try:
        from pypdf import PdfReader
    except ImportError:
        print('pypdf unavailable: PDF page counts not checked here.')
    else:
        report=PdfReader(str(ROOT/'report/Combined_Report.pdf'))
        assert len(report.pages)==4
        report_text='\n'.join(page.extract_text() for page in report.pages)
        for title in ['Combined Experiments and Findings','Replication Findings: Ciphers and Other Tasks','Extensions: Thinking, Guidance and New Tests','Meaningful Errors, Validity and Hackathon Status']:
            assert title in report_text
        assert len(PdfReader(str(ROOT/'slides/Presentation.pdf')).pages)==5
        assert 'Aliyah Anand' in report_text
        print('PDF limits: four report pages, five slides.')
    from openpyxl import load_workbook
    workbook=load_workbook(ROOT/'Manual_Error_Review.xlsx')
    assert workbook.sheetnames==['Review']
    sheet=workbook.active
    assert sheet.max_row==9 and sheet.max_column==7
    for excel_row,case in zip(range(5,10),key_errors):
        assert sheet.cell(excel_row,3).value==case['expected']
        assert sheet.cell(excel_row,4).value==case['observed']
        assert case['record_id'] in sheet.cell(excel_row,1).comment.text
    from pptx import Presentation
    deck=Presentation(ROOT/'slides/Presentation.pptx')
    assert len(deck.slides)==5
    assert all(name in deck.core_properties.author for name in ['Kaashvi Saini','Prachi Vats','Ashwin Anand','Aliyah Anand'])
    target=ROOT/'submission/Embers_Final_Submission.zip'
    if target.exists():
        with zipfile.ZipFile(target) as archive:
            assert archive.testzip() is None
            prefix='Embers_Final_Submission/'
            manifest=json.loads(archive.read(prefix+'SUBMISSION_MANIFEST.json'))
            for name,digest in manifest['files'].items():
                assert hashlib.sha256(archive.read(prefix+name)).hexdigest()==digest
            for name in ['report/Combined_Report.pdf','slides/Presentation.pdf','slides/Presentation.pptx','Manual_Error_Review.xlsx','analysis/KEY_ERROR_EVIDENCE.csv','analysis/COMBINED_PRIMARY_FINDINGS.csv','analysis/friend2_phase2_cells.csv']:
                assert archive.read(prefix+name)==(ROOT/name).read_bytes(),f'Stale bundle: {name}'
            assert not any('/originals/' in name or '/venv/' in name or '/legacy_generated/' in name for name in archive.namelist())
            assert not any('/evidence/friend2/repo/' in name for name in archive.namelist())
        print('Archive CRC, file hashes, and exclusions passed.')
    print(f'Validated {len(rows)} source records; exactly {len(reviews)} selected cases (5 wrong, 25 unfinished); {confirmed} participant reviews confirmed.')


if __name__=='__main__':main()
