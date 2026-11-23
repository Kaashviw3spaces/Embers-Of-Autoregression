#!/usr/bin/env python3
"""
Extension Experiment Runner for 'Embers of Autoregression'
Evaluates:
  Models:
    - qwen3-30b-a3b (MoE reasoning model)
    - qwen3-32b (Dense reasoning model)
  Tasks:
    - ROT-13 (Canonical shift cipher, high pre-training task probability)
    - ROT-12 (Non-canonical shift cipher, low pre-training task probability)
  Evaluation Modes:
    1. direct_mode: Prompt instructed to output only decoded plaintext directly without preamble.
    2. thinking_mode: Standard zero-shot thinking prompt (max_tokens=3500).
    3. retrieved_guidance: Injects explicit letter-by-letter cipher substitution lookup tables.

Tracks:
  - Substring accuracy (McCoy et al.)
  - Exact match accuracy
  - Levenshtein edit distance & normalized edit distance
  - Reasoning trace length & token exhaustion vs completion
  - Latency per run
  - Outputs incrementally to logs/extension_runs.jsonl
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
DEFAULT_LOG_PATH = "/Users/ashwinanand/embers_replication/logs/extension_runs.jsonl"
DEFAULT_SUMMARY_PATH = "/Users/ashwinanand/embers_replication/logs/extension_experiment_log.md"

MODELS = ["qwen3-30b-a3b", "qwen3-32b"]
MODES = ["direct_mode", "thinking_mode", "retrieved_guidance"]

ROT13_TABLE = """[Cipher Reference Documentation: ROT-13 Substitution Table]
To decode ROT-13 (shift 13 positions backward/forward):
A<->N, B<->O, C<->P, D<->Q, E<->R, F<->S, G<->T, H<->U, I<->V, J<->W, K<->X, L<->Y, M<->Z
a<->n, b<->o, c<->p, d<->q, e<->r, f<->s, g<->t, h<->u, i<->v, j<->w, k<->x, l<->y, m<->z
"""

ROT12_TABLE = """[Cipher Reference Documentation: ROT-12 Decoding Table]
To decode ROT-12 (shift 12 positions backward in alphabet / shift 14 positions forward):
A->O, B->P, C->Q, D->R, E->S, F->T, G->U, H->V, I->W, J->X, K->Y, L->Z, M->A, N->B, O->C, P->D, Q->E, R->F, S->G, T->H, U->I, V->J, W->K, X->L, Y->M, Z->N
a->o, b->p, c->q, d->r, e->s, f->t, g->u, h->v, i->w, j->x, k->y, l->z, m->a, n->b, o->c, p->d, q->e, r->f, s->g, t->h, u->i, v->j, w->k, x->l, y->m, z->n
"""


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


def build_prompt_for_mode(base_instruction_plus_input: str, task: str, mode: str) -> str:
    """
    Constructs the prompt according to the target experimental mode.
    """
    if mode == "thinking_mode":
        return base_instruction_plus_input
    elif mode == "direct_mode":
        return (
            f"{base_instruction_plus_input}\n\n"
            "CRITICAL INSTRUCTION: Output ONLY the final decoded plaintext string directly. "
            "Do NOT include any introduction, explanations, scratchpad work, or quotation marks. "
            "Output the decoded text immediately:"
        )
    elif mode == "retrieved_guidance":
        table = ROT13_TABLE if "13" in task else ROT12_TABLE
        return (
            f"{table}\n"
            "Use the exact substitution reference table above to look up each letter and decode the following message:\n\n"
            f"{base_instruction_plus_input}"
        )
    return base_instruction_plus_input


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


def generate_extension_markdown(log_path: str, summary_path: str):
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

    # Structure: by model -> by task -> by mode
    grid = {}
    for r in runs:
        m = r.get("model", "unknown")
        t = r.get("task", "unknown")
        mode = r.get("mode", "unknown")
        if m not in grid:
            grid[m] = {}
        if t not in grid[m]:
            grid[m][t] = {}
        if mode not in grid[m][t]:
            grid[m][t][mode] = {"total": 0, "correct": 0, "exact": 0, "gt_res": 0, "latencies": [], "eds": []}

        st = grid[m][t][mode]
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
        "# Extension Experiment Log: Model Architecture & Prompting Paradigms",
        f"**Generated:** {now_str}",
        f"**Total Runs Logged:** {len(runs)} | **Log Path:** `{log_path}`",
        "",
        "## 1. Experimental Grid Summary (Accuracy & Latency)",
        "| Model | Task (Shift) | Evaluation Mode | N | Substring Acc | Exact Match | Reasoning Solved | Avg Latency (s) | Avg Edit Dist |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for m in sorted(grid.keys()):
        for t in sorted(grid[m].keys()):
            for mode in sorted(grid[m][t].keys()):
                st = grid[m][t][mode]
                n = st["total"]
                acc = (st["correct"] / n) * 100 if n else 0
                ex = (st["exact"] / n) * 100 if n else 0
                rs = (st["gt_res"] / n) * 100 if n else 0
                alat = sum(st["latencies"]) / n if n else 0
                aed = sum(st["eds"]) / n if n else 0
                lines.append(f"| `{m}` | `{t}` | `{mode}` | {n} | **{acc:.1f}%** ({st['correct']}/{n}) | {ex:.1f}% | {rs:.1f}% | {alat:.2f}s | {aed:.2f} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Mechanistic Observations & Hypotheses Verification",
        "- **Hypothesis 1 (Direct Mode vs Thinking Mode):** Does forcing direct output reduce token exhaustion, or does it trigger outright hallucination?",
        "- **Hypothesis 2 (Retrieved Guidance):** Does in-context table injection level the playing field between ROT-13 and ROT-12?",
        "- **Hypothesis 3 (MoE vs Dense):** How does `qwen3-30b-a3b` (MoE) compare to `qwen3-32b` (Dense) in reasoning trace length and latency on non-canonical shifts?",
        "",
        "## 3. Sample Detailed Runs",
        ""
    ])

    for i, r in enumerate(runs[:12]):
        lines.append(f"### Run #{i+1}: `{r.get('model')}` | `{r.get('task')}` | `{r.get('mode')}` (Item {r.get('item_index')})")
        lines.append(f"- **Ground Truth:** `{r.get('ground_truth')}`")
        lines.append(f"- **Answer:** `{r.get('answer')[:120] if r.get('answer') else '[EMPTY]'}`")
        lines.append(f"- **Result:** `{'PASS' if r.get('is_correct') else 'FAIL'}` | **Category:** `{r.get('failure_category')}` | **Latency:** {r.get('latency_seconds'):.2f}s")
        reasoning_snippet = (r.get("reasoning") or "").replace("\n", " ")[:200]
        lines.append(f"- **Reasoning Excerpt:** *{reasoning_snippet}...*")
        lines.append("")

    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_experiment_items(num_items: int = 4) -> list:
    """
    Builds the 48 experimental combinations (2 models x 2 tasks x 3 modes x 4 items).
    """
    rot13_file = "/Users/ashwinanand/embers_replication/data/claim1_task_probability/shift_ciphers/shift_13.jsonl"
    rot12_file = "/Users/ashwinanand/embers_replication/data/claim1_task_probability/shift_ciphers/shift_12.jsonl"

    with open(rot13_file, "r", encoding="utf-8") as f:
        rot13_items = [json.loads(line) for line in f][:num_items]
    with open(rot12_file, "r", encoding="utf-8") as f:
        rot12_items = [json.loads(line) for line in f][:num_items]

    all_jobs = []
    for model in MODELS:
        for task_name, items in [("rot-13", rot13_items), ("rot-12", rot12_items)]:
            for mode in MODES:
                for idx, raw_item in enumerate(items):
                    prompt = build_prompt_for_mode(raw_item["instruction_plus_input"], task_name, mode)
                    uid = f"ext::{model}::{task_name}::{mode}::{idx}"
                    job = {
                        "run_uid": uid,
                        "model": model,
                        "task": task_name,
                        "mode": mode,
                        "item_index": idx,
                        "prompt": prompt,
                        "ground_truth": raw_item["correct_output"],
                        "raw_input": raw_item["input"]
                    }
                    all_jobs.append(job)
    return all_jobs


def run_extension(jobs: list, log_path: str = DEFAULT_LOG_PATH, summary_path: str = DEFAULT_SUMMARY_PATH,
                  workers: int = 1, delay_between: float = 1.0):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    completed_uids = load_existing_uids(log_path)
    print(f"Loaded {len(completed_uids)} previously completed extension runs.")

    pending_jobs = [j for j in jobs if j["run_uid"] not in completed_uids]
    print(f"Total jobs: {len(jobs)} | Remaining: {len(pending_jobs)}")

    if not pending_jobs:
        print("All extension runs completed.")
        generate_extension_markdown(log_path, summary_path)
        return

    def process_job(job: dict) -> dict:
        t0 = datetime.now(timezone.utc).isoformat()
        res = query_model(job["model"], job["prompt"], max_tokens=3500)
        raw_content = res.get("raw_content", "")
        reasoning_content = res.get("reasoning_content", "")
        thinking, clean_ans, is_truncated = extract_reasoning_and_answer(raw_content, reasoning_content)

        eval_res = evaluate_prediction(job["ground_truth"], raw_content, clean_ans, thinking, res.get("finish_reason", "unknown"))

        record = {
            "timestamp": t0,
            "run_uid": job["run_uid"],
            "model": job["model"],
            "task": job["task"],
            "mode": job["mode"],
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

    if workers <= 1:
        for job in pending_jobs:
            record = process_job(job)
            done_count += 1
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            
            icon = "PASS" if record["is_correct"] else "FAIL"
            ans_str = record["answer"][:30] if record["answer"] else f"[{record['failure_category']}]"
            print(f"[{done_count}/{total_pending}] {icon} | {record['model']} | {record['task']} | {record['mode']} (idx {record['item_index']}) | {ans_str}")
            
            if done_count % 4 == 0 or done_count == total_pending:
                generate_extension_markdown(log_path, summary_path)

            if delay_between > 0:
                time.sleep(delay_between)
    else:
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
                    print(f"[{done_count}/{total_pending}] {icon} | {record['model']} | {record['task']} | {record['mode']} | {ans_str}")
                except Exception as e:
                    print(f"Extension worker error: {e}")

                if done_count % 4 == 0 or done_count == total_pending:
                    generate_extension_markdown(log_path, summary_path)

    generate_extension_markdown(log_path, summary_path)
    print(f"Extension runs complete. Summary written to {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Extension Runner for Embers Replication")
    parser.add_argument("--num-items", type=int, default=4, help="Items per condition (default 4)")
    parser.add_argument("--workers", type=int, default=1, help="Concurrency workers (default 1)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--log-path", type=str, default=DEFAULT_LOG_PATH)
    parser.add_argument("--summary-path", type=str, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args()

    jobs = build_experiment_items(num_items=args.num_items)
    run_extension(jobs, log_path=args.log_path, summary_path=args.summary_path,
                  workers=args.workers, delay_between=args.delay)


if __name__ == "__main__":
    main()
