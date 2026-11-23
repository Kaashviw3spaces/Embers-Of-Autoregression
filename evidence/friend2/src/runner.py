#!/usr/bin/env python3
"""
Automated Replication Runner for 'Embers of Autoregression' (McCoy et al., PNAS 2024 / arXiv:2309.13638)
Evaluates Qwen3 (qwen3-30b-a3b) on:
  - Claim 1: Task Probability (canonical high-probability vs non-canonical low-probability tasks)
  - Claim 2: Output Probability (high vs medium vs low vs adversarial target sequence probabilities)

Features:
  - Resilient API caller with exponential backoff and jitter on HTTP 429/5xx
  - Thinking model parsing: extracts reasoning from message.reasoning_content or <think> tags
  - Dual-metric scoring: Substring containment (McCoy et al.) and Levenshtein edit distance
  - Advanced failure categorization: Token Exhaustion, Prior Intrusion, Algorithmic Drift
  - Resumable append-only logging to logs/raw_runs.jsonl
  - Live markdown synthesis generation to logs/experiment_log.md
"""

import os
import sys
import json
import time
import random
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_BASE_URL = "http://10.7.25.115:30400/v1"
DEFAULT_API_KEY = "[REDACTED_KEY]"
DEFAULT_MODEL = "qwen3-30b-a3b"
DEFAULT_LOG_PATH = "/Users/ashwinanand/embers_replication/logs/raw_runs.jsonl"
DEFAULT_SUMMARY_PATH = "/Users/ashwinanand/embers_replication/logs/experiment_log.md"


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute standard Levenshtein edit distance between s1 and s2."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def extract_reasoning_and_answer(raw_content: str, reasoning_content: str = None) -> tuple[str, str, bool]:
    """
    Extracts (reasoning_trace, clean_answer, is_truncated) from Qwen3 response.
    Handles dual-field API response (reasoning_content) as well as inline <think> tags.
    """
    thinking = reasoning_content or ""
    answer = raw_content or ""
    is_truncated = False

    if "<think>" in answer:
        if "</think>" in answer:
            parts = answer.split("</think>", 1)
            inline_think = parts[0].replace("<think>", "").strip()
            thinking = f"{thinking}\n{inline_think}".strip()
            answer = parts[1].strip()
        else:
            inline_think = answer.replace("<think>", "").strip()
            thinking = f"{thinking}\n{inline_think}".strip()
            answer = ""
            is_truncated = True

    clean_answer = answer.strip()
    # Strip wrapping quotes if present
    if clean_answer.startswith('"') and clean_answer.endswith('"') and len(clean_answer) >= 2:
        clean_answer = clean_answer[1:-1].strip()
    elif clean_answer.startswith("'") and clean_answer.endswith("'") and len(clean_answer) >= 2:
        clean_answer = clean_answer[1:-1].strip()

    return thinking.strip(), clean_answer, is_truncated


def categorize_failure(is_correct: bool, finish_reason: str, gt: str, answer: str, reasoning: str) -> str:
    """
    Categorizes the run outcome into academic failure profiles:
      - SUCCESS
      - TOKEN_EXHAUSTION_DURING_REASONING
      - PRIOR_INTRUSION
      - ALGORITHMIC_DRIFT
      - FORMAT_EXTRACTION_FAILURE
    """
    if is_correct:
        return "SUCCESS"
    
    clean_gt = gt.strip().strip('"').strip("'").lower()
    clean_ans = answer.strip().strip('"').strip("'").lower()
    clean_res = reasoning.strip().strip('"').strip("'").lower()

    if finish_reason == "length" and not clean_ans:
        if clean_gt in clean_res:
            return "TOKEN_EXHAUSTION_AFTER_SOLVING"
        return "TOKEN_EXHAUSTION_DURING_REASONING"

    if clean_gt in clean_res and clean_ans and clean_gt not in clean_ans:
        return "FORMAT_EXTRACTION_FAILURE"

    # Prior intrusion check: did the model output an English word/sentence that doesn't match the cipher
    if len(clean_ans) > 5 and any(word in clean_ans for word in ["government", "people", "would", "about", "could"]):
        return "PRIOR_INTRUSION"

    return "ALGORITHMIC_DRIFT"


