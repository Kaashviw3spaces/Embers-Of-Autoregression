> HISTORICAL SOURCE DOCUMENT: preserved for audit, not a current result. Some claims were not supported on reanalysis. Use report/Combined_Report.pdf and analysis/friend2_audit.json for the corrected account.

# LOG REPOSITORY MANIFEST
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
