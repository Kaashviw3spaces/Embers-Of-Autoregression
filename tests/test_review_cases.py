import unittest
from pathlib import Path
from analysis.evidence import load_all
from analysis.review_cases import curated_reviews


class ReviewCaseTests(unittest.TestCase):
    def test_exactly_thirty_evidenced_cases_without_formatting_successes(self):
        rows, _ = load_all(Path(__file__).resolve().parents[1])
        cases = curated_reviews(rows)
        self.assertEqual(len(cases), 30)
        self.assertEqual(len({r['record_id'] for r in cases}), 30)
        self.assertEqual(sum(r['finish_reason'] == 'stop' for r in cases), 5)
        self.assertEqual(sum(r['finish_reason'] == 'length' for r in cases), 25)
        for row in cases:
            source_text = row['raw_text'] or row['reasoning_text']
            self.assertIn(row['evidence_excerpt'], source_text)
            self.assertFalse(row['strict_correct'])
            self.assertFalse(row['api_error'])
            self.assertTrue(row['oracle_matches_expected'])
        extra = next(r for r in cases if r['category'] == 'Extra letter')
        self.assertEqual(extra['observed_answer'], 'LITERALL')
        self.assertEqual(extra['expected'], 'LITERAL')
        self.assertNotIn('fdd78aa495b7c8f6c1f2988c', {r['record_id'] for r in cases})


if __name__ == '__main__':
    unittest.main()
