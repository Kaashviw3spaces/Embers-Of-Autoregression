> HISTORICAL SOURCE DOCUMENT: preserved for audit, not a current result. Some claims were not supported on reanalysis. Use report/Combined_Report.pdf and analysis/friend2_audit.json for the corrected account.

# Extension Phase 2 Experiment Log: Advanced Hypotheses Evaluation
**Generated:** 2026-11-24 00:28:59
**Total Runs Logged:** 24 | **Log Path:** `/Users/ashwinanand/embers_replication/logs/extension_phase2_runs.jsonl`

## 1. Hypothesis Testing Grid Summary
| Hypothesis | Model | Task & Condition | N | Substring Acc | Exact Match | Reasoning Solved | Avg Latency (s) | Avg Edit Dist |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Hypothesis A (Tokenization Intervention) | `qwen3-30b-a3b` | `rot-12::char_spaced_stimuli` | 3 | **0.0%** (0/3) | 0.0% | 0.0% | 40.34s | 50.67 |
| Hypothesis A (Tokenization Intervention) | `qwen3-30b-a3b` | `rot-13::char_spaced_stimuli` | 3 | **0.0%** (0/3) | 0.0% | 0.0% | 38.28s | 50.67 |
| Hypothesis A (Tokenization Intervention) | `qwen3-32b` | `rot-12::char_spaced_stimuli` | 3 | **0.0%** (0/3) | 0.0% | 0.0% | 27.62s | 50.67 |
| Hypothesis A (Tokenization Intervention) | `qwen3-32b` | `rot-13::char_spaced_stimuli` | 3 | **0.0%** (0/3) | 0.0% | 0.0% | 0.00s | 50.67 |
| Hypothesis B (Compute Scaling 4096) | `qwen3-30b-a3b` | `rot-12::budget_4096_tokens` | 3 | **0.0%** (0/3) | 0.0% | 100.0% | 41.70s | 50.67 |
| Hypothesis B (Compute Scaling 4096) | `qwen3-32b` | `rot-12::budget_4096_tokens` | 3 | **0.0%** (0/3) | 0.0% | 100.0% | 37.70s | 383.33 |
| Hypothesis C (Few-Shot Calibration) | `qwen3-30b-a3b` | `rot-12::fewshot_3shot` | 3 | **0.0%** (0/3) | 0.0% | 66.7% | 34.74s | 50.67 |
| Hypothesis C (Few-Shot Calibration) | `qwen3-32b` | `rot-12::fewshot_3shot` | 3 | **0.0%** (0/3) | 0.0% | 66.7% | 37.27s | 50.67 |

---

## 2. Hypothesis-by-Hypothesis Empirical Verification

### Hypothesis A: Tokenization Intervention (Character Spacing)
- Evaluates whether inserting spaces between every ciphertext letter eliminates BPE token boundary fragmentation.

### Hypothesis B: Test-Time Compute Budget Scaling (4096 Tokens)
- Evaluates whether giving thinking models 4096 tokens allows latent-solved cases to reach final answer emission.

### Hypothesis C: In-Context Few-Shot Calibration (3-Shot Demonstrations)
- Evaluates whether 3 explicit in-context demonstrations can elevate local task probability and overcome pre-training frequency deficits.

---

## 3. Sample Runs Master Table
| Run UID | Model | Hypothesis | Condition | Result | Category | Latency (s) | Answer Preview |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `p2::qwen3-30b-a3b::hypA_char_spaced::rot-12::0` | `qwen3-30b-a3b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 35.67s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypA_char_spaced::rot-12::1` | `qwen3-30b-a3b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 48.54s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypA_char_spaced::rot-12::2` | `qwen3-30b-a3b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 36.82s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypA_char_spaced::rot-13::0` | `qwen3-30b-a3b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 34.75s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypA_char_spaced::rot-13::1` | `qwen3-30b-a3b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 49.45s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypA_char_spaced::rot-13::2` | `qwen3-30b-a3b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 30.64s | [EMPTY] |
| `p2::qwen3-32b::hypA_char_spaced::rot-12::0` | `qwen3-32b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `p2::qwen3-32b::hypA_char_spaced::rot-12::1` | `qwen3-32b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 49.02s | [EMPTY] |
| `p2::qwen3-32b::hypA_char_spaced::rot-12::2` | `qwen3-32b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 33.84s | [EMPTY] |
| `p2::qwen3-32b::hypA_char_spaced::rot-13::0` | `qwen3-32b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `p2::qwen3-32b::hypA_char_spaced::rot-13::1` | `qwen3-32b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `p2::qwen3-32b::hypA_char_spaced::rot-13::2` | `qwen3-32b` | Hypothesis A (Tokenization Intervention) | `char_spaced_stimuli` | **FAIL** | `ALGORITHMIC_DRIFT` | 0.00s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypB_compute_4096::rot-12::0` | `qwen3-30b-a3b` | Hypothesis B (Compute Scaling 4096) | `budget_4096_tokens` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 36.38s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypB_compute_4096::rot-12::1` | `qwen3-30b-a3b` | Hypothesis B (Compute Scaling 4096) | `budget_4096_tokens` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 50.75s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypB_compute_4096::rot-12::2` | `qwen3-30b-a3b` | Hypothesis B (Compute Scaling 4096) | `budget_4096_tokens` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 37.98s | [EMPTY] |
| `p2::qwen3-32b::hypB_compute_4096::rot-12::0` | `qwen3-32b` | Hypothesis B (Compute Scaling 4096) | `budget_4096_tokens` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 40.27s | [EMPTY] |
| `p2::qwen3-32b::hypB_compute_4096::rot-12::1` | `qwen3-32b` | Hypothesis B (Compute Scaling 4096) | `budget_4096_tokens` | **FAIL** | `FORMAT_EXTRACTION_FAILURE` | 37.75s | To decode the given **Rot-12** cipher, we rev |
| `p2::qwen3-32b::hypB_compute_4096::rot-12::2` | `qwen3-32b` | Hypothesis B (Compute Scaling 4096) | `budget_4096_tokens` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 35.07s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypC_fewshot_3shot::rot-12::0` | `qwen3-30b-a3b` | Hypothesis C (Few-Shot Calibration) | `fewshot_3shot` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 32.63s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypC_fewshot_3shot::rot-12::1` | `qwen3-30b-a3b` | Hypothesis C (Few-Shot Calibration) | `fewshot_3shot` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 35.49s | [EMPTY] |
| `p2::qwen3-30b-a3b::hypC_fewshot_3shot::rot-12::2` | `qwen3-30b-a3b` | Hypothesis C (Few-Shot Calibration) | `fewshot_3shot` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 36.09s | [EMPTY] |
| `p2::qwen3-32b::hypC_fewshot_3shot::rot-12::0` | `qwen3-32b` | Hypothesis C (Few-Shot Calibration) | `fewshot_3shot` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 30.00s | [EMPTY] |
| `p2::qwen3-32b::hypC_fewshot_3shot::rot-12::1` | `qwen3-32b` | Hypothesis C (Few-Shot Calibration) | `fewshot_3shot` | **FAIL** | `TOKEN_EXHAUSTION_AFTER_SOLVING` | 30.15s | [EMPTY] |
| `p2::qwen3-32b::hypC_fewshot_3shot::rot-12::2` | `qwen3-32b` | Hypothesis C (Few-Shot Calibration) | `fewshot_3shot` | **FAIL** | `TOKEN_EXHAUSTION_DURING_REASONING` | 51.67s | [EMPTY] |