def evaluate_prediction(ground_truth: str, raw_content: str, clean_answer: str,
                        reasoning: str, finish_reason: str) -> dict:
    """
    Evaluates prediction using McCoy et al. protocol:
      - is_correct: Substring match of ground truth inside answer or raw content
      - exact_match: Clean stripped case-insensitive match
      - edit_distance: Levenshtein distance to clean_answer
      - norm_edit_distance: Distance normalized by len(ground_truth)
      - gt_in_reasoning: Checks if model solved problem inside reasoning trace
      - failure_category: Diagnostic taxonomy
    """
    clean_gt = ground_truth.strip()
    if clean_gt.startswith('"') and clean_gt.endswith('"') and len(clean_gt) >= 2:
        clean_gt = clean_gt[1:-1].strip()

    gt_norm = clean_gt.lower()
    ans_norm = clean_answer.lower()
    raw_norm = (raw_content or "").lower()
    res_norm = (reasoning or "").lower()

    # McCoy et al substring containment check
    is_correct = (clean_gt in clean_answer) or (clean_gt in (raw_content or "")) or (gt_norm in ans_norm)
    exact_match = (clean_gt == clean_answer) or (gt_norm == ans_norm)
    ed = levenshtein_distance(clean_answer, clean_gt)
    norm_ed = ed / max(len(clean_gt), 1)
    gt_in_reasoning = gt_norm in res_norm

    fail_cat = categorize_failure(is_correct, finish_reason, clean_gt, clean_answer, reasoning)

    return {
        "is_correct": bool(is_correct),
        "exact_match": bool(exact_match),
        "edit_distance": ed,
        "norm_edit_distance": round(norm_ed, 4),
        "clean_ground_truth": clean_gt,
        "gt_in_reasoning": bool(gt_in_reasoning),
        "failure_category": fail_cat
    }


