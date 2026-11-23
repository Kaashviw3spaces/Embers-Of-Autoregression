#!/usr/bin/env python3
"""
Generates the Unified Master Experiment Log combining primary replication and extension runs.
Produces:
  - logs/MASTER_EXPERIMENT_LOG.md
  - logs/LOG_MANIFEST.md
"""

import os
import json
from datetime import datetime

base_dir = '/Users/ashwinanand/embers_replication'
logs_dir = os.path.join(base_dir, 'logs')
results_dir = os.path.join(base_dir, 'results')
docs_dir = os.path.join(base_dir, 'docs')

# Read sources
with open(os.path.join(logs_dir, 'experiment_log.md'), 'r', encoding='utf-8') as f:
    primary_log_content = f.read()

with open(os.path.join(logs_dir, 'extension_experiment_log.md'), 'r', encoding='utf-8') as f:
    ext_log_content = f.read()

with open(os.path.join(results_dir, 'extension_findings.md'), 'r', encoding='utf-8') as f:
    ext_findings_content = f.read()

with open(os.path.join(results_dir, 'paper_vs_simulation_comparison.md'), 'r', encoding='utf-8') as f:
    paper_comparison_content = f.read()

master_md = f"""# UNIFIED MASTER EXPERIMENT LOG & CONTEXT REPOSITORY
## AIRIS Research Hackathon — Problem Statement 8 ('Embers of Autoregression')
**Target Paper:** McCoy et al. (PNAS 2024 / arXiv:2309.13638)  
**Team:** kybers | **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Evaluated Models:** `qwen3-30b-a3b` (Sparse MoE Thinking Model) & `qwen3-32b` (Dense Thinking Model)  
**Total Experimental Runs:** 117 Runs (63 Primary Replication + 54 Extension Trials)  
**Master JSONL Dataset:** `/Users/ashwinanand/embers_replication/logs/all_runs_master.jsonl`

---

## 📌 TABLE OF CONTENTS
1. [Executive Project Blueprint & Context](#1-executive-project-blueprint--context)
2. [Master Ledger Summary & Metric Dashboard](#2-master-ledger-summary--metric-dashboard)
3. [Phase 1: Primary Replication (Claim 1 & Claim 2)](#3-phase-1-primary-replication-claim-1--claim-2)
4. [Phase 2: Comparative Study (Published Baselines vs Qwen3)](#4-phase-2-comparative-study-published-baselines-vs-qwen3)
5. [Phase 3: Extension Investigation (Thinking Mode & Retrieved Guidance)](#5-phase-3-extension-investigation-thinking-mode--retrieved-guidance)
6. [Phase 4: Extension Master Ledger & Deep-Dive Case Studies](#6-phase-4-extension-master-ledger--deep-dive-case-studies)
7. [Phase 5: Student Learning Curve & Human vs AI Failure Matrix](#7-phase-5-student-learning-curve--human-vs-ai-failure-matrix)
8. [Phase 6: Artifact & Data Manifest](#8-phase-6-artifact--data-manifest)

---

## 1. Executive Project Blueprint & Context

### 1.1 The Central Thesis
Does next-token autoregressive pre-training fundamentally bias LLMs when executing strictly deterministic, symbolic rules?
McCoy et al. showed that holding formal problem complexity invariant:
- **Claim 1 (Task Probability):** Models perform dramatically worse on statistically rare task variants (e.g. ROT-12 cipher, reverse alphabetical sorting, synthetic linear equations) than on common variants (ROT-13, forward alphabetical sorting, Celsius-to-Fahrenheit conversion).
- **Claim 2 (Target Output Probability):** Holding the cipher rule constant, models perform worse when the correct output text is uncommon or adversarial natural language.

### 1.2 Our Key Hackathon Findings & Discoveries
1. **Replication of Both Claims Confirmed:** Evaluated on open-weights thinking models using the official McCoy et al. stimuli (59 JSONL files, 11,883 items).
2. **The Latent Token Budget Shift:** In thinking models (`qwen3`), the embers of autoregression do **not** disappear. They convert from output-level hallucination into **Latent Token Inflation**: because rare tasks lack pre-trained associative subwords, the model requires 2x-5x more reasoning steps (+43.8% compute penalty), exhausting its generation budget before emitting visible output.
3. **Extension 1 (Thinking Mode vs Direct Mode):** Direct mode without scratchpad fails completely (0.0%). Thinking mode solves 100% of ROT-12 cases *internally* in MoE (`qwen3-30b-a3b`), but hits `finish_reason=length` right before emitting the answer.
4. **Extension 2 (Controlled Internet-Retrieved Guidance):** Injecting explicit in-context substitution tables neutralized the task frequency penalty, slashing latency by up to 58.8% and breaking the 0.0% barrier on ROT-12 (achieving 25.0% exact match).
5. **MoE vs Dense Architectural Divergence:** MoE maintains strict modular character arithmetic on rare tasks (100% latent solving), while Dense is vulnerable to accumulating arithmetic drift and directional epistemic loops (0% latent solving on ROT-12).

---

## 2. Master Ledger Summary & Metric Dashboard

| Experiment Phase | Total Runs | Visible Substring Acc | Latent Reasoning Solved | Primary Driver |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1: Primary Replication (21 Conditions)** | 63 | 34.9% (22/63) | 79.4% (50/63) | 41.3% Token Exhaustion After Solving |
| **Phase 2: Extension Mode Ablation (12 Cells)** | 54 | 20.4% (11/54) | 59.3% (32/54) | In-context tables break 0% ROT-12 barrier |
| **Combined Master Total** | **117** | **28.2% (33/117)** | **70.1% (82/117)** | **100% Audited with Latent Traces** |

---

## 3. Phase 1: Primary Replication (Claim 1 & Claim 2)

{primary_log_content}

---

## 4. Phase 2: Comparative Study (Published Baselines vs Qwen3)

{paper_comparison_content}

---

## 5. Phase 3: Extension Investigation (Thinking Mode & Retrieved Guidance)

{ext_findings_content}

---

## 6. Phase 4: Extension Master Ledger & Deep-Dive Case Studies

{ext_log_content}

---

## 7. Phase 5: Student Learning Curve & Human vs AI Failure Matrix

Refer to the complete standalone guide in `docs/student_learning_curve.md`.
Key pillars:
- **BPE Token Fragmentation:** Common ciphers (ROT-13) preserve subwords; rare ciphers (ROT-12) fracture into single-character tokens, tripling sequence length.
- **Metric Sensitivity:** Strict exact match yields artificial 0% due to chat preambles; McCoy substring containment (`gt in res`) + Levenshtein distance correctly isolates cryptographic reasoning.
- **Judge Defense Guide:** 8 domain-specific questions with defensive answers addressing tokenization, in-context learning confounders, and temperature effects.

---

## 8. Phase 6: Artifact & Data Manifest

| File Path | Description | Record Count / Purpose |
| :--- | :--- | :--- |
| `logs/all_runs_master.jsonl` | **Unified Master Execution Stream** | 117 complete JSON runs with prompts, latent thoughts, answers, edit distances |
| `logs/MASTER_EXPERIMENT_LOG.md` | **This Unified Document** | Complete end-to-end repository context & synthesis |
| `logs/LOG_MANIFEST.md` | Log index guide for external evaluators | Quick start guide for incoming agents/reviewers |
| `logs/experiment_log.md` | Primary replication ledger & 35 hand-inspected failures | 63 records |
| `logs/extension_experiment_log.md` | Extension ledger & 12-cell matrix breakdown | 54 records |
| `logs/raw_runs.jsonl` | Raw primary execution stream | 63 records |
| `logs/extension_runs.jsonl` | Raw extension execution stream | 54 records |
| `results/paper_vs_simulation_comparison.md` | Comparative tables against published GPT-4, Claude 3, LLaMA-3 | Comprehensive comparative study |
| `results/extension_findings.md` | Multi-model evaluation (MoE vs Dense across Direct, Think, Retrieved) | Full extension research report |
| `docs/student_learning_curve.md` | Pedagogical failure matrix, BPE analysis, and 8-question oral defense | 466 lines |
| `data/dataset_catalog.json` | Catalog of all 59 official stimuli files | 11,883 items |
| `src/runner.py` | Primary replication evaluation harness | Source code |
| `src/extension_runner.py` | Extension 12-cell factorial test harness | Source code |
| `run.sh` | One-command replication execution script | Shell script |
"""

