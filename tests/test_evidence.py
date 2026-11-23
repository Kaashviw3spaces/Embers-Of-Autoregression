import csv
import json
from pathlib import Path
import tempfile
import unittest
from analysis.evidence import load_all, load_live
from rebuild_evidence import preserve_reviews, csv_write
from prepare_data import prepare_user_plan

ROOT=Path(__file__).resolve().parents[1]


class EvidenceTests(unittest.TestCase):
    def test_known_source_counts_and_no_copy_imports(self):
        rows,retries=load_all(ROOT)
        original=[r for r in rows if r['contributor'] in {'teammate','user'} and r['run_kind']!='expanded_smoke']
        self.assertEqual(len(original),398)
        self.assertEqual(len(retries),11)
        self.assertEqual(sum(r['status']=='quarantined' for r in original),14)
        self.assertTrue(all('results/master' not in r['source_file'] for r in rows))
        self.assertTrue(all(r['oracle_matches_expected'] for r in rows if not r['api_error']))

    def test_existing_human_notes_survive_rebuild(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'review.csv'
            with path.open('w',newline='') as file:
                w=csv.DictWriter(file,fieldnames=['record_id','human_verified','human_category','human_notes','reviewer_name'])
                w.writeheader();w.writerow({'record_id':'abc','human_verified':'True','human_category':'Truncation','human_notes':'Read original output.','reviewer_name':'Test reviewer'})
            out=preserve_reviews(path,[{'record_id':'abc','human_verified':False}])
            self.assertEqual(out[0]['human_notes'],'Read original output.')
            self.assertEqual(out[0]['reviewer_name'],'Test reviewer')

    def test_csv_preserves_fields_from_later_contributors(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'records.csv'
            csv_write(path,[{'record_id':'legacy'},{'record_id':'new','http_status':429}])
            with path.open(newline='') as file:rows=list(csv.DictReader(file))
            self.assertEqual(rows[1]['http_status'],'429')

    def test_requested_alias_case_is_not_silently_changed(self):
        rows,_=load_all(ROOT)
        original=[r for r in rows if r['source_file']=='runs/rot13dec_Qwen3-30B-A3B_baseline.json']
        self.assertTrue(original)
        self.assertTrue(all(r['model_requested']=='Qwen3-30B-A3B' for r in original))

    def test_new_live_envelope_import_and_source_origin(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'runs').mkdir()
            record={'request':{'model':'qwen3-32b','max_tokens':100},'task_name':'rot13dec','condition':'baseline','stimulus_id':0,'input_words':'Uryyb','prompt':'decode','gt':'Hello','content':'Hello','finish_reason':'stop','correct':True,'http_status':200,'api_error':None,'returned_model':'qwen3-32b','raw_api_response':{'usage':{'prompt_tokens':12,'completion_tokens':2}}}
            (root/'runs/live_attempts_example.jsonl').write_text(json.dumps(record)+'\n')
            rows=load_live(root)
            self.assertEqual(len(rows),1)
            self.assertTrue(rows[0]['strict_correct'])
            self.assertEqual(rows[0]['completion_tokens'],2)
            self.assertEqual(rows[0]['channel_provenance'],'final content and reasoning saved separately')

    def test_documented_selection_matches_all_logged_user_items(self):
        # Generate in a temporary directory to keep tests from changing user files.
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder);shutil.copytree(ROOT/'stimuli',target/'stimuli')
            tests,plan=prepare_user_plan(target)
            self.assertEqual(len(tests),60)
            self.assertEqual(len(plan),480)
            self.assertEqual(len({r['run_id'] for r in plan}),480)
            lookup={t['id']:t for t in tests}
            rows,_=load_all(ROOT)
            for r in rows:
                if r['contributor']=='user':
                    self.assertEqual(lookup[r['item_id']]['input'],r['input'])
                    self.assertEqual(lookup[r['item_id']]['expected'],r['expected'])


if __name__=='__main__':unittest.main()
