# AIRIS 2026 | Embers of Autoregression

Team Kybers: Kaashvi Saini, Prachi Vats, Ashwin Anand, Aliyah Anand. Problem: the paper predicts that task, input and output familiarity affect exact deterministic tasks. We test related conditions using supplied Qwen logs. This is a partial reproduction; backend identities are not independently verified. Reference: https://arxiv.org/abs/2309.13638.

# Same rules. Different completion.

Workflow: supplied paper inputs -> requested Qwen API -> saved responses -> independent deterministic answer-key checks -> error review. Counts include all canonical source rows once: 596 records, 554 returned outputs, 42 request errors. Fourteen shortened cipher excerpts are excluded from scoring. Graph: completed visible text containing the expected answer, n=3 per condition; explanations allowed. This is a diagnostic, not answer-only accuracy. The primary logs do not record per-call model identity. Source: analysis/COMBINED_PRIMARY_FINDINGS.csv.

# Five clear errors.

All five examples have finish_reason=stop. F1 ROT-13 changes path to way. F2 ROT-12 returns How would you like them done in a little while? instead of But this time, there may also be another reason. F3 ROT-12 returns I cannot understand the people around me, but they are very polite. instead of I think everyone has their own path, and they can make it happen. F4 LITERAL -> LITERALL adds L. F5 APPLIED -> APPLEID swaps I and E. Full source IDs, file rows and actual responses: analysis/KEY_ERROR_EVIDENCE.csv and Manual_Error_Review.xlsx. No causal claim about training probability is established.

# Can guidance help a cipher finish?

Original predictions: thinking and internet-sourced guidance help ROT-12 more than ROT-13; the team reports submitting its prediction. Actual first extension is a prompt comparison, not verified thinking on/off or internet access. Direct still has reasoning; Table is authored guidance. Left chart: requested qwen3-30b-a3b, ROT-12, Direct 0/4 exact, Standard 0/4, Table 1/4. Same item 2: Direct and Standard truncated with empty final content; Table returned Well, it was not exactly planned from the beginning. New exploratory spacing/budget/few-shot log: 24 attempts, 20 returned responses, all length-ended, four errors. Budget 4096 is stated in source code/condition, not measured usage. No complete answer in that log. Sources: friend2_extension_cells.csv, friend2_phase2_cells.csv and PHASE2_CASE_AUDIT.csv.

# Useful evidence. Careful conclusions.

Observed: five completed rule-violating answers, a matched guided ROT-12 completion, and correct counterexamples in other deterministic tasks. The final campaign adds 56 short-budget responses: eight completed word counts (all targets 1), 48 unfinished; uneven source budgets prevent a fair architecture comparison. Overall reproduction is partial: distinct checkpoint identities, effective thinking switches and an internet effect are not established. The Excel and supplementary packet contain 30 distinct inputs: five completed wrong answers and 25 unfinished responses. Zero participant reviews are confirmed in the supplied files; this is not a claim of 30 human-reviewed completed errors. No surprise-twist result was supplied. AI assistance: ChatGPT; supplied documents also name Antigravity and an @verifier role. References and all evidence are in the report and source index.
