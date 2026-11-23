"""Offline rebuild of both contributors' evidence. Never makes network requests."""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import shutil

from analysis.evidence import load_all, read_jsonl, redact
from analysis.scoring import SCORING_VERSION, oracle_answer

ROOT = Path(__file__).resolve().parent


def json_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def csv_write(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(key for row in rows for key in row)) if rows else ["record_id"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items() if k in fields})


def preserve_reviews(path, rows):
    previous = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as file:
            previous = {r.get("record_id"): r for r in csv.DictReader(file) if r.get("record_id")}
    for row in rows:
        old = previous.get(row["record_id"], {})
        for key in ["human_verified", "human_category", "human_notes", "reviewer_name"]:
            row[key] = old.get(key, False if key == "human_verified" else "")
    return rows


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        # Never combine contributors, smoke/pilot, or request settings implicitly.
        system = json.dumps((row.get("request") or {}).get("messages", [])[:1], sort_keys=True) if row["contributor"] == "user" else "unrecorded"
        key = (row["contributor"], row["source_file"], row["model_requested"], row["task"], row["run_kind"], row["intervention"], row["max_tokens_requested"], system)
        groups[key].append(row)
    out = []
    for _, items in sorted(groups.items(), key=lambda item: str(item[0])):
        first = items[0]
        returned = [r for r in items if not r["api_error"] and not r["duplicate_of"]]
        usable = [r for r in returned if r["source_quality"] != "quarantined_excerpt"]
        denominator = len(usable)
        out.append({
            **{k:first[k] for k in ["contributor", "source_file", "model_requested", "task", "run_kind", "intervention", "max_tokens_requested"]},
            "records": len(items), "returned_records": len(returned), "quarantined": len(returned)-denominator,
            "strict_denominator": denominator, "strict_correct": sum(r["strict_correct"] is True for r in usable),
            "normalized_correct": sum(r["normalized_correct"] is True for r in usable),
            "legacy_stored_correct": sum(r["stored_correct"] is True for r in returned),
            "truncated": sum(r["status"] == "truncated" for r in usable),
            "completed_stop": sum(r["finish_reason"] == "stop" for r in usable),
            "completed_visible_target_contains":sum(r["completed_visible_target_contains"] is True for r in usable),
            "target_present_in_reasoning":sum(r["target_present_in_reasoning"] is True for r in usable),
            "strict_accuracy": sum(r["strict_correct"] is True for r in usable)/denominator if denominator else None,
            "interpretation": "Descriptive rescoring of supplied stored text; checkpoint and legacy channel provenance remain unverified. Not official-paper scoring."
        })
    return out


