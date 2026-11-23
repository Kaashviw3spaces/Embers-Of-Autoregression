from pathlib import Path
from collections import Counter
import unittest
from analysis.evidence import load_all
from analysis.friend2_audit import audit

ROOT=Path(__file__).resolve().parents[1]


class FriendEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,_=load_all(ROOT)
        cls.friend=[r for r in cls.rows if r['contributor']=='friend2']
        cls.audit=audit(cls.rows)

    def test_master_copy_and_published_repo_are_not_imported(self):
        self.assertEqual(len(self.friend),141)
        self.assertTrue(all('all_runs_master' not in r['source_file'] and '/repo/' not in r['source_file'] for r in self.friend))

    def test_technical_failures_are_not_wrong_model_answers(self):
        errors=[r for r in self.friend if r['api_error']]
        self.assertEqual(len(errors),16)
        self.assertTrue(all(r['strict_correct'] is None for r in errors))
        self.assertEqual(sum(c['items_without_response'] for c in self.audit['cells']),6)

    def test_first_returned_response_preserves_retry_attempts(self):
        self.assertEqual(sum(c['item_opportunities'] for c in self.audit['cells']),48)
        self.assertEqual(sum(c['attempt_records'] for c in self.audit['cells']),54)
        self.assertEqual(sum(c['returned_item_responses'] for c in self.audit['cells']),42)

    def test_actual_guided_rot12_case_is_verified_against_oracle(self):
        cells=[c for c in self.audit['cells'] if c['model_requested']=='qwen3-30b-a3b' and c['task']=='rot12dec' and c['prompt_variant']=='retrieved_guidance']
        self.assertEqual(cells[0]['strict_completed_exact'],1)
        self.assertEqual(cells[0]['returned_item_responses'],4)
        self.assertTrue(all(r['oracle_matches_expected'] and r['source_input_matches_prompt'] for r in self.friend))

    def test_direct_is_not_claimed_to_disable_reasoning(self):
        direct=[r for r in self.friend if r['intervention']=='direct_mode' and not r['api_error']]
        self.assertTrue(direct)
        self.assertTrue(all(r['reasoning_text'] for r in direct))
        self.assertTrue(all(r['thinking_verified'] is False for r in direct))
        self.assertFalse(self.audit['web_retrieval_recorded_in_extension'])

    def test_missing_primary_model_not_filled_from_master(self):
        primary=[r for r in self.friend if r['run_kind']=='friend2_primary']
        self.assertEqual(len(primary),63)
        self.assertTrue(all(r['model_requested']=='not_recorded_in_source_row' for r in primary))

    def test_phase2_finish_reason_overrides_inconsistent_source_boolean(self):
        phase=[r for r in self.friend if r['run_kind']=='friend2_phase2']
        returned=[r for r in phase if not r['api_error']]
        self.assertEqual(len(phase),24)
        self.assertEqual(len(returned),20)
        self.assertTrue(all(r['finish_reason']=='length' and r['status']=='truncated' for r in returned))
        self.assertTrue(all(r['stored_is_truncated'] is False and r['truncation_flag_disagrees'] for r in returned))
        self.assertTrue(all(r['strict_correct'] is False and r['max_tokens_requested'] is None and r['completion_tokens'] is None for r in returned))
        self.assertEqual(self.audit['phase2']['strict_completed_exact'],0)
        self.assertEqual(self.audit['phase2']['target_present_in_reasoning'],10)

    def test_phase2_spacing_matches_presented_input_without_rewriting_the_prompt(self):
        spaced=[r for r in self.friend if r['intervention']=='char_spaced_stimuli']
        self.assertEqual(len(spaced),12)
        self.assertTrue(all(r['presented_input']==' '.join(r['input']) and r['source_input_matches_prompt'] for r in spaced))
        self.assertTrue(all(r['prompt_template_placeholder_present'] for r in spaced))
        self.assertEqual(len(self.audit['phase2_cells']),8)


if __name__=='__main__':unittest.main()
