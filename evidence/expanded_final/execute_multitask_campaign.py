#!/usr/bin/env python3
"""
execute_multitask_campaign.py
Executes Phase 2 Expanded Experimental Campaign across prioritized benchmark tasks
from McCoy et al. (PNAS 2024).
"""

import os
import re
import json
import time
from Levenshtein import distance
from openai import OpenAI
from threading import Lock
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = "/Users/prachivats21/embers_project"
REPO_STIMULI = "/Users/prachivats21/embers_repo/stimuli"
RUNS_DIR = os.path.join(BASE_DIR, "runs")

class SafeRateLimiter:
    def __init__(self, max_rpm=18, max_tpm=40000):
        self.min_interval = 60.0 / max_rpm
        self.max_tpm = max_tpm
        self.lock = Lock()
        self.last_call_time = 0.0
        self.token_history = deque()

    def wait_for_slot(self, estimated_tokens=300):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
                now = time.time()

            cutoff = now - 60.0
            while self.token_history and self.token_history[0][0] < cutoff:
                self.token_history.popleft()

            current_tpm = sum(t for _, t in self.token_history)
            if current_tpm + estimated_tokens > self.max_tpm:
                sleep_needed = 60.0 - (now - self.token_history[0][0]) + 1.0
                print(f"[RateLimiter] Throttling {sleep_needed:.1f}s...")
                time.sleep(sleep_needed)
                now = time.time()

            self.last_call_time = now

    def record_actual_tokens(self, total_tokens):
        with self.lock:
            self.token_history.append((time.time(), total_tokens))

rate_limiter = SafeRateLimiter(max_rpm=18, max_tpm=40000)

def parse_task_response(task_type, raw_text, gt):
    text = raw_text.strip()
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].startswith("```"):
            text = "\n".join(lines[1:-1]).strip()
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        text = text[1:-1].strip()

    gt_clean = gt.strip()

    if task_type == "counting":
        # Extract last or first integer
        digits = re.findall(r"\b\d+\b", text)
        if digits:
            parsed = digits[-1]
        else:
            parsed = text
        is_correct = (parsed == gt_clean)
        return parsed, is_correct, (0 if is_correct else 1)

    elif task_type == "reverse":
        parsed = text.strip()
        is_correct = (gt_clean.lower() in parsed.lower()) or (parsed.lower() in gt_clean.lower())
        lev = distance(gt_clean, parsed)
        return parsed, is_correct, lev

    elif task_type == "sorting":
        parsed = text.strip()
        is_correct = (gt_clean.lower() in parsed.lower())
        lev = distance(gt_clean, parsed)
        return parsed, is_correct, lev

    elif task_type == "swap":
        parsed = text.strip()
        is_correct = (gt_clean.lower() in parsed.lower())
        lev = distance(gt_clean, parsed)
        return parsed, is_correct, lev

    elif task_type == "multiplication":
        digits = re.findall(r"\b\d+\b", text)
        if digits:
            parsed = digits[-1]
        else:
            parsed = text
        is_correct = (parsed == gt_clean)
        return parsed, is_correct, (0 if is_correct else 1)

    elif task_type == "pig":
        parsed = text.strip()
        is_correct = (gt_clean.lower() in parsed.lower())
        lev = distance(gt_clean, parsed)
        return parsed, is_correct, lev

    else:
        parsed = text
        is_correct = (gt_clean.lower() in parsed.lower())
        return parsed, is_correct, distance(gt_clean, parsed)

def call_api(client, model, prompt, max_tokens=250):
    rate_limiter.wait_for_slot(estimated_tokens=max_tokens + 50)
    t0 = time.time()
    try:
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
            timeout=120.0
        )
        latency = time.time() - t0
        usage = getattr(res, "usage", None)
        tokens = getattr(usage, "total_tokens", max_tokens) if usage else max_tokens
        rate_limiter.record_actual_tokens(tokens)
        msg = res.choices[0].message
        content = msg.content or ""
        reasoning = getattr(msg, "reasoning_content", "") or ""
        if not content and reasoning:
            content = reasoning
        return {
            "success": True,
            "content": content.strip(),
            "latency": latency,
            "tokens": tokens,
            "finish_reason": res.choices[0].finish_reason,
            "api_error": None,
            "retries": []
        }
    except Exception as e:
        latency = time.time() - t0
        err_msg = str(e)
        return {
            "success": False,
            "content": "",
            "latency": latency,
            "tokens": 0,
            "finish_reason": "error",
            "api_error": err_msg[:120],
            "retries": [{"error": err_msg[:120], "timestamp": time.time()}]
        }

