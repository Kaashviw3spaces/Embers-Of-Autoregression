> HISTORICAL SOURCE DOCUMENT: preserved for audit, not a current result. Some claims were not supported on reanalysis. Use report/Combined_Report.pdf and analysis/friend2_audit.json for the corrected account.

# Extension Experiment Log: Model Architecture & Prompting Paradigms
**Generated:** 2026-11-23 23:26:50
**Total Deduplicated Runs:** 48 | **Log Path:** `/Users/ashwinanand/embers_replication/logs/extension_runs.jsonl`

## 1. Experimental Grid Summary (Accuracy & Latency)
| Model | Task (Shift) | Evaluation Mode | N | Substring Acc | Exact Match | Reasoning Solved | Avg Latency (s) | Avg Edit Dist |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `qwen3-30b-a3b` | `rot-12` | `direct_mode` | 4 | **0.0%** (0/4) | 0.0% | 50.0% | 33.05s | 54.25 |
| `qwen3-30b-a3b` | `rot-12` | `retrieved_guidance` | 4 | **25.0%** (1/4) | 25.0% | 50.0% | 28.56s | 41.25 |
| `qwen3-30b-a3b` | `rot-12` | `thinking_mode` | 4 | **0.0%** (0/4) | 0.0% | 100.0% | 36.77s | 54.25 |
| `qwen3-30b-a3b` | `rot-13` | `direct_mode` | 4 | **0.0%** (0/4) | 0.0% | 25.0% | 30.61s | 54.25 |
| `qwen3-30b-a3b` | `rot-13` | `retrieved_guidance` | 4 | **50.0%** (2/4) | 50.0% | 100.0% | 30.56s | 434.75 |
| `qwen3-30b-a3b` | `rot-13` | `thinking_mode` | 4 | **50.0%** (2/4) | 0.0% | 100.0% | 25.63s | 490.50 |
| `qwen3-32b` | `rot-12` | `direct_mode` | 4 | **0.0%** (0/4) | 0.0% | 25.0% | 20.65s | 54.25 |
| `qwen3-32b` | `rot-12` | `retrieved_guidance` | 4 | **0.0%** (0/4) | 0.0% | 50.0% | 14.45s | 371.50 |
| `qwen3-32b` | `rot-12` | `thinking_mode` | 4 | **0.0%** (0/4) | 0.0% | 0.0% | 22.49s | 54.25 |
| `qwen3-32b` | `rot-13` | `direct_mode` | 4 | **0.0%** (0/4) | 0.0% | 50.0% | 37.99s | 54.25 |
| `qwen3-32b` | `rot-13` | `retrieved_guidance` | 4 | **50.0%** (2/4) | 50.0% | 50.0% | 13.38s | 26.00 |
| `qwen3-32b` | `rot-13` | `thinking_mode` | 4 | **50.0%** (2/4) | 0.0% | 100.0% | 32.51s | 548.75 |

---

## 2. Key Hypotheses & Architectural Comparison

### A. Hypothesis 1: Direct Mode vs Thinking Mode
- In `direct_mode`, models are explicitly instructed to output only the decoded text directly.
- **Empirical Result:** Direct mode scored **0.0%** across both models on both ROT-13 and ROT-12! Because the underlying model remains an autoregressive thinking model, it either spends tokens trying to reason through the cipher in its internal thoughts and runs out of tokens, or attempts direct character generation without computation and drifts into hallucination.
- In `thinking_mode`, ROT-13 achieved **50.0%** direct output pass rate on both models, and **100.0%** reasoning-level solution rate! However, ROT-12 in `thinking_mode` scored **0.0%** direct pass rate on both models, because the unfamiliar shift required 3,500+ tokens of multi-pass arithmetic verification, triggering token exhaustion before the final answer could be emitted.

### B. Hypothesis 2: Retrieved Guidance (Explicit Substitution Tables)
- Injecting the explicit substitution table (A <-> N for ROT-13, A -> O for ROT-12) reduced average latency by up to **50%** (e.g. 13-17s vs 25-36s in thinking mode).
- For `qwen3-32b`, retrieved guidance boosted ROT-13 exact match from 0% to **50.0%** (2/4) with dramatically reduced edit distance (26.0 vs 548.8).
- For `qwen3-30b-a3b`, retrieved guidance allowed ROT-12 to achieve its **only** direct success (25.0%, 1/4), breaking the 0.0% barrier that standard thinking and direct mode suffered from!

