import unittest
from analysis.scoring import evaluate, normalized_answer, oracle_answer, final_text
from run_experiment import parse_acronym_response, response_record, make_request
from analysis.evidence import redact
from analysis.statistical_analysis import mcnemar_exact


class ScoringTests(unittest.TestCase):
    def test_answer_key_does_not_control_extraction(self):
        raw='I considered EPISODE, but my final choice is WRONG.'
        self.assertNotEqual(parse_acronym_response(raw,gt='EPISODE'),'EPISODE')
        self.assertEqual(parse_acronym_response(raw,gt='EPISODE'),parse_acronym_response(raw,gt='OTHER'))

    def test_truncated_target_is_not_completed_success(self):
        result=evaluate('The answer could be EPISODE','EPISODE','length','acronym1_11')
        self.assertFalse(result['strict_correct'])
        self.assertEqual(result['status'],'truncated')

    def test_reasoning_is_not_final_content(self):
        body=make_request('qwen3-32b','task',False,'')
        raw={'model':'qwen3:30b','id':'id','choices':[{'finish_reason':'length','message':{'content':'','reasoning_content':'HELLO'}}],'usage':{'prompt_tokens':12,'completion_tokens':20,'total_tokens':32}}
        result=response_record(raw,body)
        self.assertEqual(result['content'],'')
        self.assertEqual(result['reasoning_content'],'HELLO')
        self.assertEqual(result['returned_model'],'qwen3:30b')
        self.assertEqual(result['prompt_tokens'],12)
        self.assertEqual(result['completion_tokens'],20)

    def test_strict_and_secondary_rules_are_separate(self):
        result=evaluate('E-P-I-S-O-D-E','EPISODE','stop','acronym1_11')
        self.assertFalse(result['strict_correct'])
        self.assertTrue(result['normalized_correct'])
        self.assertFalse(evaluate('Answer: EPISODE','EPISODE','stop','acronym1_11')['normalized_correct'])
        contradicted=evaluate('I considered EPISODE but choose WRONG','EPISODE','stop','acronym1_11')
        self.assertFalse(contradicted['strict_correct'])
        self.assertFalse(contradicted['normalized_correct'])

    def test_think_tags_do_not_leak_target(self):
        self.assertEqual(final_text('<think>EPISODE</think>WRONG'),'WRONG')
        self.assertEqual(final_text('<think>EPISODE'),'')

    def test_errors_and_quarantine_have_no_score(self):
        self.assertIsNone(evaluate('','HELLO',None,'rot13dec',True)['strict_correct'])
        self.assertIsNone(evaluate('excerpt','HELLO','stop','rot13dec',quality='quarantined_excerpt')['strict_correct'])

    def test_cipher_and_initial_oracles(self):
        self.assertEqual(oracle_answer('rot12dec','Tqxxa!'),'Hello!')
        self.assertEqual(oracle_answer('rot13dec','Uryyb!'),'Hello!')
        self.assertEqual(oracle_answer('rot12enc','Hello!'),'Tqxxa!')
        self.assertEqual(oracle_answer('acronym1_11','exalted preteen impeded salient outcast drifter esquire'),'EPISODE')

    def test_keys_are_redacted(self):
        data={'Authorization':'Bearer sk-example','api_key':'secret','error':'api_key: '+('a'*64)+' sk-example'}
        clean=redact(data)
        self.assertEqual(clean['Authorization'],'[REDACTED]')
        self.assertNotIn('a'*64,clean['error'])
        self.assertNotIn('sk-example',clean['error'])

    def test_modes_change_only_mode_field(self):
        off=make_request('qwen3-32b','task',False,'reference')
        on=make_request('qwen3-32b','task',True,'reference')
        self.assertEqual(off['messages'],on['messages'])
        self.assertEqual(off['max_tokens'],on['max_tokens'])
        self.assertNotEqual(off['reasoning_effort'],on['reasoning_effort'])

    def test_exact_paired_test(self):
        self.assertEqual(mcnemar_exact([True],[True])['p_value'],1)
        self.assertEqual(mcnemar_exact([True]*5,[False]*5)['p_value'],0.0625)
        with self.assertRaises(ValueError):mcnemar_exact([True],[])


if __name__=='__main__':unittest.main()
