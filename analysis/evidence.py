"""Source-preserving loaders for legacy run files and contributed JSONL logs."""
from pathlib import Path
import hashlib
import json
import re
from analysis.scoring import SCORING_VERSION, evaluate, oracle_answer, pig_latin_encode


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as file:
        for number, line in enumerate(file, 1):
            if line.strip():
                yield number, json.loads(line)


def redact(value):
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key.lower() in {"api_key", "authorization", "x-api-key"} else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED_KEY]", value)
        value = re.sub(r"(api[_ ]key:\s*)[a-fA-F0-9]{32,}", r"\1[REDACTED_IDENTIFIER]", value)
        value = re.sub(r"(Bearer\s+)[A-Za-z0-9_.-]+", r"\1[REDACTED_KEY]", value)
    return value


def identify(contributor, source, index):
    return hashlib.sha256(f"{contributor}|{source}|{index}".encode()).hexdigest()[:24]


def complete(row):
    row["scoring_version"] = SCORING_VERSION
    row["human_verified"] = False
    row["human_notes"] = ""
    if row.get("api_error"):
        row["source_quality"] = "request_error"
    elif row["raw_text"].strip() == "Okay, let's see. I need t...":
        row["source_quality"] = "quarantined_excerpt"
    else:
        row["source_quality"] = "stored_output_provenance_unverified"
    row.update(evaluate(row["raw_text"], row["expected"], row["finish_reason"], row["task"], bool(row.get("api_error")), row["source_quality"]))
    eligible=not row.get('api_error') and row['source_quality']!='quarantined_excerpt'
    row['completed_visible_target_contains']=bool(row['finish_reason']=='stop' and row['expected'].casefold() in row['final_text'].casefold()) if eligible else None
    row['target_present_in_reasoning']=bool(row.get('reasoning_text') and row['expected'].casefold() in row['reasoning_text'].casefold()) if eligible else None
    try:
        if row['task'].startswith('pigdec_'):
            suffix='say' if row['task'].startswith('pigdec_say') else 'ay'
            row['oracle_matches_expected']=pig_latin_encode(row['expected'],suffix)==row['input']
            row['answer_key_check_method']='Forward Pig Latin encoding of the reference; inverse is not necessarily unique'
        else:
            row["oracle_matches_expected"] = oracle_answer(row["task"], row["input"]) == row["expected"]
            row['answer_key_check_method']='Independent deterministic transformation'
    except ValueError:
        row["oracle_matches_expected"] = None
    if row["status"] == "api_error":
        row["draft_notes"] = "Infrastructure/setup event; excluded from model-answer denominators and manual model-failure count."
    elif row["status"] == "quarantined":
        row["draft_notes"] = "Stored excerpt is identical across 14 rows; full independent API outputs are missing. Do not infer a decoding mechanism or count as verified failures."
    elif row["status"] == "truncated":
        row["draft_notes"] = "The saved finish reason is length. This is noncompletion under that run's budget, even if the correct letters appear earlier. It does not prove inability to solve with more budget."
    elif row["status"] == "correct":
        row["draft_notes"] = "Stored completed text matches the answer key. Checkpoint provenance is still unverified."
    elif row["status"] == "formatting":
        row["draft_notes"] = "The strict exact-answer rule failed because the stored response includes extra text or formatting. Check whether the model actually chooses the correct answer; a target appearing in text alone is not sufficient to award correctness or infer a decoding error."
    elif row["category"] == "Letter-order error":
        row["draft_notes"] = "The completed stored answer has the expected letters in a different order. No attention or token-probability measurement identifies a cause."
    else:
        row["draft_notes"] = "Compare the full stored answer with the oracle-checked answer key. Separate incorrect content from an extra explanatory wrapper; no internal cause is established."
    if row.get("stored_correct") is False and row["status"] == "truncated":
        row["draft_notes"] += " The legacy parsed token may come from an input quotation or unfinished explanation; it is not a verified final choice."
    if row["contributor"] == "user" and row["task"] == "rot13dec" and row["item_id"] == "ROT-13_3":
        row["category"] = "Word substitution"
        row["draft_notes"] = "The answer changes path to way while preserving the rest of the sentence. Ciphertext cngu decodes exactly to path. This is compatible with paraphrasing but does not establish a probability-based cause."
    return row


