"""Recompute the third contribution without importing its generated master twice."""
from collections import Counter, defaultdict
import hashlib
import json


def audit(rows):
    rows=[r for r in rows if r['contributor']=='friend2']
    if not rows:return {'available':False,'cells':[]}
    phases={kind:[r for r in rows if r['run_kind']==kind] for kind in ['friend2_primary','friend2_extension','friend2_phase2']}
    extension=phases['friend2_extension']
    groups=defaultdict(list)
    for row in extension:groups[(row['model_requested'],row['task'],row['intervention'])].append(row)
    cells=[]
    for (model,task,mode),attempts in sorted(groups.items()):
        by_uid=defaultdict(list)
        for r in attempts:by_uid[r['run_uid']].append(r)
        selected=[]
        for uid,records in by_uid.items():
            successful=[r for r in records if not r['api_error']]
            # Select the first returned response, never the first correct one.
            if successful:selected.append(successful[0])
        cells.append({
            'model_requested':model,'task':task,'prompt_variant':mode,
            'item_opportunities':len(by_uid),'attempt_records':len(attempts),
            'returned_item_responses':len(selected),'items_without_response':len(by_uid)-len(selected),
            'request_error_records':sum(bool(r['api_error']) for r in attempts),
            'strict_completed_exact':sum(r['strict_correct'] is True for r in selected),
            'completed_visible_target_contains':sum(r['completed_visible_target_contains'] is True for r in selected),
            'truncated_item_responses':sum(r['finish_reason']=='length' for r in selected),
            'reasoning_text_nonempty':sum(bool(r['reasoning_text']) for r in selected),
            'target_present_in_reasoning':sum(r['target_present_in_reasoning'] is True for r in selected),
            'mean_response_latency_seconds':sum(r['latency_seconds'] for r in selected)/len(selected) if selected else None,
            'selection_policy':'First returned model response per UID; all request errors remain in the attempt inventory.',
            'interpretation':'Prompt variants, not verified thinking switches. Guidance is an authored table, not recorded internet retrieval. Tiny sample; checkpoint identities unverified.'
        })
    phase2_groups=defaultdict(list)
    for row in phases['friend2_phase2']:
        phase2_groups[(row['model_requested'],row['task'],row['intervention'])].append(row)
    phase2_cells=[]
    for (model,task,condition),items in sorted(phase2_groups.items()):
        returned=[r for r in items if not r['api_error']]
        phase2_cells.append({
            'model_requested':model,'task':task,'condition':condition,'item_opportunities':len({r['run_uid'] for r in items}),
            'attempt_records':len(items),'returned_records':len(returned),'request_error_records':len(items)-len(returned),
            'strict_completed_exact':sum(r['strict_correct'] is True for r in returned),
            'truncated_records':sum(r['finish_reason']=='length' for r in returned),
            'final_content_nonempty':sum(bool(r['raw_text']) for r in returned),
            'target_present_in_reasoning':sum(r['target_present_in_reasoning'] is True for r in returned),
            'truncation_flag_disagreements':sum(r['truncation_flag_disagrees'] for r in returned),
            'prompt_template_placeholder_present':sum(r['prompt_template_placeholder_present'] for r in items),
            'max_tokens_logged_per_call':False,'token_usage_logged':False,
            'interpretation':'Exploratory prompt/budget pilot. No completed answers; no causal tokenization, compute-scaling or few-shot claim established.',
        })
    payloads=defaultdict(list)
    for row in rows:
        if row['api_error']:continue
        fingerprint=hashlib.sha256(json.dumps([row['prompt'],row['expected'],row['raw_text'],row['reasoning_text']],ensure_ascii=False).encode()).hexdigest()
        payloads[fingerprint].append(row)
    repeats=[]
    for fingerprint,records in payloads.items():
        if len(records)>1:
            repeats.append({'payload_sha256':fingerprint,'record_ids':[r['record_id'] for r in records],'run_uids':[r['run_uid'] for r in records],'models':[r['model_requested'] for r in records],'note':'Same prompt, target, content and reasoning. Retained as separate timestamped records, but independence is not established; deterministic repeated requests, reuse or server routing cannot be distinguished here.'})
    def phase_summary(records):
        returned=[r for r in records if not r['api_error']]
        return {'source_records':len(records),'distinct_uids':len({r['run_uid'] for r in records}),'returned_records':len(returned),'request_error_records':len(records)-len(returned),'strict_completed_exact':sum(r['strict_correct'] is True for r in returned),'completed_visible_target_contains':sum(r['completed_visible_target_contains'] is True for r in returned),'truncated_records':sum(r['finish_reason']=='length' for r in returned),'stored_correct_flags':sum(r['stored_correct'] is True for r in records),'target_present_in_reasoning':sum(r['target_present_in_reasoning'] is True for r in returned)}
    return {
        'available':True,'primary':phase_summary(phases['friend2_primary']),'extension':phase_summary(extension),
        'phase2':phase_summary(phases['friend2_phase2']),'phase2_cells':phase2_cells,
        'phase2_truncation_flag_disagreements':sum(r.get('truncation_flag_disagrees',False) for r in phases['friend2_phase2']),
        'combined_stored_correct_flags':sum(r['stored_correct'] is True for r in rows),
        'cells':cells,'identical_payload_groups':repeats,
        'effective_thinking_switch_verified':False,'web_retrieval_recorded_in_extension':False,
        'primary_model_field_missing':len(phases['friend2_primary']),
        'all_imported_answer_keys_oracle_checked':all(r['oracle_matches_expected'] for r in rows),
        'unsupported_claims':['Confirmed probability mechanism or tokenization cause','Measured reasoning-token budgets or consumption (per-call configuration/usage not logged)','Target in reasoning means solved internally','Architecture effect from requested labels','Internet retrieval effect from authored tables','All cells have four returned model responses','All source records are independent successful experiments','Phase-1 source flags total 31, not the previously claimed 33','Phase-2 few-shot calibration confirmed or tokenization hypothesis rejected','A finite budget pilot proves that more compute cannot help'],
    }
