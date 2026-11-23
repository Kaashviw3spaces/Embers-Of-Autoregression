# Current descriptive comparisons

Primary conditions are in analysis/COMBINED_PRIMARY_FINDINGS.csv. Completed target containment, strict exact completion and target-in-reasoning diagnostics are distinct. Checkpoints and independent calls remain unverified.

## Phase 1: exact completed / received replies

| Requested label | Cipher | Direct: exact / replies | Standard: exact / replies | Table: exact / replies |
| --- | --- | --- | --- | --- |
| 30B-A3B | ROT-13 | 0 / 4 | 0 / 4 | 2 / 4 |
| 30B-A3B | ROT-12 | 0 / 4 | 0 / 4 | 1 / 4 |
| 32B | ROT-13 | 0 / 4 | 0 / 4 | 2 / 2 |
| 32B | ROT-12 | 0 / 3 | 0 / 3 | 0 / 2 |

## Phase 2: all returned replies are unfinished

| New test (3 planned per label) | Requested 30B-A3B | Requested 32B |
| --- | --- | --- |
| Spacing / ROT-13 | 3 replies; 3 unfinished | 0 replies; 0 unfinished; 3 API errors |
| Spacing / ROT-12 | 3 replies; 3 unfinished | 2 replies; 2 unfinished; 1 API error |
| Budget labeled 4096 / ROT-12 | 3 replies; 3 unfinished | 3 replies; 3 unfinished |
| Three examples / ROT-12 | 3 replies; 3 unfinished | 3 replies; 3 unfinished |

See analysis/friend2_phase2_cells.csv and PHASE2_CASE_AUDIT.csv. Source truncation flags are retained; finish_reason governs classification. Target text in reasoning is not called internally solved. No causal tokenization, architecture, thinking-switch or internet-retrieval claim is established.