def main():
    from prepare_data import prepare_user_plan
    reconstructed_tests, planned_cells = prepare_user_plan(ROOT)
    rows, retries = load_all(ROOT)
    master = ROOT / "results/master"
    master.mkdir(parents=True, exist_ok=True)
    # Existing legacy reports were backed up before this first corrected rebuild.
    usable = [r for r in rows if not r["api_error"] and r["source_quality"] != "quarantined_excerpt" and not r["duplicate_of"]]
    failures = [r for r in usable if r["strict_correct"] is False]
    from analysis.review_cases import curated_reviews
    review_fields = ["case_number", "record_id", "task", "item_id", "category", "expected", "observed_answer", "evidence_excerpt", "draft_notes", "finish_reason", "source_file", "source_record", "source_quality", "input", "prompt", "model_requested", "model_returned", "intervention", "thinking_requested", "guidance_present", "raw_text", "reasoning_text", "review_group", "annotation_origin", "human_verified", "human_category", "human_notes", "reviewer_name"]
    reviews = preserve_reviews(ROOT / "MANUAL_FAILURE_REVIEW.csv", curated_reviews(rows))
    # Rebuild the counts only from verified annotations that include a named reviewer and notes.
    reviewed = [r for r in reviews if str(r["human_verified"]).lower() == "true" and r["reviewer_name"].strip() and r["human_notes"].strip()]
    review_by_id = {r["record_id"]:r for r in reviews}
    for row in rows:
        if row["record_id"] in review_by_id:
            row.update({k:review_by_id[row["record_id"]][k] for k in ["human_verified", "human_category", "human_notes", "reviewer_name"]})

    csv_write(ROOT / "MASTER_RESULTS.csv", rows)
    with (ROOT / "MASTER_RAW_RESPONSES.jsonl").open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    errors = [{"event_kind":"final_request_error", "record_id":r["record_id"], "source_file":r["source_file"], "error":r["api_error"]} for r in rows if r["api_error"]]
    errors += [{"event_kind":"retry_history_event", "record_id":r["parent_record_id"], "source_file":r["source_file"], "error":r["event"]} for r in retries]
    csv_write(ROOT / "MASTER_API_ERRORS.csv", errors)
    # The full automatic candidate index is distinct from the selected 30-case review.
    csv_write(ROOT / "MASTER_ERROR_ANALYSIS.csv", failures)
    csv_write(ROOT / "analysis/ALL_CANDIDATE_FAILURES.csv", failures)
    csv_write(ROOT / "MANUAL_FAILURE_REVIEW.csv", reviews, review_fields)
    csv_write(ROOT / "analysis/REVIEW_FIRST_30.csv", reviews, review_fields)
    csv_write(ROOT / "analysis/human_verification_review.csv", reviews, review_fields)
    csv_write(ROOT / "analysis/error_logs.csv", failures)
    csv_write(ROOT / "analysis/api_errors.csv", errors)
    category_counts = Counter(r["category"] for r in failures)
    csv_write(ROOT / "analysis/failure_summary.csv", [{"category": k, "count":v, "classification":"AI/deterministic draft; not participant review"} for k,v in sorted(category_counts.items())])

    quarantined = [r for r in rows if r["status"] == "quarantined"]
    csv_write(ROOT / "analysis/quarantined_records.csv", quarantined)
    comparisons = aggregate(rows)
    csv_write(ROOT / "analysis/run_summary.csv", comparisons)
    from analysis.expanded_audit import audit as audit_expanded
    expanded=audit_expanded(rows)
    json_write(ROOT/'analysis/EXPANDED_CAMPAIGN_AUDIT.json',expanded)
    csv_write(ROOT/'analysis/EXPANDED_CAMPAIGN_CELLS.csv',expanded['cells'])
    from analysis.friend2_audit import audit
    friend2=audit(rows)
    json_write(ROOT/'analysis/friend2_audit.json',friend2)
    if friend2['available']:
        csv_write(ROOT/'analysis/friend2_extension_cells.csv',friend2['cells'])
        csv_write(ROOT/'analysis/friend2_payload_repeats.csv',friend2['identical_payload_groups'])
        csv_write(ROOT/'analysis/friend2_phase2_cells.csv',friend2['phase2_cells'])
        csv_write(ROOT/'analysis/PHASE2_CASE_AUDIT.csv',[
            {k:r.get(k) for k in ['record_id','source_file','source_record','run_uid','model_requested','task','intervention','item_id','expected','finish_reason','stored_is_truncated','truncation_flag_disagrees','api_error','strict_correct','target_present_in_reasoning','source_input_matches_prompt','prompt_template_placeholder_present','source_code_budget_not_per_call_record','raw_text','reasoning_text']}
            for r in rows if r['run_kind']=='friend2_phase2'])
    json_write(ROOT / "analysis/error_analysis.json", {"scoring_version":SCORING_VERSION,"categories":dict(category_counts),"human_review_confirmed":len(reviewed)})

    source_checks = []
    for path in sorted((ROOT / "stimuli").glob("*.jsonl")):
        task = path.stem.split("_highprob")[0]
        mismatch = []
        total = 0
        for number, item in read_jsonl(path):
            total += 1
            if oracle_answer(task,item["input"]) != item["correct_output"]:
                mismatch.append(number)
        source_checks.append({"source_file":str(path.relative_to(ROOT)),"examples":total,"mismatch_rows":mismatch})
    assert all(not c["mismatch_rows"] for c in source_checks), "Dataset answer-key mismatch"
    json_write(ROOT / "analysis/dataset_checks.json", source_checks)

    pilot_files = [f for f in (ROOT/"runs").glob("acronym1_11*pilot.json")]
    mapping = {}
    for path in pilot_files:
        data=json.loads(path.read_text());mapping[data["model"]]={r["stimulus_id"]:r for r in data["results"] if not r.get("api_error")}
    matched = {}
    if all(m in mapping for m in ["qwen3-30b-a3b","qwen3-32b"]):
        a,b=mapping['qwen3-30b-a3b'],mapping['qwen3-32b'];ids=sorted(a.keys() & b.keys())
        matched={"matched_ids":ids,"n":len(ids),"stored_correct_30b":sum(bool(a[i]['correct']) for i in ids),"stored_correct_32b":sum(bool(b[i]['correct']) for i in ids),"interpretation":"Stored-flag comparison only; provenance and scoring differences prevent an architecture conclusion. No significance claim generated."}
    json_write(ROOT/"analysis/matched_comparison.json",matched)

    summary = {
        "generated_at":datetime.now(timezone.utc).isoformat(), "scoring_version":SCORING_VERSION,
        "top_level_source_records":len(rows), "records_by_contributor":dict(Counter(r['contributor'] for r in rows)),
        "reconstructed_user_test_items":len(reconstructed_tests), "planned_cipher_cells_not_executed":len(planned_cells),
        "returned_response_records":sum(not bool(r['api_error']) for r in rows),
        "final_request_error_records":sum(bool(r['api_error']) for r in rows), "retry_history_events":len(retries),
        "not_total_network_attempts":"Legacy retries are separate from top-level records; cancelled or unlogged calls may be absent.",
        "duplicate_imports_excluded":sum(bool(r['duplicate_of']) for r in rows), "quarantined_excerpt_records":len(quarantined),
        "usable_stored_response_records":len(usable), "strict_completed_stored_matches":sum(r['strict_correct'] is True for r in usable),
        "normalized_completed_matches":sum(r['normalized_correct'] is True for r in usable),
        "strict_failure_candidates":len(failures),"status_counts":dict(Counter(r['status'] for r in rows)),
        "participant_reviews_confirmed":len(reviewed), "selected_review_cases":len(reviews),
        "selected_review_wrong_completed_answers":sum(r['review_group']=='Wrong completed answer' for r in reviews),
        "selected_review_unfinished_responses":sum(r['review_group']=='Unfinished response' for r in reviews),
        "verified_two_checkpoint_comparison":False,
        "thinking_extension_established":False,"retrieval_extension_established":False,"twist_results_supplied":False,
        "matched_stored_flags":matched,
        "friend2_prompt_variant_evidence":friend2,
        "expanded_campaign_evidence":expanded,"simple_excel_completed_error_cases":5,
        "limitations":["Original pilot file missing; user pilot records reconstructed from chat.","Legacy final content and reasoning were not consistently separated.","Fourteen identical shortened cipher outputs are quarantined.","32B legacy pilot has uniform latency/token metadata and lacks API envelopes.","Checkpoint identities and effective thinking switches remain unverified.","Prompt-variant pilots are not verified thinking-off or web-retrieval controls.","Added phase-2 trials have no completed answers; source truncation flags conflict with finish reasons.","Phase-2 budgets are named in code/condition labels; actual per-call request configuration and usage are missing.","No twist evidence was supplied."]
    }
    json_write(ROOT / "MASTER_RUN_METADATA.json", summary)
    json_write(ROOT / "analysis/current_summary.json", summary)
    # Compatibility aliases are exact copies of corrected masters, not additional data.
    for name in ["MASTER_RESULTS.csv","MASTER_RAW_RESPONSES.jsonl","MASTER_API_ERRORS.csv","MASTER_ERROR_ANALYSIS.csv","MASTER_RUN_METADATA.json","MANUAL_FAILURE_REVIEW.csv"]:
        shutil.copyfile(ROOT/name, master/name)
    # Historical run packages remain untouched: their old scores are not current.
    (ROOT/"results/READ_CURRENT_OUTPUTS.txt").write_text("Current combined results are results/master/ and root MASTER_* files. Older per-run packages are historical and contain legacy scores. Do not count copies as new runs. See README.md.\n")
    json_write(ROOT/"analysis/source_hashes.json",{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'runs').glob('*.json'))})
    from analysis.documents import build_documents
    build_documents(ROOT, rows, comparisons, summary)
    from analysis.final_deck import build as build_final_deck
    build_final_deck(ROOT,rows,summary)
    from analysis.review_workbook import build as build_review_workbook
    build_review_workbook(ROOT,reviews)
    if __name__ == "__main__":
        print(json.dumps({k:summary[k] for k in ['top_level_source_records','returned_response_records','final_request_error_records','quarantined_excerpt_records','strict_completed_stored_matches','strict_failure_candidates','participant_reviews_confirmed']},indent=2))
    return summary


if __name__ == "__main__":
    main()
