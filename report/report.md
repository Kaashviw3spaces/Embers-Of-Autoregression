# Paper 8: Combined Experiments and Findings

Team Kybers: Kaashvi Saini, Prachi Vats, Ashwin Anand, Aliyah Anand

AIRIS Research Hackathon | Embers of Autoregression | Experiments: 23 November 2026 | Updated 24 November 2026

We tested exact rule-following across ciphers, acronyms, sorting, word reversal, linear functions and article swapping. The strongest completed mistakes are a changed word in ROT-13, two unrelated ROT-12 sentences, an extra acronym letter and letters in the wrong order. Other tests completed correctly. Many responses ran out of output budget, so they must be reported as unfinished rather than as proven wrong answers.

## The paper claim we tested

The paper predicts that familiar tasks, inputs and outputs are easier for language models even when the rule is deterministic. Its arXiv abstract reports GPT-4 cipher accuracy of 51% for high-probability outputs and 13% for low-probability outputs [1]. We tested related conditions on requested Qwen3-30B-A3B and Qwen3-32B labels. A shift comparison tests task familiarity; changing sentence wording or order tests a different question about output probability. These are separate comparisons.

## All supplied experiment sets are included

| Experiment set | Rows | Replies | Errors | What it adds |
| --- | --- | --- | --- | --- |
| Acronym + early cipher runs | 372 | 367 | 5 | Acronym frequency conditions; early cipher records |
| Additional cipher attempts | 27 | 6 | 21 | Completed ROT-12/13 errors, one success, and setup failures |
| Multi-task pilot | 63 | 63 | 0 | 21 conditions: ciphers, sorting, reversal, functions, articles |
| Cipher prompt extensions | 54 | 42 | 12 | Two requested models; Direct, Standard and Table prompts |
| New spacing / budget / examples | 24 | 20 | 4 | Character spacing, budget labeled 4096, and three examples |
| Final short-budget campaign | 56 | 56 | 0 | Counting and additional reversal, sorting, swapping, arithmetic and Pig Latin checks |

Total: 596 source records, 554 returned outputs and 42 request errors. These are recorded rows, not a claim of that many independent calls. The 60 prepared cipher cases (30 per shift) are a test plan; preparing them does not mean every case was run. Fourteen repeated shortened cipher excerpts are excluded from scoring.

## How we checked the tests

All 554 returned-record answer keys pass rule checks: letter shifts, initials, sorting, reversal, counting, arithmetic and article swapping. Pig Latin references were checked by encoding them back to the input; decoding can be ambiguous. The 3,400 supplied acronym/cipher stimulus keys also pass. Each example links to a file and row. Generated copies and published-author logs are not counted as new team experiments.

We keep three outcomes separate: (1) completed exact answer, (2) completed visible text containing the target with extra explanation, and (3) unfinished response (finish_reason=length). The second is a diagnostic, not answer-only accuracy. API errors are not wrong model answers. Source code and logs do not independently verify backend identity; some requests for 32B returned a 30B label.

# Replication Findings: Ciphers and Other Tasks

The multi-task pilot has 63 records in 21 conditions, with three examples per condition. The table covers all 21 conditions. Fractions below count completed visible replies containing the expected answer; they do not count text found only in reasoning. All 20 completed replies contain the target, but include explanations; 43 replies are unfinished. None are answer-only exact matches.

| Test family | Completed replies containing the expected answer | What we learn |
| --- | --- | --- |
| Cipher familiarity | ROT-13 1/3; ROT-12 0/3; ROT-2 0/3 | ROT-12 and ROT-2 do not finish; this is a completion gap, not six proven wrong decodings. |
| Alphabetical sorting | Forward 3/3; reverse 0/3 | Forward finishes on all three; reverse finishes on none. |
| Number sorting | Ascending 0/3; descending 0/3 | Both directions run out of output budget. |
| Linear functions | Familiar 3/3; altered 3/3 | Both finish with the target. The altered formula does not fail in these examples. |
| ROT-13 output groups | Ordinary 1/3; Medium 0/3; Reordered 0/3; Altered word 0/3 | One ordinary reply finishes; the other groups all truncate. Only three items per group. |
| ROT-12 output groups | Ordinary 0/3; reordered 0/3 | All six truncate; there is no observed gap between these groups. |
| Word reversal | Ordinary 3/3; Medium 2/3; Reordered 2/3; Altered word 2/3 | Unusual outputs sometimes succeed. Familiar wording is not required for every answer. |
| Article swapping | Ordinary 0/3; reordered 0/3 | All six truncate; neither group has a completed answer. |