def load_legacy(root):
    rows, retries = [], []
    manifest=root/'evidence/expanded_final/IMPORT_MANIFEST.json'
    expanded=set(json.loads(manifest.read_text())['new_run_files']) if manifest.exists() else set()
    for path in sorted((root / "runs").glob("*.json")):
        # Generated master copies and packages are deliberately not imported.
        data = json.loads(path.read_text())
        source = str(path.relative_to(root))
        task = data.get("task_name") or path.name.split("_")[0]
        original_task=task
        if path.name in expanded:
            if task.startswith('revdec_'):task='word_reverse'
            elif task.startswith('counting_words_'):task='count_words'
            elif task.startswith('sorting_rev'):task='sort_reversealphabetical'
            elif task.startswith('swap_next_base'):task='article_swap_prev'
            elif task=='multiplication_word':task='word_multiply'
        kind = "smoke" if "smoke" in path.name else "pilot" if "pilot" in path.name else "other"
        if path.name in expanded:kind='expanded_smoke'
        for index, item in enumerate(data.get("results", []), 1):
            error = item.get("api_error", item.get("error"))
            row = {
                "record_id": identify("teammate", source, index), "contributor": "teammate", "source_file": source, "source_record": index,
                "source_fidelity": "supplied legacy run record; no original API envelope", "timestamp": item.get("timestamp"),
                "run_kind": kind, "model_requested": data.get("model", "unknown"), "model_returned": item.get("returned_model"),
                "checkpoint_verified": False, "task": task, "original_task_name":original_task, "intervention": data.get("condition", "baseline"),
                "thinking_requested": "on" if data.get("thinking_mode") else "unknown", "thinking_verified": False,
                "guidance_present": bool(data.get("has_guidance")) or data.get("condition") in {"guidance", "retrieval"},
                "item_id": str(item.get("stimulus_id", item.get("id", index-1))),
                "input": item.get("input_words", item.get("input", "")), "prompt": item.get("prompt", ""),
                "expected": item.get("gt", "").strip().strip('"'), "raw_text": item.get("raw_response", item.get("raw", "")),
                "reasoning_text": item.get("reasoning_content", ""), "channel_provenance": "legacy caller may substitute reasoning for final content",
                "stored_parsed": item.get("parsed_response", item.get("parsed", "")), "stored_correct": item.get("correct"),
                "finish_reason": item.get("finish_reason"), "api_error": redact(error), "http_status": item.get("http_status"),
                "response_id": item.get("response_id"), "max_tokens_requested": data.get("max_tokens"),
                "temperature": data.get("temperature"), "top_p": data.get("top_p"),
                "reported_tokens_used": item.get("tokens_used"), "prompt_tokens": None, "completion_tokens": None,
                "tokens_note": "Legacy tokens_used may be total usage or a filled-in value; split usage unavailable.",
                "latency_seconds": item.get("latency"), "request": None, "raw_api_response": None,
                "source_code_max_tokens_not_per_call_record":(150 if data.get('model')=='qwen3-32b' else 250) if path.name in expanded else None,
            }
            rows.append(complete(row))
            for retry_index, retry in enumerate(item.get("retry_history", []), 1):
                retries.append({"parent_record_id": row["record_id"], "source_file": source, "event_index": retry_index, "event": redact(retry)})
    return rows, retries


