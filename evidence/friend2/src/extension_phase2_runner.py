#!/usr/bin/env python3
"""
Extension Phase 2 Experiment Runner for 'Embers of Autoregression'
Tests three targeted hypotheses on qwen3-30b-a3b (MoE) and qwen3-32b (Dense):

1. Hypothesis A: Tokenization Intervention (Character-Spaced Stimuli)
   - Evaluates ROT-13 and ROT-12 with character-separated ciphers to isolate single-token processing and eliminate BPE subword fragmentation.
2. Hypothesis B: Test-Time Compute Budget Scaling (max_tokens=4096)
   - Evaluates ROT-12 with expanded token budget (4096 tokens) to test if headroom allows completion after latent solving.
3. Hypothesis C: In-Context Few-Shot Calibration (3-Shot Demonstrations)
   - Evaluates ROT-12 with 3 explicit few-shot demonstrations to test if in-context task probability overrides pre-training frequency deficits.

Logs full traces to logs/extension_phase2_runs.jsonl and summarizes in logs/extension_phase2_experiment_log.md.
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
DEFAULT_LOG_PATH = "/Users/ashwinanand/embers_replication/logs/extension_phase2_runs.jsonl"
DEFAULT_SUMMARY_PATH = "/Users/ashwinanand/embers_replication/logs/extension_phase2_experiment_log.md"

MODELS = ["qwen3-30b-a3b", "qwen3-32b"]


def levenshtein_distance(s1: str, s2: str) -> int:
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
    if clean_answer.startswith('"') and clean_answer.endswith('"') and len(clean_answer) >= 2:
        clean_answer = clean_answer[1:-1].strip()
    elif clean_answer.startswith("'") and clean_answer.endswith("'") and len(clean_answer) >= 2:
        clean_answer = clean_answer[1:-1].strip()

    return thinking.strip(), clean_answer, is_truncated


def evaluate_prediction(ground_truth: str, raw_content: str, clean_answer: str,
                        reasoning: str, finish_reason: str) -> dict:
    clean_gt = ground_truth.strip()
    if clean_gt.startswith('"') and clean_gt.endswith('"') and len(clean_gt) >= 2:
        clean_gt = clean_gt[1:-1].strip()

    gt_norm = clean_gt.lower()
    ans_norm = clean_answer.lower()
    raw_norm = (raw_content or "").lower()
    res_norm = (reasoning or "").lower()

    is_correct = (clean_gt in clean_answer) or (clean_gt in (raw_content or "")) or (gt_norm in ans_norm)
    exact_match = (clean_gt == clean_answer) or (gt_norm == ans_norm)
    ed = levenshtein_distance(clean_answer, clean_gt)
    norm_ed = ed / max(len(clean_gt), 1)
    gt_in_reasoning = gt_norm in res_norm

    if is_correct:
        fail_cat = "SUCCESS"
    elif finish_reason == "length" and not clean_answer:
        fail_cat = "TOKEN_EXHAUSTION_AFTER_SOLVING" if gt_in_reasoning else "TOKEN_EXHAUSTION_DURING_REASONING"
    elif gt_in_reasoning and clean_answer and not is_correct:
        fail_cat = "FORMAT_EXTRACTION_FAILURE"
    else:
        fail_cat = "ALGORITHMIC_DRIFT"

    return {
        "is_correct": bool(is_correct),
        "exact_match": bool(exact_match),
        "edit_distance": ed,
        "norm_edit_distance": round(norm_ed, 4),
        "clean_ground_truth": clean_gt,
        "gt_in_reasoning": bool(gt_in_reasoning),
        "failure_category": fail_cat
    }


def query_model(model: str, prompt: str, base_url: str = DEFAULT_BASE_URL,
                api_key: str = DEFAULT_API_KEY, max_tokens: int = 3500, max_retries: int = 6) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0
    }
    data = json.dumps(payload).encode("utf-8")
    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    delay = 2.0
    last_error = None

    for attempt in range(max_retries):
        t0 = time.time()
        try:
            req = urllib.request.Request(endpoint, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
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


def space_characters(s: str) -> str:
    """Inserts spaces between all characters to force single-token character processing."""
    return " ".join(list(s))


def build_phase2_jobs(num_items: int = 3) -> list:
    rot13_file = "/Users/ashwinanand/embers_replication/data/claim1_task_probability/shift_ciphers/shift_13.jsonl"
    rot12_file = "/Users/ashwinanand/embers_replication/data/claim1_task_probability/shift_ciphers/shift_12.jsonl"

    with open(rot13_file, "r", encoding="utf-8") as f:
        rot13_items = [json.loads(line) for line in f][:num_items]
    with open(rot12_file, "r", encoding="utf-8") as f:
        rot12_items = [json.loads(line) for line in f][:num_items]

    jobs = []

    for model in MODELS:
        # Hypothesis A: Tokenization Intervention (Character Spacing)
        for task_name, items, shift_k, exemplar_raw in [
            ("rot-13", rot13_items, 13, "F g n l   u r e r !"),
            ("rot-12", rot12_items, 12, "E f m k   t q d q !")
        ]:
            for idx, item in enumerate(items):
                spaced_input = space_characters(item["input"])
                prompt = (
                    f"Rot-{shift_k} is a cipher in which each letter is shifted {shift_k} positions forward in the alphabet. "
                    "To prevent token grouping and facilitate character-level analysis, each character in the message is separated by a space.\n"
                    "For example, here is a message written in rot-{shift_k} along with the original text:\n"
                    f"Rot-{shift_k} text: \"{exemplar_raw}\"\n"
                    "Original text: \"Stay here!\"\n\n"
                    f"Here is another message in rot-{shift_k}. Decode this message to produce the original text (output standard unspaced natural text):\n"
                    f"Rot-{shift_k} text: \"{spaced_input}\"\n"
                    "Original text:"
                )
                uid = f"p2::{model}::hypA_char_spaced::{task_name}::{idx}"
                jobs.append({
                    "run_uid": uid,
                    "hypothesis": "Hypothesis A (Tokenization Intervention)",
                    "model": model,
                    "task": task_name,
                    "condition": "char_spaced_stimuli",
                    "item_index": idx,
                    "prompt": prompt,
                    "ground_truth": item["correct_output"],
                    "max_tokens": 3500
                })

        # Hypothesis B: Test-Time Compute Budget Scaling (max_tokens=4096)
        for idx, item in enumerate(rot12_items):
            prompt = item["instruction_plus_input"]
            uid = f"p2::{model}::hypB_compute_4096::rot-12::{idx}"
            jobs.append({
                "run_uid": uid,
                "hypothesis": "Hypothesis B (Compute Scaling 4096)",
                "model": model,
                "task": "rot-12",
                "condition": "budget_4096_tokens",
                "item_index": idx,
                "prompt": prompt,
                "ground_truth": item["correct_output"],
                "max_tokens": 4096
            })

        # Hypothesis C: In-Context Few-Shot Calibration (3-Shot Demonstrations)
        for idx, item in enumerate(rot12_items):
            fewshot_prompt = (
                "Rot-12 is a cipher in which each letter is shifted 12 positions forward in the alphabet.\n"
                "Here are some examples of messages written in rot-12 along with the original decoded text:\n\n"
                "Example 1:\n"
                "Rot-12 text: \"Efmk tqdq!\"\n"
                "Original text: \"Stay here!\"\n\n"
                "Example 2:\n"
                "Rot-12 text: \"Tqxxa iadxp!\"\n"
                "Original text: \"Hello world!\"\n\n"
                "Example 3:\n"
                "Rot-12 text: \"Saap yadzuzs!\"\n"
                "Original text: \"Good morning!\"\n\n"
                "Here is another message in rot-12. Decode this message to produce the original text:\n"
                f"Rot-12 text: \"{item['input']}\"\n"
                "Original text:"
            )
            uid = f"p2::{model}::hypC_fewshot_3shot::rot-12::{idx}"
            jobs.append({
                "run_uid": uid,
                "hypothesis": "Hypothesis C (Few-Shot Calibration)",
                "model": model,
                "task": "rot-12",
                "condition": "fewshot_3shot",
                "item_index": idx,
                "prompt": fewshot_prompt,
                "ground_truth": item["correct_output"],
                "max_tokens": 3500
            })

    return jobs


def load_existing_uids(log_path: str) -> set:
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


def generate_phase2_summary(log_path: str, summary_path: str):
    if not os.path.exists(log_path):
        return
    runs_by_uid = {}
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rec = json.loads(line)
                    uid = rec.get("run_uid")
                    if uid:
                        if uid not in runs_by_uid or rec.get("status") == "success":
                            runs_by_uid[uid] = rec
                except Exception:
                    pass

    runs = list(runs_by_uid.values())
    if not runs:
        return

    from collections import defaultdict
    grid = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        "total": 0, "correct": 0, "exact": 0, "gt_res": 0, "latencies": [], "eds": []
    })))

    for r in runs:
        hyp = r.get("hypothesis", "unknown")
        m = r.get("model", "unknown")
        cond = f"{r.get('task')}::{r.get('condition')}"
        st = grid[hyp][m][cond]
        st["total"] += 1
        if r.get("is_correct"):
            st["correct"] += 1
        if r.get("exact_match"):
            st["exact"] += 1
        if r.get("gt_in_reasoning"):
            st["gt_res"] += 1
        st["latencies"].append(r.get("latency_seconds", 0.0))
        st["eds"].append(r.get("edit_distance", 0))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Extension Phase 2 Experiment Log: Advanced Hypotheses Evaluation",
        f"**Generated:** {now_str}",
        f"**Total Runs Logged:** {len(runs)} | **Log Path:** `{log_path}`",
        "",
        "## 1. Hypothesis Testing Grid Summary",
        "| Hypothesis | Model | Task & Condition | N | Substring Acc | Exact Match | Reasoning Solved | Avg Latency (s) | Avg Edit Dist |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for hyp in sorted(grid.keys()):
        for m in sorted(grid[hyp].keys()):
            for cond in sorted(grid[hyp][m].keys()):
                st = grid[hyp][m][cond]
                n = st["total"]
                acc = (st["correct"] / n) * 100 if n else 0
                ex = (st["exact"] / n) * 100 if n else 0
                rs = (st["gt_res"] / n) * 100 if n else 0
                alat = sum(st["latencies"]) / n if n else 0
                aed = sum(st["eds"]) / n if n else 0
                lines.append(f"| {hyp} | `{m}` | `{cond}` | {n} | **{acc:.1f}%** ({st['correct']}/{n}) | {ex:.1f}% | {rs:.1f}% | {alat:.2f}s | {aed:.2f} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Hypothesis-by-Hypothesis Empirical Verification",
        "",
        "### Hypothesis A: Tokenization Intervention (Character Spacing)",
        "- Evaluates whether inserting spaces between every ciphertext letter eliminates BPE token boundary fragmentation.",
        "",
        "### Hypothesis B: Test-Time Compute Budget Scaling (4096 Tokens)",
        "- Evaluates whether giving thinking models 4096 tokens allows latent-solved cases to reach final answer emission.",
        "",
        "### Hypothesis C: In-Context Few-Shot Calibration (3-Shot Demonstrations)",
        "- Evaluates whether 3 explicit in-context demonstrations can elevate local task probability and overcome pre-training frequency deficits.",
        "",
        "---",
        "",
        "## 3. Sample Runs Master Table",
        "| Run UID | Model | Hypothesis | Condition | Result | Category | Latency (s) | Answer Preview |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ])

    for r in sorted(runs, key=lambda x: (x.get("hypothesis", ""), x.get("model", ""), x.get("task", ""), x.get("item_index", 0))):
        res = "PASS" if r.get("is_correct") else "FAIL"
        ans_p = (r.get("answer") or "[EMPTY]")[:45].replace("|", " ").replace("\n", " ")
        lines.append(f"| `{r.get('run_uid')}` | `{r.get('model')}` | {r.get('hypothesis')} | `{r.get('condition')}` | **{res}** | `{r.get('failure_category')}` | {r.get('latency_seconds'):.2f}s | {ans_p} |")

    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def run_phase2(jobs: list, log_path: str = DEFAULT_LOG_PATH, summary_path: str = DEFAULT_SUMMARY_PATH,
               workers: int = 2):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    completed_uids = load_existing_uids(log_path)
    print(f"Loaded {len(completed_uids)} previously completed Phase 2 runs.")

    pending_jobs = [j for j in jobs if j["run_uid"] not in completed_uids]
    print(f"Total jobs: {len(jobs)} | Remaining: {len(pending_jobs)}")

    if not pending_jobs:
        print("All Phase 2 jobs already completed.")
        generate_phase2_summary(log_path, summary_path)
        return

    def process_job(job: dict) -> dict:
        t0 = datetime.now(timezone.utc).isoformat()
        res = query_model(job["model"], job["prompt"], max_tokens=job.get("max_tokens", 3500))
        raw_content = res.get("raw_content", "")
        reasoning_content = res.get("reasoning_content", "")
        thinking, clean_ans, is_truncated = extract_reasoning_and_answer(raw_content, reasoning_content)

        eval_res = evaluate_prediction(job["ground_truth"], raw_content, clean_ans, thinking, res.get("finish_reason", "unknown"))

        record = {
            "timestamp": t0,
            "run_uid": job["run_uid"],
            "hypothesis": job["hypothesis"],
            "model": job["model"],
            "task": job["task"],
            "condition": job["condition"],
            "item_index": job["item_index"],
            "prompt": job["prompt"],
            "ground_truth": job["ground_truth"],
            "clean_ground_truth": eval_res["clean_ground_truth"],
            "raw_content": raw_content,
            "reasoning": thinking,
            "answer": clean_ans,
            "finish_reason": res.get("finish_reason", "unknown"),
            "is_truncated": is_truncated,
            "is_correct": eval_res["is_correct"],
            "exact_match": eval_res["exact_match"],
            "edit_distance": eval_res["edit_distance"],
            "norm_edit_distance": eval_res["norm_edit_distance"],
            "gt_in_reasoning": eval_res["gt_in_reasoning"],
            "failure_category": eval_res["failure_category"],
            "latency_seconds": res.get("latency_seconds", 0.0),
            "attempts": res.get("attempts", 1),
            "status": res.get("status", "unknown"),
            "error": res.get("error", None)
        }
        return record

    total_pending = len(pending_jobs)
    done_count = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []
        for i, job in enumerate(pending_jobs):
            time.sleep(0.5)
            futures.append(pool.submit(process_job, job))

        for future in as_completed(futures):
            done_count += 1
            try:
                record = future.result()
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
                icon = "PASS" if record["is_correct"] else "FAIL"
                ans_str = record["answer"][:30] if record["answer"] else f"[{record['failure_category']}]"
                print(f"[{done_count}/{total_pending}] {icon} | {record['model']} | {record['hypothesis'][:12]} | {record['task']} | {ans_str}")
            except Exception as e:
                print(f"Phase 2 worker error: {e}")

            if done_count % 3 == 0 or done_count == total_pending:
                generate_phase2_summary(log_path, summary_path)

    generate_phase2_summary(log_path, summary_path)
    print(f"Extension Phase 2 complete. Summary written to {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Extension Phase 2 Runner for Embers Replication")
    parser.add_argument("--num-items", type=int, default=3, help="Items per condition (default 3)")
    parser.add_argument("--workers", type=int, default=2, help="Concurrency workers (default 2)")
    parser.add_argument("--log-path", type=str, default=DEFAULT_LOG_PATH)
    parser.add_argument("--summary-path", type=str, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args()

    jobs = build_phase2_jobs(num_items=args.num_items)
    run_phase2(jobs, log_path=args.log_path, summary_path=args.summary_path, workers=args.workers)


if __name__ == "__main__":
    main()