Chart: ordinary ROT-13 1/3; reordered ROT-13 0/3; reordered reversal 2/3. Different tasks are shown separately; these are small descriptive counts.

## Acronym pilots: included as supporting evidence

| Requested label / condition | Exact completed | Unfinished |
| --- | --- | --- |
| 30B-A3B / common input / output | 27/100 | 71 |
| 30B-A3B / rarer input | 8/100 | 92 |
| 30B-A3B / rarer output | 5/100 | 94 |
| 32B / common input / output | 32/33 | 0 |

The acronym table uses the stricter completed exact-answer rule. Older correct flags sometimes counted target letters inside unfinished reasoning, so those old flags are not the headline result. The legacy 32B pilot lacks original API envelopes and has uniform latency/token fields; its 32/33 result cannot establish an architecture advantage.

Relation to the paper: some completion patterns fit the familiarity prediction, but do not prove its cause. Both linear formulas work, and unusual reversal outputs sometimes work. Three items per condition, repeated payloads and missing backend evidence prevent a strong numerical replication of the paper.

## What the final folder adds

Its 56 additional responses contain eight completed one-word counting answers and 48 unfinished replies. Common-word and rare-word counting each finish correctly in 4/5 cases on the requested 30B label; every target is 1. This is a basic check, not evidence of a frequency gap. All other added tasks are unfinished. The source code uses different short budgets for the two model labels (250 versus 150), so we exclude claims that one model is better. All 82 source files were audited; duplicate exports match the original run logs.

# Extensions: Thinking, Guidance and New Tests

## Original predictions and prompt comparisons

We predicted thinking and internet-sourced guidance would help ROT-12 more than ROT-13; the team reports submitting that prediction. The saved first extension compares Direct (answer-only instruction), Standard (ordinary prompt, named thinking_mode in the source), and Table (authored substitution table). Direct still generates reasoning, and Table has no logged web retrieval. These are prompt comparisons; actual thinking-on/off and internet effects remain unestablished.

| Requested label | Cipher | Direct: exact / replies | Standard: exact / replies | Table: exact / replies |
| --- | --- | --- | --- | --- |
| 30B-A3B | ROT-13 | 0 / 4 | 0 / 4 | 2 / 4 |
| 30B-A3B | ROT-12 | 0 / 4 | 0 / 4 | 1 / 4 |
| 32B | ROT-13 | 0 / 4 | 0 / 4 | 2 / 2 |
| 32B | ROT-12 | 0 / 3 | 0 / 3 | 0 / 2 |

Each cell planned four items. Fractions show exact completed answers / received replies, excluding API errors. Phase 1 has 48 item opportunities, 54 attempt records, 42 replies (33 unfinished) and 12 errors; six items have no reply. The full 12-cell table, including missing items, errors and unfinished counts, is analysis/friend2_extension_cells.csv. We select the first returned reply per item without choosing on correctness.

A useful matched case: for requested 30B-A3B, ROT-12 item 2, Direct and Standard both truncated with empty final content. Table returned exactly "Well, it was not exactly planned from the beginning." This is one observed completion, not a reliable general benefit. All five exact Phase-1 replies used Table; four Standard replies contained the target with explanations. The separate web-sourced pilot truncated and changed its system instruction, so it does not isolate internet guidance.

## Added in the updated ZIP: three exploratory interventions

| New test (3 planned per label) | Requested 30B-A3B | Requested 32B |
| --- | --- | --- |
| Spacing / ROT-13 | 3 replies; 3 unfinished | 0 replies; 0 unfinished; 3 API errors |
| Spacing / ROT-12 | 3 replies; 3 unfinished | 2 replies; 2 unfinished; 1 API error |
| Budget labeled 4096 / ROT-12 | 3 replies; 3 unfinished | 3 replies; 3 unfinished |
| Three examples / ROT-12 | 3 replies; 3 unfinished | 3 replies; 3 unfinished |

