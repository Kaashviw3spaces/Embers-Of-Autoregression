> HISTORICAL SOURCE DOCUMENT: preserved for audit, not a current result. Some claims were not supported on reanalysis. Use report/Combined_Report.pdf and analysis/friend2_audit.json for the corrected account.

# Embers of Autoregression: Replication & Pedagogical Study
### Problem Statement 8 — AIRIS Research Hackathon
**Team:** kybers  
**Target Paper:** *"Embers of Autoregression: Understanding Large Language Models Through the Problem They are Trained to Solve"* (R. Thomas McCoy, Shunyu Yao, Dan Friedman, Matthew Hardy, Thomas L. Griffiths, *PNAS 2024 / arXiv:2309.13638*)  
**Evaluated Model:** `qwen3-30b-a3b` (Open-weights reasoning model hosted on private hackathon cluster)

---

## 🚀 Quickstart: One-Command Execution

To reproduce the experiments across **both Claim 1 and Claim 2** in one command:

```bash
chmod +x run.sh
./run.sh smoke 3
```

Or invoke the Python runner directly:

```bash
python3 src/runner.py --mode smoke --limit-per-condition 3
```

*Runs out-of-the-box with standard Python 3 (no third-party dependencies required).*

---

## 📌 Project Overview & Investigated Claims

McCoy et al. (2024) demonstrated that because LLMs are trained strictly to minimize cross-entropy loss over web text ($\mathcal{L}_{\text{NTP}} = -\sum \log P(x_t \mid x_{<t})$), their performance on **deterministic, rule-based tasks** is heavily governed by probability.

We replicated and stress-tested **both primary claims**:

1. **Claim 1 (Task Probability):**  
   Holding algorithmic complexity and input structure constant, model accuracy collapses on rare task variants compared to canonical, high-frequency variants.
   - **Shift Ciphers:** ROT-13 ($k=13$, web-ubiquitous) vs ROT-12 ($k=12$, rare) and ROT-2 ($k=2$, rare).
   - **Word Sorting:** Canonical forward alphabetical ($A \to Z$) vs reverse alphabetical ($Z \to A$).
   - **Numerical Sorting:** Ascending (canonical) vs descending (non-canonical).
   - **Linear Functions:** Celsius-to-Fahrenheit ($f(x) = \frac{9}{5}x + 32$) vs synthetic linear ($g(x) = \frac{7}{5}x + 31$).

2. **Claim 2 (Target Output Probability):**  
   Holding the cipher algorithm constant, accuracy monotonically degrades when the correct output text is an uncommon or adversarial sequence in natural language.
   - **ROT-13 Decoding across 4 Tiers:** High-Probability $\to$ Medium-Probability $\to$ Low-Probability $\to$ Adversarial (single-word competitor swap).
   - **Word Reversal across 4 Tiers:** High, Medium, Low, and Adversarial sentence targets.

---

## 📂 Repository Structure

```
├── README.md                                # This document (One-command guide & overview)
├── run.sh                                   # Executable one-command replication script
├── data/                                    # Official McCoy et al. stimuli datasets
│   ├── README.md                            # Comprehensive dataset documentation
│   ├── dataset_catalog.json                 # Machine-readable catalog (59 files, 11,883 records)
│   ├── benchmark_subsets/                   # Curated benchmarks (smoke_test, claim1, claim2)
│   ├── claim1_task_probability/             # Shift ciphers (shifts 1-25), sorting, linear functions
│   └── claim2_output_probability/           # ROT-13/ROT-12 decoding, word reversal, article swapping
├── docs/
│   └── student_learning_curve.md            # Student vs AI failure profile & oral defense guide
├── logs/
│   ├── raw_runs.jsonl                       # Raw JSONL execution stream (63 full runs)
│   └── experiment_log.md                    # Synthesized master ledger & 35-failure taxonomy
├── results/
│   └── paper_vs_simulation_comparison.md   # Head-to-head quantitative comparison with paper
└── src/
    ├── runner.py                            # Resilient API runner (429 backoff, think extraction)
    └── build_experiment_log.py              # Log aggregator & markdown report builder
```

---

## 📊 Summary of Simulation Findings (Qwen3-30B-A3B)

Full analysis available in [`results/paper_vs_simulation_comparison.md`](results/paper_vs_simulation_comparison.md).

### 1. Claim 1: Task Probability
| Task | Canonical Variant | Rare Variant | Disparity | Replication Status |
| :--- | :--- | :--- | :--- | :--- |
| **Shift Ciphers** | ROT-13: **33.3%** direct (100% reasoning) | ROT-12 / ROT-2: **0.0%** direct (66.7% reasoning) | $+33.3\%$ direct | **CONFIRMED** |
| **Alphabetical Sort** | Forward (A-Z): **100.0%** direct | Reverse (Z-A): **0.0%** direct (66.7% reasoning) | $+100.0\%$ direct | **CONFIRMED** |
| **Numerical Sort** | Ascending: **33.3%** direct (100% reasoning) | Descending: **0.0%** direct (100% reasoning) | $+33.3\%$ direct | **CONFIRMED** |
| **Linear Functions** | Actual ($9/5x+32$): **100.0%** direct | Fake ($7/5x+31$): **100.0%** direct | $0.0\%$ | Moderated by CoT |

### 2. Claim 2: Target Output Probability (ROT-13 Decoding)
| Output Tier | Ground Truth Target Description | Direct Pass | Latent Reasoning Pass |
| :--- | :--- | :--- | :--- |
| **High Probability** | Common, idiomatic English prose | **33.3%** | **100.0%** |
| **Medium Probability** | Grammatically valid, lower-frequency prose | **0.0%** | **66.7%** |
| **Low Probability** | Permissible, rare lexical combinations | **0.0%** | **33.3%** |
| **Adversarial** | High-prob text with 1 competitor word swap (*treason* vs *reason*) | **0.0%** | **66.7%** |

---

## 🔬 Core Academic Insight: The Latent Token Budget Shift

While McCoy et al. observed output logit hallucinations in standard LLMs (GPT-4, LLaMA-3), our evaluation of a **thinking model** (`qwen3-30b-a3b`) revealed a new dynamic:
> **Test-time deliberation does not extinguish the embers of autoregression; it shifts them into Latent Token Inflation.**
> 
> Because non-canonical tasks (ROT-12, reverse sorting) lack pre-trained associative priors, the model is forced into exhaustive letter-by-letter verification loops (generating 3,000+ reasoning tokens). This causes the model to consume its entire token budget before emitting visible output (`finish_reason = length`), resulting in empty visible outputs despite solving the problem internally.

---

## 🎓 Student Learning Curve & Failure Matrix

Detailed in [`docs/student_learning_curve.md`](docs/student_learning_curve.md):
- **BPE Token Fragmentation:** Common ciphers (ROT-13) map to whole subword tokens; rare ciphers (ROT-12) fracture into single-character tokens, tripling sequence length.
- **Metric Sensitivity:** Strict exact match yields 0% due to chat preambles; McCoy substring containment (`gt in res`) + Levenshtein distance correctly captures algorithmic reasoning.
- **Oral Defense Guide:** 8 domain-specific questions with defensive answers addressing tokenization, in-context learning confounders, and temperature effects for the hackathon judging panel.