master_log_path = os.path.join(logs_dir, 'MASTER_EXPERIMENT_LOG.md')
with open(master_log_path, 'w', encoding='utf-8') as f:
    f.write(master_md)

# Write LOG_MANIFEST.md
manifest_md = f"""# LOG REPOSITORY MANIFEST
**AIRIS Research Hackathon — Team kybers**
**Target Paper:** *Embers of Autoregression* (McCoy et al., PNAS 2024 / arXiv:2309.13638)

If you are inspecting or transferring this directory to another machine or agent, this document provides the exact map of all empirical logs and context:

## 1. Primary Unified Datasets
- **`logs/all_runs_master.jsonl`** (117 records, ~1.2 MB):
  Contains **every single prompt, full latent thinking trace (`<think>`), visible output, ground truth, finish reason, Levenshtein edit distance, and latency** across both the primary replication (63 runs) and the extension experiments (54 runs).
  - Schema per JSON record:
    * `timestamp`: ISO timestamp of run
    * `run_uid`: Unique execution identifier
    * `experiment_phase`: `'primary_replication'` or `'extension_investigation'`
    * `model`: `'qwen3-30b-a3b'` or `'qwen3-32b'`
    * `prompt`: Exact raw prompt delivered to the model
    * `reasoning`: Complete extracted Chain-of-Thought deliberation
    * `answer`: Clean extracted visible response
    * `ground_truth`: Exact target string
    * `is_correct`: Boolean substring containment pass (`gt in answer`)
    * `exact_match`: Boolean exact string match (`gt == answer.strip()`)
    * `edit_distance`: Character Levenshtein edit distance
    * `latency_seconds`: Server inference latency
    * `finish_reason`: `'stop'` or `'length'` (token exhaustion)
    * `failure_category`: Mechanistic taxonomy category

## 2. Synthesized Master Reports
- **`logs/MASTER_EXPERIMENT_LOG.md`** (~120 KB):
  The **single source of truth** markdown document. Contains executive blueprints, multi-model dashboards, full 117-run ledgers, 35+ hand-audited failure case studies, and complete methodological disclosures.
- **`results/paper_vs_simulation_comparison.md`**:
  Side-by-side comparison tables against published baselines (GPT-4, Claude 3 Opus, GPT-3.5 Turbo, Gemini 1.0 Pro, LLaMA-3 70B).
- **`results/extension_findings.md`**:
  Complete research report for the Hackathon Extension testing Thinking Mode vs Direct Mode vs Retrieved Guidance on Sparse MoE vs Dense architectures.
- **`docs/student_learning_curve.md`**:
  Pedagogical diagnostic breakdown of where human students fail vs blind AI scripts, low-level tokenization mechanics, and 8-question judge defense Q&A.
"""

manifest_path = os.path.join(logs_dir, 'LOG_MANIFEST.md')
with open(manifest_path, 'w', encoding='utf-8') as f:
    f.write(manifest_md)

print("MASTER_EXPERIMENT_LOG.md and LOG_MANIFEST.md generated successfully!")