The new log adds 24 attempts: 20 replies, all unfinished, and four API errors. No new condition produced a completed answer. Spacing changes the input presentation; the larger-budget and three-example conditions use ROT-12. These additional hypotheses are exploratory: no evidence of a prior submitted prediction was supplied for them.

The budget is labeled 4096 in the condition and source code; per-call configuration and token usage are absent. The complete target appears in reasoning in 6/6 budget replies and 4/6 three-example replies. That is a text-containment diagnostic, not proof the task was solved internally. These trials did not deliver completed answers; they do not prove that more compute or examples can never help.

Some source flags wrongly call these 20 unfinished replies untruncated. We use the server finish reason and keep the original flags. Spacing prompts also contain an unfilled template label; no measurements show how letters were tokenized. The data cannot establish a tokenization cause. Seven identical-payload groups, including two new cross-model budget pairs, leave model identity and independent calls uncertain.

# Meaningful Errors, Validity and Hackathon Status

These five replies finished and chose wrong content. The simple Manual_Error_Review.xlsx contains only these five cases, with short explanations and space for your check. Source details are in cell comments and analysis/KEY_ERROR_EVIDENCE.csv. Unfinished replies and correct answers with extra explanation are excluded from the Excel sheet.

| Case / task | Expected | Actual completed answer | Specific error |
| --- | --- | --- | --- |
| F1: ROT-13 | ...their own path... | ...their own way... | Wrong word |
| F2: ROT-12 | But this time, there may also be another reason. | How would you like them done in a little while? | Wrong sentence |
| F3: ROT-12 | I think everyone has their own path, and they can make it happen. | I cannot understand the people around me, but they are very polite. | Wrong sentence |
| F4: Acronym | LITERAL | LITERALL | Extra letter |
| F5: Acronym | APPLIED | APPLEID | Letters in wrong order |

Why the cipher errors matter: ROT-13 cngu must decode to path, not its synonym way. In F2, the explanation even states N becomes H although shifting N back by 12 gives B. These are checkable rule violations. They are compatible with an influence of fluent language, but these examples alone do not establish a pretraining-probability mechanism.

## An additional useful trace: doubting the literal answer

In an altered-word ROT-13 case, the trace decodes principals, then says the intended word is probably principles and starts rechecking. The answer key really is principals. A reordered case similarly questions the phrase another may. These are qualitative signs of conflict with natural wording, not completed wrong answers: both runs truncate. They help explain why we separate internal discussion from the final response.

## What this supports for the hackathon

| Hackathon item | Evidence and current status |
| --- | --- |
| Central claim + two open models | Task/output conditions tested. Two Qwen labels requested; two distinct backends remain unverified. |
| Extension + prior prediction | Team reports submitting its original prediction. Prompt variants and new exploratory tests are logged; verified thinking/internet effects remain unestablished. |
| 30 failures read by hand | Excel shows only 5 clear completed errors. A separate 30-case packet adds 25 unfinished replies. 0 participant reviews confirmed; this requirement is not certified. |
| Surprise twist | No twist results were supplied. |
| Code, report, slides, all logs | Offline rebuild, this four-page report, five slides, a simple Excel sheet, recorded outputs/errors, source references and AI disclosure are included. |

The defensible conclusion is a partial reproduction: real exact-rule errors and uneven completion were observed, alongside successful counterexamples. The tests and calculations are traceable; a causal explanation, reliable effect size, two verified checkpoints, and completed thinking/internet ablations are not established. The supplied brief explicitly accepts an honestly explained unsuccessful reproduction [2].

## Sources and disclosure

[1] McCoy et al., Embers of Autoregression, arXiv:2309.13638 (2023 preprint; PNAS 2024): https://arxiv.org/abs/2309.13638. Official stimuli: https://github.com/tommccoy1/embers-of-autoregression. [2] Supplied AIRIS Research Hackathon Problem Statements PDF. Additional resource: saved Wikipedia Caesar-cipher excerpt. Experimental evidence: supplied run files and redacted source logs; see MASTER_RAW_RESPONSES.jsonl and analysis/REPORT_EVIDENCE_INDEX.csv.

ChatGPT assisted planning, code, debugging, checking logs, annotations, report and slides. Supplied documents also name Antigravity and an @verifier role; participants should confirm the complete tool list. These annotations are AI-assisted, not a certification of human review. No experimental outputs or missing results were generated during this report rebuild.