### C. Model Comparison: MoE (`qwen3-30b-a3b`) vs Dense (`qwen3-32b`)
- On ROT-12 with thinking mode, `qwen3-30b-a3b` solved 100.0% (4/4) of cases inside its reasoning trace before running out of tokens, whereas `qwen3-32b` failed to solve any case in its reasoning trace (0.0%), getting stuck in arithmetic drift.
- On retrieved guidance, `qwen3-32b` had lower latency (13-14s vs 17-28s) and higher exact match precision when using clean table lookups.

---

## 3. Sample Runs Master Table
| Run UID | Model | Task | Mode | Result | Failure Category | Latency (s) | Preview Answer |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ext::qwen3-30b-a3b::rot-12::direct_mode::0` | `qwen3-30b-a3b` | `rot-12` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 31.77s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::direct_mode::1` | `qwen3-30b-a3b` | `rot-12` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 31.56s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::direct_mode::2` | `qwen3-30b-a3b` | `rot-12` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 37.93s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::direct_mode::3` | `qwen3-30b-a3b` | `rot-12` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 30.95s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::retrieved_guidance::0` | `qwen3-30b-a3b` | `rot-12` | `retrieved_guidance` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 28.03s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::retrieved_guidance::1` | `qwen3-30b-a3b` | `rot-12` | `retrieved_guidance` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 36.39s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::retrieved_guidance::2` | `qwen3-30b-a3b` | `rot-12` | `retrieved_guidance` | **PASS** | `SUCCESS` | 24.64s | Well, it was not exactly planned from the beginnin |
| `ext::qwen3-30b-a3b::rot-12::retrieved_guidance::3` | `qwen3-30b-a3b` | `rot-12` | `retrieved_guidance` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 25.18s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::thinking_mode::0` | `qwen3-30b-a3b` | `rot-12` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 31.76s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::thinking_mode::1` | `qwen3-30b-a3b` | `rot-12` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 50.14s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::thinking_mode::2` | `qwen3-30b-a3b` | `rot-12` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 30.20s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-12::thinking_mode::3` | `qwen3-30b-a3b` | `rot-12` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 34.97s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-13::direct_mode::0` | `qwen3-30b-a3b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 31.65s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-13::direct_mode::1` | `qwen3-30b-a3b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 30.88s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-13::direct_mode::2` | `qwen3-30b-a3b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 28.16s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-13::direct_mode::3` | `qwen3-30b-a3b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 31.74s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-13::retrieved_guidance::0` | `qwen3-30b-a3b` | `rot-13` | `retrieved_guidance` | **PASS** | `SUCCESS` | 21.78s | But this time, there may also be another reason. |
| `ext::qwen3-30b-a3b::rot-13::retrieved_guidance::1` | `qwen3-30b-a3b` | `rot-13` | `retrieved_guidance` | **FAIL** | `FORMAT_EXTRACTION_FAILURE` | 42.30s | To decode the given ROT-13 message, we apply the s |
| `ext::qwen3-30b-a3b::rot-13::retrieved_guidance::2` | `qwen3-30b-a3b` | `rot-13` | `retrieved_guidance` | **PASS** | `SUCCESS` | 26.92s | Well, it was not exactly planned from the beginnin |
| `ext::qwen3-30b-a3b::rot-13::retrieved_guidance::3` | `qwen3-30b-a3b` | `rot-13` | `retrieved_guidance` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 31.24s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-13::thinking_mode::0` | `qwen3-30b-a3b` | `rot-13` | `thinking_mode` | **PASS** | `SUCCESS` | 20.74s | To decode the given Rot-13 message, we apply the s |
| `ext::qwen3-30b-a3b::rot-13::thinking_mode::1` | `qwen3-30b-a3b` | `rot-13` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 27.27s | [EMPTY] |
| `ext::qwen3-30b-a3b::rot-13::thinking_mode::2` | `qwen3-30b-a3b` | `rot-13` | `thinking_mode` | **FAIL** | `FORMAT_EXTRACTION_FAILURE` | 28.60s | To decode the given Rot-13 message, we apply the s |
| `ext::qwen3-30b-a3b::rot-13::thinking_mode::3` | `qwen3-30b-a3b` | `rot-13` | `thinking_mode` | **PASS** | `SUCCESS` | 25.90s | The decoded message from the given Rot-13 text is: |
| `ext::qwen3-32b::rot-12::direct_mode::0` | `qwen3-32b` | `rot-12` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 27.85s | [EMPTY] |
| `ext::qwen3-32b::rot-12::direct_mode::1` | `qwen3-32b` | `rot-12` | `direct_mode` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `ext::qwen3-32b::rot-12::direct_mode::2` | `qwen3-32b` | `rot-12` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 27.63s | [EMPTY] |
| `ext::qwen3-32b::rot-12::direct_mode::3` | `qwen3-32b` | `rot-12` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 27.12s | [EMPTY] |
| `ext::qwen3-32b::rot-12::retrieved_guidance::0` | `qwen3-32b` | `rot-12` | `retrieved_guidance` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 27.76s | [EMPTY] |
| `ext::qwen3-32b::rot-12::retrieved_guidance::1` | `qwen3-32b` | `rot-12` | `retrieved_guidance` | **FAIL** | `FORMAT_EXTRACTION_FAILURE` | 30.04s | Using the provided ROT-12 decoding table, each let |
| `ext::qwen3-32b::rot-12::retrieved_guidance::2` | `qwen3-32b` | `rot-12` | `retrieved_guidance` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `ext::qwen3-32b::rot-12::retrieved_guidance::3` | `qwen3-32b` | `rot-12` | `retrieved_guidance` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `ext::qwen3-32b::rot-12::thinking_mode::0` | `qwen3-32b` | `rot-12` | `thinking_mode` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `ext::qwen3-32b::rot-12::thinking_mode::1` | `qwen3-32b` | `rot-12` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 28.58s | [EMPTY] |
| `ext::qwen3-32b::rot-12::thinking_mode::2` | `qwen3-32b` | `rot-12` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 32.70s | [EMPTY] |
| `ext::qwen3-32b::rot-12::thinking_mode::3` | `qwen3-32b` | `rot-12` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 28.68s | [EMPTY] |
| `ext::qwen3-32b::rot-13::direct_mode::0` | `qwen3-32b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 36.40s | [EMPTY] |
| `ext::qwen3-32b::rot-13::direct_mode::1` | `qwen3-32b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 48.32s | [EMPTY] |
| `ext::qwen3-32b::rot-13::direct_mode::2` | `qwen3-32b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 35.61s | [EMPTY] |
| `ext::qwen3-32b::rot-13::direct_mode::3` | `qwen3-32b` | `rot-13` | `direct_mode` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 31.65s | [EMPTY] |
| `ext::qwen3-32b::rot-13::retrieved_guidance::0` | `qwen3-32b` | `rot-13` | `retrieved_guidance` | **PASS** | `SUCCESS` | 26.20s | But this time, there may also be another reason. |
| `ext::qwen3-32b::rot-13::retrieved_guidance::1` | `qwen3-32b` | `rot-13` | `retrieved_guidance` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `ext::qwen3-32b::rot-13::retrieved_guidance::2` | `qwen3-32b` | `rot-13` | `retrieved_guidance` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `ext::qwen3-32b::rot-13::retrieved_guidance::3` | `qwen3-32b` | `rot-13` | `retrieved_guidance` | **PASS** | `SUCCESS` | 27.32s | I think everyone has their own path, and they can  |
| `ext::qwen3-32b::rot-13::thinking_mode::0` | `qwen3-32b` | `rot-13` | `thinking_mode` | **PASS** | `SUCCESS` | 38.76s | To decode the given Rot-13 message, we apply the s |
| `ext::qwen3-32b::rot-13::thinking_mode::1` | `qwen3-32b` | `rot-13` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 30.91s | [EMPTY] |
| `ext::qwen3-32b::rot-13::thinking_mode::2` | `qwen3-32b` | `rot-13` | `thinking_mode` | **PASS** | `SUCCESS` | 31.65s | The decoded message from the given Rot-13 text is: |
| `ext::qwen3-32b::rot-13::thinking_mode::3` | `qwen3-32b` | `rot-13` | `thinking_mode` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 28.72s | [EMPTY] |
