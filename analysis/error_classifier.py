"""Observable-output categories only; internal causal mechanisms are not inferred."""
from analysis.scoring import evaluate


def classify_acronym_error(input_sentence, ground_truth, parsed_pred, raw_resp, finish_reason=None):
    result=evaluate(raw_resp,ground_truth,finish_reason,'acronym1')
    return {
        'category':result['category'],
        'explanation':'AI/deterministic draft based on raw output and finish reason. Parsed tokens from unfinished text are not final model choices.',
        'confidence':None,
        'needs_human_review':True,
    }