def run_condition_benchmark(task_type, cond_id, file_path, model, client, num_examples=5, max_tokens=250):
    full_path = os.path.join(REPO_STIMULI, file_path)
    if not os.path.exists(full_path):
        print(f"Skipping {cond_id}: {full_path} not found")
        return

    with open(full_path, "r") as f:
        lines = [json.loads(l) for l in f.readlines()][:num_examples]

    print(f"\n>>> Running {task_type}:{cond_id} | Model: {model} | N={len(lines)}")
    results = []

    for idx, item in enumerate(lines):
        prompt = item.get("instruction_plus_input", item.get("prompt", item.get("input", "")))
        gt = str(item.get("correct_output", item.get("target", "")))
        inp = str(item.get("input", ""))

        call_res = call_api(client, model, prompt, max_tokens=max_tokens)
        raw_text = call_res["content"]
        parsed, is_correct, lev = parse_task_response(task_type, raw_text, gt)

        status_str = "PASS" if is_correct else "FAIL"
        print(f"  [{idx+1}/{len(lines)}] {status_str} | GT: {gt[:20]!r} | Pred: {parsed[:20]!r} | Lat: {call_res['latency']:.1f}s")

        results.append({
            "stimulus_id": idx,
            "input_words": inp,
            "prompt": prompt,
            "gt": gt,
            "raw_response": raw_text,
            "parsed_response": parsed,
            "correct": is_correct and call_res["success"],
            "lev_distance": lev,
            "latency": call_res["latency"],
            "tokens_used": call_res["tokens"],
            "finish_reason": call_res["finish_reason"],
            "api_error": call_res["api_error"],
            "retry_history": call_res["retries"]
        })

    correct_count = sum(1 for r in results if r["correct"])
    acc = correct_count / len(results) if results else 0.0
    mean_lev = sum(r["lev_distance"] for r in results) / len(results) if results else 0.0

    run_record = {
        "task_name": cond_id,
        "task_family": task_type,
        "model": model,
        "condition": "baseline",
        "total_requested": len(results),
        "valid_completed": len(results),
        "api_error_count": sum(1 for r in results if r["api_error"]),
        "accuracy": acc,
        "mean_levenshtein": mean_lev,
        "results": results
    }

    out_file = os.path.join(RUNS_DIR, f"{cond_id}_{model}_baseline_smoke.json")
    with open(out_file, "w") as f:
        json.dump(run_record, f, indent=2)
    print(f"--> Saved {out_file} (Acc: {acc*100:.1f}%)")

def main():
    client = OpenAI(base_url="http://10.7.25.115:30400/v1", api_key="[REDACTED_KEY]")

    matrix = [
        ("counting", "counting_words_common", "counting_words_common.jsonl", 5),
        ("counting", "counting_words_rare", "counting_words_rare.jsonl", 5),
        ("reverse", "revdec_highprob", "revdec_highprob.jsonl", 5),
        ("reverse", "revdec_lowprob", "revdec_lowprob.jsonl", 5),
        ("sorting", "sorting_rev_10shot", "sorting_rev_10shot.jsonl", 5),
        ("swap", "swap_next_base_highprob", "swap_next_base_highprob.jsonl", 5),
        ("swap", "swap_next_base_lowprob", "swap_next_base_lowprob.jsonl", 5),
        ("multiplication", "multiplication_word", "multiplication_word.jsonl", 5),
        ("pig", "pigdec_ay_highprob", "pigdec_ay_highprob.jsonl", 5),
        ("pig", "pigdec_say_highprob", "pigdec_say_highprob.jsonl", 5),
    ]

    print("==================================================================")
    print("STARTING MULTI-TASK EXPANDED CAMPAIGN ON QWEN3-30B-A3B")
    print("==================================================================")
    for task_type, cond_id, file_path, n in matrix:
        run_condition_benchmark(task_type, cond_id, file_path, "qwen3-30b-a3b", client, num_examples=n)

    print("\n==================================================================")
    print("STARTING MATCHED MULTI-TASK COMPARISON ON QWEN3-32B (DENSE)")
    print("==================================================================")
    matched_matrix = [
        ("counting", "counting_words_common", "counting_words_common.jsonl", 3),
        ("reverse", "revdec_highprob", "revdec_highprob.jsonl", 3),
    ]
    for task_type, cond_id, file_path, n in matched_matrix:
        run_condition_benchmark(task_type, cond_id, file_path, "qwen3-32b", client, num_examples=n, max_tokens=150)

    print("\n[CAMPAIGN COMPLETE] Executing master repository assembly...")

if __name__ == "__main__":
    main()
