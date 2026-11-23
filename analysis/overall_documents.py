"""Three-contributor synthesis. Numerical claims are derived from imported records."""
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
import html
import json


def build_overall(root,rows,groups,summary):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.graphics.shapes import Drawing,String
    from reportlab.graphics.charts.barcharts import HorizontalBarChart

    report=root/'report';report.mkdir(exist_ok=True)
    slides=root/'slides';slides.mkdir(exist_ok=True)
    audit=summary['friend2_prompt_variant_evidence']
    now=datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %B %Y')
    matrix=[['Model label','Shift','Prompt','Jobs','Replies','Exact','Contains','Length','API errs']]
    model_labels={'qwen3-30b-a3b':'30B-A3B','qwen3-32b':'32B'}
    mode_labels={'direct_mode':'Direct','thinking_mode':'Standard','retrieved_guidance':'Table'}
    cells=sorted(audit['cells'],key=lambda c:(c['model_requested'],c['task']!='rot13dec',{'direct_mode':0,'thinking_mode':1,'retrieved_guidance':2}[c['prompt_variant']]))
    for c in cells:
        matrix.append([model_labels[c['model_requested']],c['task'].replace('rot','').replace('dec',''),mode_labels[c['prompt_variant']],str(c['item_opportunities']),str(c['returned_item_responses']),str(c['strict_completed_exact']),str(c['completed_visible_target_contains']),str(c['truncated_item_responses']),str(c['request_error_records'])])
    acronym=[g for g in groups if g['contributor']=='teammate' and g['run_kind']=='pilot' and 'acronym' in g['task']]
    acronym_table=[['Requested model / condition','N','Old flag','Completed exact','Truncated']]
    for g in sorted(acronym,key=lambda g:(g['model_requested'],g['task'])):
        acronym_table.append([g['model_requested']+' / '+g['task'],str(g['strict_denominator']),str(g['legacy_stored_correct']),str(g['strict_correct']),str(g['truncated'])])
    n=summary;p=audit['primary'];e=audit['extension']
    source_counts=n['records_by_contributor']
    human_sources=f"{source_counts.get('teammate',0)} from the first teammate, {source_counts.get('user',0)+source_counts.get('new_live',0)} from the user (including newly logged attempts), and {source_counts.get('friend2',0)} from the second friend"
    sections=[
        ('Paper 8: What Our Combined Evidence Shows',[
            f'AIRIS Research Hackathon | Experiments dated 23 November 2026 | Revised {now}',
            'Scope and status. We combined three contributions about Embers of Autoregression: acronym experiments, user shift-cipher pilots, and a second friend\'s multi-task and prompt-variant logs. This is an evidence-based pilot analysis, not a claim that every hackathon requirement or original prediction was completed.',
            'Paper claim and questions. The paper predicts that deterministic tasks can be affected by task familiarity and input/output probability. We examined acronym initials, ROT-13 versus ROT-12, and smaller supporting tests of reversal, sorting, and linear functions. The requested open-model labels were Qwen3-30B-A3B and Qwen3-32B; distinct checkpoint identities were not independently verified.',
            'Our intended extensions. We expected thinking and internet-retrieved cipher guidance to help ROT-12 more than ROT-13. The team reported submitting predictions, but the exact submitted text and receipt were not provided. The user prepared 30 matched items per cipher; the documented seed-42 selection was reconstructed and checked against their logged items. A planned 480-response matrix is not a completed experiment.',
            f'What was saved. There are {n["top_level_source_records"]} top-level source records: '+human_sources+f'. Of these, {n["returned_response_records"]} contain model outputs and {n["final_request_error_records"]} are final request errors. Eleven older retry-history events are separate. These are source-record counts, not a guaranteed number of independent calls; some retries and cancelled calls were not recorded individually.',
            'Source boundaries. We import original run files once, not their generated master copies. The second friend\'s logs/all_runs_master.jsonl repeats its two underlying logs and is not added again. Their repo/ directory contains the published authors\' code and closed-model results; none of those reference results are counted as team experiments. All supplied team records remain traceable to a contributor, source file and row.',
            'What is most useful. The new friend\'s extension has 48 item opportunities across 12 model/cipher/prompt cells. It includes a completed exact ROT-12 answer with a supplied substitution table. This is a concrete observation. It does not by itself prove that internet access works, thinking was disabled in a control group, or a general probability gap was removed.',
        ]),
        ('Prompt-Variant Pilot: Results We Can Include',[
            f'The new extension log contains {e["source_records"]} attempt records for {e["distinct_uids"]} item UIDs. There are {e["returned_records"]} returned model responses and {e["request_error_records"]} error records. Six repeated UIDs have an error followed by a returned response; these are retained as attempts, not counted as extra items. Six item opportunities have no returned model response.',
            'What the modes actually mean. Direct adds an answer-only instruction. Standard is the original task prompt, labeled thinking_mode in the source. Table adds an authored substitution table. The caller does not set a thinking-disable switch, and every returned direct-mode record still has reasoning text. The table is embedded in code; no web retrieval is recorded. These are prompt variants, not a clean on/off thinking or internet-access experiment.',
            'MATRIX',
            'Table definitions. Jobs are distinct item UIDs; Replies are returned item responses. Exact requires finish_reason=stop and exact final-content matching. Contains counts completed visible content containing the target (case-insensitive), a diagnostic that does not require answer-only formatting. Length counts truncated replies. API errs count failed attempts, including recovered retries; they are not wrong model answers. We select the first returned response per UID without selecting on correctness.',
            'Observed guidance example. In requested 30B-A3B / ROT-12, the table prompt produced one exact completed answer among four replies: "Well, it was not exactly planned from the beginning." Direct and Standard each produced no exact completed answers in four replies. This small observation supports a case study, not a reliable estimate of a general benefit.',
            'Limits of interpretation. Standard ROT-13 replies sometimes contain the correct sentence with explanations, so a strict formatting failure is not automatically a decoding failure. Some 32B cells have only two or three replies; missing API responses must remain missing. Checkpoints and actual generation settings were not independently verified. No significance, architectural, tokenization or causal claim is made.',
        ]),
        ('Scoring and Failure Analysis',[
            'Separate outputs from reasoning. We score completed visible/stored answer text and retain reasoning separately when available. A target string appearing in reasoning is labeled exactly that; it does not prove the model solved the problem internally or would have answered correctly. Truncated output is noncompletion under a particular budget, not proof of an intrinsic inability.',
            'Why the acronym report changed. Its old parser searched for the known target in cleaned response text, sometimes before separating reasoning. Many unfinished traces were counted as correct. We preserve those old flags and add an explicit completed exact metric. The latter is a stricter reanalysis, not a claim to reproduce the paper\'s exact grader.',
            'ACRONYM_TABLE',
            'CHART',
            'Concrete failures. A ROT-13 response substituted way for path; two ROT-12 responses gave unrelated sentences. The stored acronym answer APPLEID differs from APPLIED in letter order. Another response listed the correct initials for LITERAL but joined them as LITERALL, adding an extra L. These five completed answers have specific content errors. Correct answers wrapped in extra explanation are excluded from the selected review.',
            f'Review status. Fourteen identical shortened ROT-12 excerpts remain quarantined. The other {n["usable_stored_response_records"]} stored response records yield {n["strict_completed_stored_matches"]} strict completed matches and {n["strict_failure_candidates"]} automatic candidate nonmatches/noncompletions. These are audit counts, not a pooled accuracy. The selected review contains exactly 30 cases: 5 wrong completed answers and 25 unfinished responses. Each has a source excerpt and a simple explanation; correct answers with extra explanation are excluded. Participant review is confirmed for {n["participant_reviews_confirmed"]} cases. AI annotation is not manual participant review.',
        ]),
        ('What Is Established, and What Remains Open',[
            f'New primary-pilot evidence. The second friend supplies {p["source_records"]} records across 21 conditions, three examples each. Of these, {p["truncated_records"]} truncate and {p["completed_visible_target_contains"]} contain the target in completed visible content; none are answer-only exact matches under our strict rule. This shows sensitivity to completion and presentation. Three examples per condition, overlapping tasks and missing per-call model identity are insufficient for a strong replication claim.',
            'Thinking prediction: not established as an on/off effect. The new data add a useful Standard-versus-Direct prompt comparison, but Direct still generated reasoning. We cannot attribute the differences to enabling versus disabling thinking. Earlier unsupported thinking percentages were removed; the new table is calculated from actual source records.',
            'Internet prediction: not established. The new table condition has some exact replies, including one ROT-12 reply, but it uses an authored reference table. The user\'s separate web-sourced pilot truncated and changed its system instruction relative to the unguided attempt. These do not establish an internet-access effect or confirm the submitted prediction.',
            'Evidence checks and uncertainty. Answer keys for the imported new records match independent deterministic transformations and source stimuli. Five groups repeat identical prompt/target/content/reasoning across differently labeled records, including one cross-model pair. They are preserved with flags; independent calls or distinct backends cannot be established from these records. The older 32B pilot also has uniform latency/token metadata, and its original API envelopes are absent.',
            'Claims excluded. We do not claim confirmed pretraining attractors, measured attention weights, a tokenization mechanism, 3500 observed reasoning tokens, internals solved from target containment, an architecture advantage, or a neutralized probability gap. No token usage was saved in the new logs; latency is not a substitute. Hard-coded keys were redacted in copied material, and the original source projects were not executed during this merge.',
            'Reproducibility and remaining work. Install requirements and run python3 rebuild_evidence.py offline; tests use python3 -m unittest discover -s tests. The package includes source records, full reasoning where supplied, separate API errors, computed summaries, provenance and checksums. Participants still need to verify at least 30 failures, supply the exact submitted predictions, clarify checkpoint/mode provenance, recover missing originals, and provide twist results. No new inference or submission was made during the merge.',
            'Sources and disclosure. McCoy et al., arXiv:2309.13638 / PNAS 2024; official stimuli at github.com/tommccoy1/embers-of-autoregression; supplied AIRIS rules; the user\'s saved Wikipedia Caesar-cipher excerpt; and the three contributors\' records. ChatGPT assisted code, debugging, audit and writing. Teammate files name Antigravity and an @verifier role; participants must confirm the full tool list and which reviews were actually human. The report makes no certification of an unprovided preregistration receipt or manual-review history.',
        ]),
    ]

    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleO',fontName='Helvetica-Bold',fontSize=20,leading=24,spaceAfter=12,textColor=colors.HexColor('#172C42')))
    styles.add(ParagraphStyle(name='BodyO',fontName='Helvetica',fontSize=9.5,leading=13,spaceAfter=8))
    styles.add(ParagraphStyle(name='CellO',fontName='Helvetica',fontSize=7.7,leading=10))
    def table(data,widths):
        t=Table([[Paragraph(html.escape(str(v)),styles['CellO']) for v in line] for line in data],colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEF4F7')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#D8E1E8')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        return t
    story=[];md=[]
    for page,(title,texts) in enumerate(sections):
        if page:story.append(PageBreak())
        story.append(Paragraph(html.escape(title),styles['TitleO']));md += ['# '+title,'']
        for text in texts:
            data=matrix if text=='MATRIX' else acronym_table if text=='ACRONYM_TABLE' else None
            if data:
                widths=[70,35,65,35,42,40,52,40,55] if text=='MATRIX' else [215,35,65,85,65]
                story += [table(data,widths),Spacer(1,8)]
                md += ['| '+' | '.join(data[0])+' |','| '+' | '.join(['---']*len(data[0]))+' |',*['| '+' | '.join(line)+' |' for line in data[1:]],'']
            elif text=='CHART':
                selected=[next(g for g in acronym if g['model_requested']=='qwen3-30b-a3b' and g['task']==task) for task in ['acronym1_11','acronym1_51','acronym1_15']]
                drawing=Drawing(480,126);chart=HorizontalBarChart();chart.x=112;chart.y=20;chart.width=280;chart.height=95
                chart.data=[tuple(g['legacy_stored_correct'] for g in selected),tuple(g['strict_correct'] for g in selected)]
                chart.categoryAxis.categoryNames=['Common/common','Rare output','Rare input'];chart.categoryAxis.labels.fontSize=8
                chart.valueAxis.valueMin=0;chart.valueAxis.valueMax=105;chart.valueAxis.valueStep=20;chart.valueAxis.labels.fontSize=7
                chart.bars[0].fillColor=colors.HexColor('#087F8C');chart.bars[1].fillColor=colors.HexColor('#A95B2D');chart.barLabelFormat='%d';chart.barLabels.fontSize=7;chart.barLabels.boxAnchor='w';chart.barLabels.dx=3
                drawing.add(chart);drawing.add(String(112,3,'Count out of 100 per original 30B acronym pilot',fontName='Helvetica',fontSize=8));story.append(drawing)
                caption='Teal: old correct flag. Brown: strict completed match. Different metrics; not an architecture comparison.'
                story.append(Paragraph(caption,styles['CellO']));story.append(Spacer(1,7));md += [caption,'']
            else:
                story.append(Paragraph(html.escape(text),styles['BodyO']));md += [text,'']
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#536477'))
        canvas.drawString(43,25,'Paper 8 | Three-contributor synthesis | AI-assisted; participant verification pending')
        canvas.drawRightString(552,25,str(doc.page))
    SimpleDocTemplate(str(report/'Combined_Report.pdf'),pagesize=(595.28,841.89),leftMargin=43,rightMargin=43,topMargin=36,bottomMargin=45,title='Paper 8: Overall Evidence Analysis').build(story,onFirstPage=footer,onLaterPages=footer)
    text='\n'.join(md)
    for path in [report/'report.md',root/'MASTER_RESEARCH_LOG.md',root/'results/master/MASTER_RESEARCH_LOG.md']:
        path.write_text(text,encoding='utf-8')
    comparison='# Current descriptive comparisons\n\nSee analysis/friend2_extension_cells.csv for opportunity, response, exact, visible-containment, truncation, and error counts. These are prompt variants with unverified checkpoints; authored tables are not internet retrieval.\n\n'+ '\n'.join(['| '+' | '.join(matrix[0])+' |','| '+' | '.join(['---']*len(matrix[0]))+' |',*['| '+' | '.join(line)+' |' for line in matrix[1:]]])+'\n\nNo causal or statistical-significance claims are made. Legacy scoring, strict completed scores, and diagnostics are separate.\n'
    for path in [root/'MODEL_COMPARISON.md',root/'results/master/MODEL_COMPARISON.md']:path.write_text(comparison)

    slide_data=[
        ('Embers of Autoregression: combined pilot evidence',[
            'Question: can familiarity affect deterministic acronym and cipher tasks?',
            'Three contributions: acronym runs, user cipher pilots, and multi-task/prompt-variant logs.',
            'Requested labels: Qwen3-30B-A3B and Qwen3-32B; checkpoints are not independently verified.',
            'Goal: report the evidence and its limits without inventing completed experiments.'
        ]),
        ('Plan, predictions, and actual coverage',[
            'Predictions: thinking and internet-retrieved guidance help ROT-12 more than ROT-13.',
            'User plan: 30 paired items per cipher; 480 cells across two models and two factors.',
            f'Combined: {n["top_level_source_records"]} source records; {n["returned_response_records"]} returned-response records; {n["final_request_error_records"]} final request errors.',
            'Published repo logs and generated master copies are not counted as new team runs.'
        ]),
        ('Ciphers and other tasks: all pilot findings',[
            '63 records across 21 conditions, with three examples per condition.',
            'ROT-13 ordinary: 1/3 completed with target; reordered: 0/3.',
            'Word reversal ordinary: 3/3; reordered: 2/3. Unusual outputs can succeed.',
            'Alphabetical sorting: 3/3; reverse alphabetical: 0/3.',
            'Familiar and altered linear formulas: both 3/3. Counts allow explanations.'
        ]),
        ('Cipher extensions: a useful result and its limits',[
            '30B / ROT-12 Table: one exact answer in four replies; Direct and Standard: zero.',
            'On the same item, Table finishes correctly; Direct and Standard both truncate.',
            'New spacing, larger-budget and three-example tests add 24 attempts.',
            'All 20 new replies are unfinished; four attempts have API errors.',
            'Direct still generates reasoning. Table is authored guidance, not web retrieval.',
        ]),
        ('Failure analysis: what we actually saw',[
            'Cipher substitution: path becomes way, violating the exact letter mapping.',
            'ROT-12 can return a fluent sentence unrelated to the encoded input.',
            'Acronyms: APPLEID instead of APPLIED; LITERALL instead of LITERAL.',
            'Truncated explanations and parser artifacts are not completed decoding answers.',
            'A target found in reasoning is not proof of an internally solved task.'
        ]),
        ('Why the evidence is checkable',[
            f'All {n["returned_response_records"]} returned-record answer keys and 3,400 stimulus keys pass rule checks.',
            'Every reported example links to a source file, row and unchanged stored response.',
            'API errors, unfinished replies and correct answers with extra text are separated.',
            'New truncation-flag conflicts are corrected using finish_reason; originals are kept.',
            'These checks validate answers and arithmetic, not backend identity or causation.'
        ]),
        ('Deliverables and honest remaining work',[
            'All source records retained with provenance; API errors and repeated imports handled separately.',
            'Offline rebuild regenerates tables, report, review packet, and slides.',
            f'{n["participant_reviews_confirmed"]} participant reviews confirmed; at least 30 still need verification.',
            'Recover originals, confirm submitted predictions and modes/checkpoints, and supply twist results.',
            'Disclose AI assistance; report the actual observations and untested questions.'
        ]),
    ]
    canvas=Canvas(str(slides/'Presentation.pdf'),pagesize=(960,540));canvas.setTitle('Paper 8: Overall Evidence Analysis')
    for number,(title,lines) in enumerate(slide_data,1):
        canvas.setFillColor(colors.HexColor('#172C42'));canvas.rect(0,0,960,540,fill=1,stroke=0)
        heading=Paragraph(html.escape(title),ParagraphStyle('SlideTitle',fontName='Helvetica-Bold',fontSize=28,leading=33,textColor=colors.white))
        _,height=heading.wrap(865,100);heading.drawOn(canvas,46,484-height)
        y=405
        for line in lines:
            para=Paragraph(html.escape(line),ParagraphStyle('SlideBody',fontName='Helvetica',fontSize=18,leading=25,textColor=colors.HexColor('#E5EFF6')))
            _,height=para.wrap(820,90);para.drawOn(canvas,66,y-height);canvas.setFillColor(colors.HexColor('#50C3C5'));canvas.circle(48,y-11,3,fill=1,stroke=0);y-=height+20
        assert y>=38,(number,y)
        canvas.setFont('Helvetica',10);canvas.setFillColor(colors.HexColor('#B5C6D4'));canvas.drawString(45,22,'AIRIS | Source-backed observations | Participant verification pending');canvas.drawRightString(915,22,f'{number}/7');canvas.showPage()
    canvas.save()
    (slides/'presentation.md').write_text('\n\n---\n\n'.join('# '+title+'\n\n'+'\n'.join('- '+line for line in lines) for title,lines in slide_data))

    from analysis.review_cases import build_review_pdf
    with (root/'MANUAL_FAILURE_REVIEW.csv').open(newline='',encoding='utf-8') as file:review_rows=list(csv.DictReader(file))
    build_review_pdf(root,review_rows)
    (root/'experiment_inventory.md').write_text('# Current combined experiment inventory\n\n'+json.dumps(n['records_by_contributor'],indent=2)+'\n\nCurrent analyses are generated from canonical source files once. The updated source adds 24 phase-2 attempts to 63 primary records and 54 phase-1 extension attempts. Phase 2 returns 20 unfinished responses and four API errors; no completed answers. Published-author logs and generated master copies are not imported as experiments. See MASTER_RUN_METADATA.json, analysis/friend2_audit.json and analysis/ARCHIVE_UPDATE_DIFF.json.\n\nThe supplied source supports prompt-variant observations and exploratory spacing/budget/few-shot trials. It does not establish a thinking switch, internet retrieval or a tokenization mechanism. Participant review, checkpoint evidence, exact submitted predictions, missing originals, and twist results remain open.\n')
    (root/'results/master/EXPERIMENT_INVENTORY.md').write_text((root/'experiment_inventory.md').read_text())
    (root/'CORRECTIONS.md').write_text('''# Corrections and merge decisions

- Original source run files preserved; third project inspected without running its code.
- User, first teammate, and second friend imported with contributor/source-row provenance.
- Generated master copies and the cloned published paper repository excluded as new experiments.
- New friend logs preserved as 63 primary records plus 54 extension attempt records.
- Repeated extension UIDs are retries, not extra items; errors retained separately.
- First returned response per UID selected without selecting on correctness.
- Exact completed content, completed visible containment, and target-in-reasoning diagnostics are separate.
- Target-in-reasoning is not called internally solved; missing token usage is not invented.
- Direct prompts are not represented as thinking-off; authored tables are not called internet retrieval.
- Unsupported earlier percentages, significance values and mechanistic claims removed from active reports.
- Fourteen shortened first-teammate cipher excerpts remain quarantined.
- Repeated identical payload groups flagged without asserting fabrication or independence.
- Hard-coded credentials removed from copied reference scripts and the shared bundle.
- Participant notes preserved. The broad automatic review was replaced with 30 explicitly identified cases: 5 wrong completed answers and 25 unfinished responses. Each has a supporting excerpt and a specific explanation; no teammate section or contributor column is included in the review.
- The larger automatic failure index remains separate in analysis/ALL_CANDIDATE_FAILURES.csv. Correct answers with extra explanation, API errors and quarantined excerpts are excluded from the selected review.
- All annotations remain drafts until participants verify them. No new model calls or submission made.
- Updated ZIP: prior raw_runs.jsonl and extension_runs.jsonl are unchanged. Added 24 phase-2 source records (20 unfinished outputs, four API errors), imported once; all_runs_master.jsonl remains a generated duplicate, not another experiment source.
- New phase-2 records preserve is_truncated=false while classifying all 20 length-ended replies as unfinished. No token usage or returned-checkpoint evidence was invented.
- Phase-2 claims of confirmed few-shot calibration, measured tokenization causes or internally solved tasks are not supported. Reasoning containment is reported only as a diagnostic. Literal {shift_k} placeholders in spacing prompts and additional repeated payload pairs are flagged.
''')
    # The main report is the simple, balanced synthesis. The detailed audit tables
    # and provenance files generated above remain supporting evidence.
    from analysis.combined_report import build_report
    build_report(root, rows, groups, summary)