class Qwen3Runner:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, api_key: str = DEFAULT_API_KEY,
                 model: str = DEFAULT_MODEL, max_tokens: int = 3200, temperature: float = 0.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.endpoint = f"{self.base_url}/chat/completions"

    def query(self, prompt: str, max_retries: int = 6) -> dict:
        """
        Sends query to Qwen3 endpoint with exponential backoff and jitter on 429/5xx.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        data = json.dumps(payload).encode("utf-8")

        delay = 2.0
        last_error = None

        for attempt in range(max_retries):
            t0 = time.time()
            try:
                req = urllib.request.Request(self.endpoint, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=90) as resp:
                    latency = round(time.time() - t0, 3)
                    res = json.loads(resp.read().decode("utf-8"))
                    choice = res["choices"][0]
                    msg = choice.get("message", {})
                    raw_content = msg.get("content", "") or ""
                    reasoning_content = msg.get("reasoning_content", "") or ""
                    finish_reason = choice.get("finish_reason", "unknown")
                    usage = res.get("usage", {})

                    return {
                        "status": "success",
                        "raw_content": raw_content,
                        "reasoning_content": reasoning_content,
                        "finish_reason": finish_reason,
                        "usage": usage,
                        "latency_seconds": latency,
                        "attempts": attempt + 1
                    }
            except urllib.error.HTTPError as e:
                latency = round(time.time() - t0, 3)
                last_error = f"HTTP {e.code}: {e.reason}"
                if e.code in (429, 500, 502, 503, 504):
                    jitter = random.uniform(0.5, 1.5)
                    sleep_time = min(35.0, delay + jitter)
                    time.sleep(sleep_time)
                    delay *= 2.0
                else:
                    break
            except Exception as e:
                latency = round(time.time() - t0, 3)
                last_error = str(e)
                jitter = random.uniform(0.5, 1.5)
                time.sleep(min(35.0, delay + jitter))
                delay *= 2.0

        return {
            "status": "error",
            "error": last_error,
            "raw_content": "",
            "reasoning_content": "",
            "finish_reason": "error",
            "usage": {},
            "latency_seconds": 0.0,
            "attempts": max_retries
        }


def get_item_uid(item: dict) -> str:
    """Produces unique identifier for experiment item."""
    claim = item.get("claim", "unknown")
    task = item.get("task_name", item.get("task_category", "task"))
    cond = item.get("condition_name", item.get("example_type", "cond"))
    idx = item.get("item_index", 0)
    return f"{claim}::{task}::{cond}::{idx}"


def load_existing_run_uids(log_path: str) -> set:
    """Loads set of already completed item UIDs from JSONL log."""
    completed = set()
    if not os.path.exists(log_path):
        return completed
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                uid = rec.get("run_uid")
                if uid and rec.get("status") == "success":
                    completed.add(uid)
            except Exception:
                pass
    return completed


def generate_experiment_markdown(log_path: str, summary_path: str):
    """
    Reads raw_runs.jsonl and produces a comprehensive Markdown synthesis report.
    """
    if not os.path.exists(log_path):
        return

    runs = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    runs.append(json.loads(line))
                except Exception:
                    pass

    if not runs:
        return

    # Aggregate by condition
    by_claim = {"claim1_task_probability": {}, "claim2_output_probability": {}}
    failure_counts = {}

    for r in runs:
        claim = r.get("claim", "other")
        task = r.get("task_name", r.get("task_category", "task"))
        cond = r.get("condition_name", "cond")
        role = r.get("hypothesis_role", r.get("output_probability_tier", ""))

        cat = r.get("failure_category", "UNKNOWN")
        failure_counts[cat] = failure_counts.get(cat, 0) + 1

        if claim not in by_claim:
            by_claim[claim] = {}
        if task not in by_claim[claim]:
            by_claim[claim][task] = {}
        if cond not in by_claim[claim][task]:
            by_claim[claim][task][cond] = {
                "role": role,
                "total": 0,
                "correct": 0,
                "exact": 0,
                "gt_in_res": 0,
                "edit_dists": [],
                "latencies": []
            }

        st = by_claim[claim][task][cond]
        st["total"] += 1
        if r.get("is_correct"):
            st["correct"] += 1
        if r.get("exact_match"):
            st["exact"] += 1
        if r.get("gt_in_reasoning"):
            st["gt_in_res"] += 1
        st["edit_dists"].append(r.get("edit_distance", 0))
        st["latencies"].append(r.get("latency_seconds", 0.0))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Replication Experiment Log: Qwen3 on 'Embers of Autoregression'",
        f"**Generated:** {now_str}",
        f"**Model:** `{DEFAULT_MODEL}` | **Endpoint:** `{DEFAULT_BASE_URL}`",
        f"**Total Runs Logged:** {len(runs)} | **Raw Log File:** `{log_path}`",
        "",
        "## Diagnostic Taxonomy of Outcomes",
        "| Category | Count | Percentage | Description |",
        "| :--- | :--- | :--- | :--- |"
    ]

    total_runs = len(runs)
    for cat, cnt in sorted(failure_counts.items(), key=lambda x: -x[1]):
        pct = (cnt / total_runs) * 100
        desc = ""
        if cat == "SUCCESS":
            desc = "Model emitted correct ground truth substring"
        elif cat == "TOKEN_EXHAUSTION_AFTER_SOLVING":
            desc = "Model deduced answer in reasoning but exceeded token budget before emitting content"
        elif cat == "TOKEN_EXHAUSTION_DURING_REASONING":
            desc = "Model spent full token budget struggling with arithmetic/cipher without finding answer"
        elif cat == "PRIOR_INTRUSION":
            desc = "Model language prior overrode cipher algorithm and emitted standard web English"
        elif cat == "ALGORITHMIC_DRIFT":
            desc = "Arithmetic error or offset shift error during step-by-step substitution"
        elif cat == "FORMAT_EXTRACTION_FAILURE":
            desc = "Ground truth present in raw output but masked by formatting markdown"
        lines.append(f"| `{cat}` | {cnt} | {pct:.1f}% | {desc} |")

    lines.extend([
        "",
        "---",
        "",
        "## 1. Claim 1: Task Probability (Canonical vs Non-Canonical Tasks)",
        "Holding formal problem structure constant, accuracy is expected to drop significantly on rare task variants.",
        "",
        "| Task Category | Condition Name | Variant Role | N | Accuracy (Substring) | Exact Match | Reasoning Solved | Avg Edit Dist | Avg Latency (s) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ])

    c1 = by_claim.get("claim1_task_probability", {})
    for task, conds in sorted(c1.items()):
        for cond, st in sorted(conds.items()):
            n = st["total"]
            acc = (st["correct"] / n) * 100 if n else 0
            ex = (st["exact"] / n) * 100 if n else 0
            res_sol = (st["gt_in_res"] / n) * 100 if n else 0
            aed = sum(st["edit_dists"]) / n if n else 0
            alat = sum(st["latencies"]) / n if n else 0
            lines.append(f"| `{task}` | `{cond}` | {st['role']} | {n} | **{acc:.1f}%** ({st['correct']}/{n}) | {ex:.1f}% | {res_sol:.1f}% | {aed:.2f} | {alat:.2f}s |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Claim 2: Output Probability (Natural Language Prior Bias)",
        "Holding task and algorithm constant, accuracy drops as target text shifts from high probability to low probability or adversarial.",
        "",
        "| Task Category | Condition Name | Output Tier | N | Accuracy (Substring) | Exact Match | Reasoning Solved | Avg Edit Dist | Avg Latency (s) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ] )

    c2 = by_claim.get("claim2_output_probability", {})
    for task, conds in sorted(c2.items()):
        for cond, st in sorted(conds.items()):
            n = st["total"]
            acc = (st["correct"] / n) * 100 if n else 0
            ex = (st["exact"] / n) * 100 if n else 0
            res_sol = (st["gt_in_res"] / n) * 100 if n else 0
            aed = sum(st["edit_dists"]) / n if n else 0
            alat = sum(st["latencies"]) / n if n else 0
            lines.append(f"| `{task}` | `{cond}` | {st['role']} | {n} | **{acc:.1f}%** ({st['correct']}/{n}) | {ex:.1f}% | {res_sol:.1f}% | {aed:.2f} | {alat:.2f}s |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Notable Failure Case Samples for Audit",
        "Sample failures with reasoning traces and target mismatches for verifier classification:",
        ""
    ])

    failures = [r for r in runs if not r.get("is_correct")]
    for i, f_item in enumerate(failures[:30]):
        lines.append(f"### Failure #{i+1}: `{f_item.get('task_name')}` - `{f_item.get('condition_name')}`")
        lines.append(f"- **Category:** `{f_item.get('failure_category')}`")
        lines.append(f"- **Ground Truth:** `{f_item.get('ground_truth')}`")
        lines.append(f"- **Answer:** `{f_item.get('answer') or '[EMPTY - TOKEN EXHAUSTION]'}`")
        lines.append(f"- **Finish Reason:** `{f_item.get('finish_reason')}` | **Edit Distance:** {f_item.get('edit_distance')}")
        reasoning_snippet = (f_item.get("reasoning") or "").replace("\n", " ")[:250]
        lines.append(f"- **Reasoning Excerpt:** *{reasoning_snippet}...*")
        lines.append("")

    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def run_benchmark(items: list, runner: Qwen3Runner, log_path: str, summary_path: str,
                  workers: int = 2, delay_between: float = 0.5):
    """
    Executes benchmark items, logging incrementally to log_path and updating summary_path.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    completed_uids = load_existing_run_uids(log_path)
    print(f"Loaded {len(completed_uids)} previously completed runs from {log_path}.")

    pending_items = [item for item in items if get_item_uid(item) not in completed_uids]
    print(f"Total items in batch: {len(items)} | Remaining to run: {len(pending_items)}")

    if not pending_items:
        print("All items in this batch are already completed.")
        generate_experiment_markdown(log_path, summary_path)
        return

    def process_item(item: dict) -> dict:
        uid = get_item_uid(item)
        prompt = item.get("instruction_plus_input", "")
        gt = item.get("correct_output", "")

        t0 = datetime.now(timezone.utc).isoformat()
        res = runner.query(prompt)

        raw_content = res.get("raw_content", "")
        reasoning_content = res.get("reasoning_content", "")
        thinking, clean_ans, is_truncated = extract_reasoning_and_answer(raw_content, reasoning_content)

        metrics = evaluate_prediction(gt, raw_content, clean_ans, thinking, res.get("finish_reason", "unknown"))

        record = {
            "timestamp": t0,
            "run_uid": uid,
            "claim": item.get("claim", "unknown"),
            "task_name": item.get("task_name", item.get("task_category", "task")),
            "condition_name": item.get("condition_name", item.get("example_type", "cond")),
            "hypothesis_role": item.get("hypothesis_role", item.get("output_probability_tier", "")),
            "item_index": item.get("item_index", 0),
            "prompt": prompt,
            "ground_truth": gt,
            "clean_ground_truth": metrics["clean_ground_truth"],
            "raw_content": raw_content,
            "reasoning": thinking,
            "answer": clean_ans,
            "finish_reason": res.get("finish_reason", "unknown"),
            "is_truncated": is_truncated,
            "is_correct": metrics["is_correct"],
            "exact_match": metrics["exact_match"],
            "edit_distance": metrics["edit_distance"],
            "norm_edit_distance": metrics["norm_edit_distance"],
            "gt_in_reasoning": metrics["gt_in_reasoning"],
            "failure_category": metrics["failure_category"],
            "latency_seconds": res.get("latency_seconds", 0.0),
            "attempts": res.get("attempts", 1),
            "status": res.get("status", "unknown"),
            "error": res.get("error", None)
        }
        return record

    total_pending = len(pending_items)
    done_count = 0

    if workers <= 1:
        for idx, item in enumerate(pending_items):
            record = process_item(item)
            done_count += 1
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            
            correct_icon = "PASS" if record["is_correct"] else "FAIL"
            ans_disp = record["answer"][:30] if record["answer"] else f"[{record['failure_category']}]"
            print(f"[{done_count}/{total_pending}] {correct_icon} | {record['task_name']} ({record['condition_name']}) | Ans: {ans_disp} | Cat: {record['failure_category']}")
            
            if done_count % 5 == 0 or done_count == total_pending:
                generate_experiment_markdown(log_path, summary_path)

            if delay_between > 0:
                time.sleep(delay_between)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # We submit items staggered to avoid burst 429
            futures = []
            for i, item in enumerate(pending_items):
                time.sleep(0.3)
                futures.append(pool.submit(process_item, item))

            for future in as_completed(futures):
                done_count += 1
                try:
                    record = future.result()
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(record) + "\n")
                    correct_icon = "PASS" if record["is_correct"] else "FAIL"
                    ans_disp = record["answer"][:30] if record["answer"] else f"[{record['failure_category']}]"
                    print(f"[{done_count}/{total_pending}] {correct_icon} | {record['task_name']} ({record['condition_name']}) | Cat: {record['failure_category']}")
                except Exception as e:
                    print(f"Worker exception: {e}")

                if done_count % 5 == 0 or done_count == total_pending:
                    generate_experiment_markdown(log_path, summary_path)

    generate_experiment_markdown(log_path, summary_path)
    print(f"Benchmark finished. Results logged to {log_path} and summarized in {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Replication Runner for Embers of Autoregression")
    parser.add_argument("--mode", type=str, choices=["smoke", "claim1", "claim2", "all"], default="smoke",
                        help="Benchmark mode to run")
    parser.add_argument("--limit-per-condition", type=int, default=None,
                        help="Limit number of items per condition (e.g. 5 or 10)")
    parser.add_argument("--workers", type=int, default=2,
                        help="Concurrency limit (default 2 with stagger)")
    parser.add_argument("--max-tokens", type=int, default=3200,
                        help="Max tokens for thinking model (default 3200)")
    parser.add_argument("--log-path", type=str, default=DEFAULT_LOG_PATH,
                        help="Path to raw_runs.jsonl output")
    parser.add_argument("--summary-path", type=str, default=DEFAULT_SUMMARY_PATH,
                        help="Path to experiment_log.md summary")
    args = parser.parse_args()

    data_dir = "/Users/ashwinanand/embers_replication/data/benchmark_subsets"
    items_to_run = []

    if args.mode == "smoke":
        smoke_file = os.path.join(data_dir, "smoke_test_suite.jsonl")
        with open(smoke_file, "r", encoding="utf-8") as f:
            items_to_run = [json.loads(line) for line in f]
    elif args.mode == "claim1":
        c1_file = os.path.join(data_dir, "claim1_core_benchmark.jsonl")
        with open(c1_file, "r", encoding="utf-8") as f:
            items_to_run = [json.loads(line) for line in f]
    elif args.mode == "claim2":
        c2_file = os.path.join(data_dir, "claim2_core_benchmark.jsonl")
        with open(c2_file, "r", encoding="utf-8") as f:
            items_to_run = [json.loads(line) for line in f]
    elif args.mode == "all":
        c1_file = os.path.join(data_dir, "claim1_core_benchmark.jsonl")
        c2_file = os.path.join(data_dir, "claim2_core_benchmark.jsonl")
        with open(c1_file, "r", encoding="utf-8") as f:
            items_to_run.extend([json.loads(line) for line in f])
        with open(c2_file, "r", encoding="utf-8") as f:
            items_to_run.extend([json.loads(line) for line in f])

    if args.limit_per_condition is not None:
        filtered = []
        counts = {}
        for it in items_to_run:
            cond = it.get("condition_name", "default")
            counts[cond] = counts.get(cond, 0) + 1
            if counts[cond] <= args.limit_per_condition:
                filtered.append(it)
        items_to_run = filtered
        print(f"Applied limit {args.limit_per_condition} per condition. Total items to run: {len(items_to_run)}")

    runner = Qwen3Runner(max_tokens=args.max_tokens)
    run_benchmark(items_to_run, runner, args.log_path, args.summary_path, workers=args.workers)


if __name__ == "__main__":
    main()