def load_user(root):
    rows = []
    for filename in ["pilot_transcribed_from_chat.jsonl", "failure_collection.jsonl"]:
        path = root / "evidence/user/redacted" / filename
        if not path.exists():
            continue
        source = str(path.relative_to(root))
        for index, record in read_jsonl(path):
            response = json.loads(record.get("raw_response", "{}"))
            choice = (response.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            test, request = record["test"], record["request"]
            task = "rot13dec" if test["cipher"] == "ROT-13" else "rot12dec"
            status = record.get("http_status")
            error = None if status == 200 else record.get("error") or response.get("error") or f"HTTP {status}"
            usage = response.get("usage", {})
            row = {
                "record_id": identify("user", source, index), "contributor": "user", "source_file": source, "source_record": index,
                "source_fidelity": "chat reconstruction; original pilot file missing" if "pilot_" in filename else "uploaded JSONL; credential identifiers redacted",
                "timestamp": record.get("timestamp"), "run_kind": record.get("run_type", "pilot"),
                "model_requested": request["model"], "model_returned": response.get("model"), "checkpoint_verified": False,
                "task": task, "intervention": "guidance" if record.get("internet_guidance") == "yes" else "baseline",
                "thinking_requested": "off", "thinking_verified": False, "guidance_present": record.get("internet_guidance") == "yes",
                "item_id": test["id"], "input": test["input"], "prompt": next(m["content"] for m in request["messages"] if m["role"] == "user"),
                "expected": test["expected"], "raw_text": message.get("content") or "", "reasoning_text": message.get("reasoning_content") or "",
                "channel_provenance": "returned content field in supplied API response", "stored_parsed": "", "stored_correct": record.get("failed") is False if status == 200 and "failed" in record else None,
                "finish_reason": choice.get("finish_reason"), "api_error": redact(error), "http_status": status,
                "response_id": response.get("id"), "max_tokens_requested": request.get("max_tokens"), "temperature": request.get("temperature"), "top_p": request.get("top_p"),
                "reported_tokens_used": None, "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                "tokens_note": "Usage from supplied API response; pilot envelopes transcribed from chat.", "latency_seconds": None,
                "request": redact(request), "raw_api_response": redact(response),
            }
            rows.append(complete(row))
    return rows


def load_all(root):
    legacy, retries = load_legacy(root)
    rows = legacy + load_user(root) + load_live(root) + load_friend2(root)
    if len({r["record_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate canonical source records")
    # Same model response imported from another contribution must not count twice.
    seen_responses = {}
    for row in rows:
        rid = row.get("response_id")
        row["duplicate_of"] = seen_responses.get(rid) if rid else None
        if rid:
            seen_responses.setdefault(rid, row["record_id"])
    return rows, retries


def load_friend2(root):
    base=root/'evidence/friend2'
    if not base.exists():return []
    lookup={}
    for path in sorted((base/'data/benchmark_subsets').glob('*.jsonl')):
        for _,item in read_jsonl(path):
            key=(item['claim'],item['task_name'],item['condition_name'],item['item_index'])
            lookup[key]=item
    rows=[]
    for filename in ['raw_runs.jsonl','extension_runs.jsonl','extension_phase2_runs.jsonl']:
        path=base/'logs'/filename
        if not path.exists():continue
        source=str(path.relative_to(root))
        for index,r in read_jsonl(path):
            phase={'extension_runs.jsonl':'extension','extension_phase2_runs.jsonl':'phase2'}.get(filename,'primary')
            if phase=='primary':
                item=lookup[(r['claim'],r['task_name'],r['condition_name'],r['item_index'])]
                condition=r['condition_name'];task_original=r['task_name'];model='not_recorded_in_source_row'
            else:
                shift=13 if '13' in r['task'] else 12
                item=lookup[('claim1_task_probability',f'rot-{shift}',f'rot{shift}_shift{shift}',r['item_index'])]
                condition=r['condition'] if phase=='phase2' else r['mode'];task_original=r['task'];model=r['model']
            if task_original.startswith('rot'):
                task='rot'+''.join(c for c in task_original if c.isdigit())+'dec'
            else:
                task={'reverse_dec':'word_reverse','conversion':'conversion_actual' if condition=='fahrenheit_actual' else 'conversion_fake','swap_prev':'article_swap_prev'}.get(task_original,task_original)
            error=None if r.get('status')=='success' else r.get('error') or 'Source records an unsuccessful API attempt.'
            row={
                'record_id':identify('friend2',source,index),'contributor':'friend2','source_file':source,'source_record':index,
                'source_fidelity':'redacted source record with separate content/reasoning; full API envelope and returned checkpoint absent',
                'timestamp':r.get('timestamp'),'run_kind':'friend2_'+phase,'model_requested':model,'model_returned':None,
                'checkpoint_verified':False,'task':task,'original_task_name':task_original,'intervention':condition,
                'thinking_requested':'not switched by API; '+condition if phase!='primary' else 'not explicitly controlled',
                'thinking_verified':False,'guidance_present':condition=='retrieved_guidance','guidance_provenance':'authored table embedded in source; no web retrieval recorded' if condition=='retrieved_guidance' else None,
                'item_id':str(r['item_index']),'run_uid':r.get('run_uid'),'input':item['input'],'prompt':r['prompt'],'expected':r['ground_truth'],
                'raw_text':r.get('raw_content') or '', 'reasoning_text':r.get('reasoning') or '',
                'channel_provenance':'separate raw_content and extracted reasoning in source; original API envelope absent',
                'stored_parsed':r.get('answer') or '', 'stored_correct':r.get('is_correct'),'stored_exact_match':r.get('exact_match'),
                'finish_reason':r.get('finish_reason'),'api_error':redact(error),'http_status':None,'response_id':None,
                'max_tokens_requested':None,'temperature':None,'top_p':None,'reported_tokens_used':None,'prompt_tokens':None,'completion_tokens':None,
                'tokens_note':'Usage and exact generation configuration not logged. Code defaults are not per-request measurements.',
                'latency_seconds':r.get('latency_seconds'),'reported_attempts':r.get('attempts'),'request':None,'raw_api_response':None,
                'legacy_failure_label':r.get('failure_category'),
                'presented_input':' '.join(item['input']) if condition=='char_spaced_stimuli' else item['input'],
                'source_input_matches_prompt':(' '.join(item['input']) if condition=='char_spaced_stimuli' else item['input']) in r['prompt'],
                'stored_is_truncated':r.get('is_truncated'),
                'truncation_flag_disagrees':r.get('finish_reason')=='length' and r.get('is_truncated') is False,
                'prompt_template_placeholder_present':'{shift_k}' in r['prompt'],
                'source_code_budget_not_per_call_record':4096 if condition=='budget_4096_tokens' else 3500 if phase=='phase2' else None,
            }
            if item['correct_output']!=row['expected']:raise ValueError('Friend2 answer differs from its source stimulus')
            rows.append(complete(row))
    return rows


def load_live(root):
    """Import append-only records from the corrected opt-in runner, if any exist."""
    rows=[]
    for path in sorted((root/'runs').glob('live_attempts_*.jsonl')):
        source=str(path.relative_to(root))
        for index,r in read_jsonl(path):
            usage=(r.get('raw_api_response') or {}).get('usage') or {}
            request=r['request']
            row={
                'record_id':identify('new_live',source,index),'contributor':'new_live','source_file':source,'source_record':index,
                'source_fidelity':'append-only API attempt with raw returned envelope when available','timestamp':r.get('timestamp'),
                'run_kind':'new_live','model_requested':request['model'],'model_returned':r.get('returned_model'),
                'checkpoint_verified':False,'task':r['task_name'],'intervention':r['condition'],
                'thinking_requested':'on' if 'thinking' in r['condition'] else 'off','thinking_verified':False,
                'guidance_present':'guidance' in r['condition'],'item_id':str(r['stimulus_id']),
                'input':r['input_words'],'prompt':r['prompt'],'expected':r['gt'],
                'raw_text':r.get('content',''),'reasoning_text':r.get('reasoning_content',''),
                'channel_provenance':'final content and reasoning saved separately','stored_parsed':'','stored_correct':r.get('correct'),
                'finish_reason':r.get('finish_reason'),'api_error':r.get('api_error'),'http_status':r.get('http_status'),
                'response_id':r.get('response_id'),'max_tokens_requested':request.get('max_tokens'),
                'temperature':request.get('temperature'),'top_p':request.get('top_p'),'reported_tokens_used':None,
                'prompt_tokens':usage.get('prompt_tokens'),'completion_tokens':usage.get('completion_tokens'),
                'tokens_note':'Measured API usage when returned; missing values remain unknown.',
                'latency_seconds':r.get('latency'),'request':redact(request),'raw_api_response':redact(r.get('raw_api_response')),
            }
            rows.append(complete(row))
    return rows
