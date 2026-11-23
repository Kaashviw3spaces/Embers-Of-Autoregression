"""Describe the final short-budget campaign without pooling it with earlier tests."""
from collections import defaultdict


def audit(rows):
    selected=[r for r in rows if r['run_kind']=='expanded_smoke']
    groups=defaultdict(list)
    for r in selected:groups[(r['model_requested'],r['original_task_name'])].append(r)
    cells=[]
    for (model,condition),items in sorted(groups.items()):
        cells.append({'model_requested':model,'condition':condition,'task':items[0]['task'],
                      'source_file':items[0]['source_file'],'records':len(items),
                      'completed_stop':sum(r['finish_reason']=='stop' for r in items),
                      'completed_with_target':sum(r['completed_visible_target_contains'] is True for r in items),
                      'strict_exact':sum(r['strict_correct'] is True for r in items),
                      'unfinished':sum(r['finish_reason']=='length' for r in items),
                      'api_errors':sum(bool(r['api_error']) for r in items),
                      'source_code_budget_not_logged_per_request':items[0]['source_code_max_tokens_not_per_call_record'],
                      'answer_keys_checked':all(r['oracle_matches_expected'] for r in items),
                      'interpretation':'Small smoke test. Source budgets differ across requested model labels; no fair architecture comparison. Recorded text may include reasoning substituted for empty final content.'})
    return {'source_records':len(selected),'cells':cells,
            'completed_stop':sum(r['finish_reason']=='stop' for r in selected),
            'unfinished':sum(r['finish_reason']=='length' for r in selected),
            'strict_exact':sum(r['strict_correct'] is True for r in selected),
            'completed_with_target':sum(r['completed_visible_target_contains'] is True for r in selected),
            'all_answer_keys_checked':all(r['oracle_matches_expected'] for r in selected),
            'counting_targets_all_one':all(r['expected']=='1' for r in selected if r['task']=='count_words'),
            'meaning':'Supporting short-budget pilots, not a new completed-error set or evidence of a cross-model advantage.'}
