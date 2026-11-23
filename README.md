# Team Kybers | Paper 8: Embers of Autoregression

**Kaashvi Saini, Prachi Vats, Ashwin Anand, Aliyah Anand**

Start with `report/Combined_Report.pdf` (four pages), `slides/Presentation.pptx`
(five editable slides), and `Manual_Error_Review.xlsx` (30 distinct cases with no repeated inputs).
The main conclusion is a partial reproduction with traceable results; missing
model controls, participant reviews and twist results are stated explicitly.

This repository combines three supplied contributions: the first teammate's acronym
runs, the user's cipher pilots, and a second friend's multi-task and prompt-variant
records. It is an **incomplete reproduction**, with explicit scoring and provenance
limitations. Current outputs are regenerated from supplied evidence; no extension
success, checkpoint identity, manual review, or twist result is invented.

## Rebuild everything offline

Use Python 3.10 or newer. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 rebuild_evidence.py
```

After dependencies are installed, the rebuild is one command. It makes no API
requests and needs no API key. It generates:

- `report/Combined_Report.pdf` and `report/report.md` (four pages covering all
  supplied experiment sets: ciphers, multi-task pilots, prompt extensions,
  supporting acronyms, meaningful errors, validity checks, and hackathon status).
- `report/Review_Packet_30.pdf` (supplementary case explanations with evidence excerpts, separate
  from the report; it does not certify that participants reviewed the cases).
- `slides/Presentation.pptx`, `slides/Presentation.pdf`, and `slides/presentation.md` (five slides).
- `Manual_Error_Review.xlsx`: one simple sheet with 30 unique test inputs:
  five completed wrong answers and 25 clearly labeled unfinished replies;
  editable check/note columns and source comments.
- Root `MASTER_*` files, mirrored in `results/master/` as compatibility copies.
- `analysis/run_summary.csv`, `current_summary.json`, `dataset_checks.json`, and
  `matched_comparison.json`.
- `analysis/friend2_extension_cells.csv`, `friend2_audit.json`, and
  `friend2_payload_repeats.csv`: computed prompt-variant results, errors, and
  evidence limitations for the third contribution.
- `analysis/friend2_phase2_cells.csv` and `PHASE2_CASE_AUDIT.csv`: the added
  spacing, larger-budget, and three-example trials, including source-flag conflicts.
- `analysis/ARCHIVE_UPDATE_DIFF.json`: changed and unchanged files in the updated ZIP.
- `analysis/FINAL_DIRECTORY_AUDIT.csv` and `.json`: every file and directory in
  the final expanded folder; duplicate exports checked against original logs.
- `analysis/EXPANDED_CAMPAIGN_CELLS.csv`: 56 added short-budget responses, of which
  eight completed word counts and 48 are unfinished. These add no completed errors.
- `analysis/COMBINED_PRIMARY_FINDINGS.csv`: all 21 multi-task conditions.
- `analysis/KEY_ERROR_EVIDENCE.csv`: the five completed content errors with sources.
- `analysis/REPORT_EVIDENCE_INDEX.csv`: source rows for the main report's
  multi-task results, prompt extensions, and key errors.
- `data/selected_tests_reconstructed.jsonl` (the documented seed-42 60-item
  selection) and `data/planned_matrix.csv` (480 planned, not executed, cells).
- `MANUAL_FAILURE_REVIEW.csv`, `analysis/REVIEW_FIRST_30.csv`, and quarantined records.

Historical per-run packages are preserved, but their scores are superseded by
the explicit current metrics. Do not count generated copies as new experiments.
`CORRECTIONS.md` describes the changes; `evidence/legacy_generated/` preserves
the original unsupported documents for internal audit, not as submission claims.

## Validate

```bash
python3 -m unittest discover -s tests -v
python3 validate_submission.py
```

Tests cover answer-key-independent extraction, completion limits, reasoning
separation, conservative normalization, source deduplication, deterministic
answer keys, measured token fields, redaction, and preservation of reviewer notes.

## Scoring

Primary: a response must finish with `stop`, have nonempty final/stored answer
text, and equal the reference after trimming surrounding whitespace. Secondary:
limited quotes, fences, and simple acronym separators are normalized. Extraction
never searches for the answer key. Legacy `stored_correct` flags remain visible
but are not treated as completed-answer accuracy.

Old logs may mix reasoning and final text. Current scores on those logs are
descriptive rescoring of available stored text, not proof of original final-channel
performance and not a claim to duplicate the paper's exact grader. API errors have
no model score. Fourteen repeated shortened ROT-12 excerpts are quarantined.
Results from different contributors, prompts, modes, token budgets, or smoke/pilot
runs are kept separate. Checkpoint and effective thinking-mode verification remain
unresolved. Do not pool all rows into one benchmark accuracy.

The completed-visible-target-containment column is a diagnostic, kept separate
from exact matching. Target presence in reasoning is never called "solved
internally" and never awards a completed-answer success. The third contribution
adds 54 extension attempt records for 48 item opportunities: 42 returned responses
and 12 request errors. Six UIDs were retried after errors; six items have no
returned response. Cells have different response denominators, which are shown.

The updated ZIP adds 24 phase-2 attempts (20 replies, four API errors) covering
character spacing, a budget labeled 4096, and three demonstrations. Every returned
reply ends with `length`; none is a completed answer. All 20 incorrectly carry
`is_truncated=false` in the source. We preserve that flag and classify using the
finish reason. No per-call token usage or full request envelopes were supplied.
The source document's claims of confirmed calibration, a tokenization mechanism,
or internal solving are not adopted. The spacing prompts contain a literal
`{shift_k}` placeholder, and two new budget payload pairs repeat across model
labels. See `analysis/friend2_phase2_cells.csv` and `PHASE2_CASE_AUDIT.csv`.

Its `direct_mode` is an answer-only prompt, not an API thinking-disable switch;
all returned Direct records still have reasoning. Its `retrieved_guidance` uses
an authored table embedded in code, with no logged web retrieval. Treat this as
a small prompt-variant pilot, not proof of the submitted thinking/internet effects.

## Human review still required

The Excel sheet contains five completed errors and 25 unfinished responses. The
`report/Review_Packet_30.pdf` explains 30 selected cases in simple words:
5 wrong completed answers and 25 unfinished responses. These are 30 cases,
not 30 different error types. Each shows the expected answer, observed answer,
supporting excerpt, explanation, and source reference. There is no teammate section.
Correct answers with extra explanation and API errors are excluded from this review.
The larger automatic index remains separate in `analysis/ALL_CANDIDATE_FAILURES.csv`.

Open `MANUAL_FAILURE_REVIEW.csv` for the same 30 cases and their full stored text.
Fill `human_category`, `human_notes`,
`reviewer_name`, and `human_verified=True` only after personally reviewing the case.
At least 30 cases need participant review for the hackathon. Truncations can be
reviewed as budget-limited noncompletion, not proof of an intrinsic inability.

The same selected cases are copied to `analysis/REVIEW_FIRST_30.csv` for compatibility,
but **edit the root MANUAL_FAILURE_REVIEW.csv**. Rebuilding preserves
reviewer fields there. Counts require True plus a reviewer name and substantive
notes. AI/deterministic annotations alone do not count as participant review.

## Original evidence and provenance

- `runs/*.json`: original teammate source records, unchanged.
- `evidence/user/originals/failure_collection.jsonl`: original uploaded user log.
- `evidence/user/redacted/`: shared copies and a labeled pilot transcription.
- `evidence/friend2/`: redacted snapshots of the new project's two canonical logs,
  a duplicate master retained only for audit, benchmark subsets, reference scripts,
  and historical analyses with warning banners. `IMPORT_MANIFEST.json` records
  original and snapshot hashes. The original `embers_replication` folder is unchanged.
- Its 63 primary source records do not contain a model field. The model declared
  in its README/defaults is not substituted for missing per-call model identity.
- Its cloned `repo/` folder contains published-author closed-model results and code.
  Those reference files are excluded from team experiment counts and the bundle.
- The user pilot file was pasted in chat and reconstructed; its original file
  remains missing. Earlier curl tests were not all supplied as saved files.
- The full user-selected dataset was not uploaded. A labeled reconstruction
  uses the supplied matching stimuli and the documented random seed; this is
  not claimed to be the original file.
- The 33-row legacy 32B pilot has uniform latency/token metadata and no original
  API envelopes. Resolve provenance before drawing a cross-checkpoint conclusion.
- Quarantined cipher excerpts need full originals. This flags missing evidence;
  it is not a claim about intent or fabrication.

The complete original project (excluding its virtual environment/cache) was backed
up before editing. `BACKUP_LOCATION.txt` records the external backup path. Original
logs are never rewritten by the offline rebuild. Generated summaries are replaceable.

The first corrected two-contributor archive is retained locally as
`submission/Embers_Two_Contributors_Previous.zip`. The current archive is the
three-contributor version. The third project's hard-coded credential was redacted
in copied files and should be rotated if still active; it is not used by this rebuild.

## Future live runs: explicit opt-in

No new inference calls were made during correction. Preview a request without a key:

```bash
python3 run_experiment.py --model qwen3-32b --task_type cipher --conditions rot13dec --max_samples 1
```

Actual requests require `--live`, `OPENAI_BASE_URL` for the shared open-model server,
and `OPENAI_API_KEY` or hidden input. Do not put a key in a file or CLI argument.
The runner is sequential, uses the same system task instruction across modes,
saves each attempt immediately, and stops on the first server/connection error.
It does not automatically retry requests that may still occupy server slots.
It writes new timestamped `runs/live_attempts_*.jsonl` files, which the offline
rebuild can import. `--intervention` supports baseline, thinking, guidance, and
thinking_guidance; requested switches do not establish effective server behavior.

`verify_models.py --base_url ...` lists advertised aliases only, not verified
checkpoint identities. No paid-model endpoint is used by default.

## Package for handoff

```bash
python3 package_submission.py
```

This rebuilds current artifacts and creates `submission/Embers_Corrected_Combined.zip`.
The ZIP includes code, stimuli, redacted source copies, logs, CSV analyses, report,
and slides. It excludes virtual environments, caches, unredacted user originals,
and superseded documents. Original local logs and the external backup remain
preserved. JSON source copies in the ZIP are reserialized/redacted; the ZIP's
manifest hashes its own contents, while `analysis/source_hashes.json` refers to
the untouched local source files. Participant review remains a requirement.

## Sources and disclosure

Official prompts and datasets: https://github.com/tommccoy1/embers-of-autoregression/
Paper: https://arxiv.org/pdf/2309.13638 (preprint; the hackathon names PNAS 2024).
User saved guidance: https://en.wikipedia.org/wiki/Caesar_cipher
The teammate `retrieval/guidance.txt` contains mathematical guidance but lacks
retrieval provenance; do not call it web-retrieved evidence without a source record.

ChatGPT assisted planning, code, debugging, inspection, correction, transcription,
annotations, and writing. Original teammate documents name Antigravity assistance;
third-project documents name an @verifier role without establishing whether it
was human review. Confirm the complete tool list and review history before submission.
Experimental outputs are the
supplied shared-server records. Confirm the exact submitted predictions, participant
review, original checkpoint/mode provenance, and surprise-twist results before
claiming those requirements are complete.
