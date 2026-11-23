# Team Kybers: Clear Rules, Unexpected Mistakes

**Paper 8 — Embers of Autoregression**

**Team:** Kaashvi Saini, Prachi Vats, Ashwin Anand, Aliyah Anand

We tested how reliably Qwen follows exact rules in ciphers, acronyms, reversal,
sorting and related tasks. Our combined evidence contains 596 source records:
554 returned model outputs and 42 request errors. Duplicate exports are not
counted as extra experiments. Fourteen repeated shortened cipher excerpts are
excluded from scoring.

Our clearest completed errors include decoding ROT-13 `cngu` as **way** instead
of **path**, two unrelated ROT-12 sentences, **LITERALL** instead of **LITERAL**,
and **APPLEID** instead of **APPLIED**. We also report correct counterexamples
and unfinished responses separately. In a small matched ROT-12 prompt comparison,
an authored substitution table produced one exact completed answer out of four
replies; Direct and Standard each produced none. This is a pilot observation,
not proof of a general guidance benefit.

Our reproduction is partial. Two distinct server checkpoints, effective thinking
controls and an internet-access effect are not verified. Additional spacing,
larger-budget and three-example trials returned no completed answers. The final
short-budget campaign adds eight completed word counts and 48 unfinished replies.
The report explains the setup, scoring, limitations, source checks and failure cases.

## Required links

- **Public GitHub repository:** https://github.com/Kaashviw3spaces/Embers-Of-Autoregression
- **Research report PDF:** https://github.com/Kaashviw3spaces/Embers-Of-Autoregression/blob/main/report/Combined_Report.pdf
- **PowerPoint on Google Drive:** https://docs.google.com/presentation/d/1FXoexbKv0SAWmk9ruZKXXCcJ4u9x8Fek/edit?usp=drivesdk&ouid=105365974121316586168&rtpof=true&sd=true

Before posting: the PPT upload is verified, but its current permission is private.
Set General access to Anyone with the link / Viewer and verify it opens for judges.
This note is an operational reminder; remove it after checking the sharing setting.

## Supporting material in the repository

- Five-slide editable PowerPoint and matching PDF.
- Four-page report in easy words.
- `Manual_Error_Review.xlsx`: 30 distinct inputs; five completed content errors
  and 25 clearly labeled unfinished replies, with no repeated test inputs.
- Source logs, errors, answer-key checks and a file-by-file directory audit.
- Separate 30-case reading packet: five wrong completed answers and 25 unfinished
  replies. Participant manual review is not certified; the five-row Excel is not
  a claim that 30 completed wrong answers have been reviewed.
- No surprise-twist result was supplied.

After installing dependencies, rebuild offline with `python3 rebuild_evidence.py`.
No API key or model call is required for the rebuild.

**Disclosure:** ChatGPT assisted planning, code, debugging, evidence checks,
annotations, report and presentation. Supplied source documents also name
Antigravity and an `@verifier` role. Experimental responses come from supplied
logs; missing results and human verification were not invented.

Submit one Writeup for the team in Kaggle's **Writeups** section. Include all three
required links/files, confirm judges can open them, and click **Submit**. A draft
is not a final submission. Select the appropriate track shown by Kaggle.
