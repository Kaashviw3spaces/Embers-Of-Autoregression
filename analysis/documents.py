"""Generate every active narrative from the same audited evidence summary."""
from pathlib import Path
import html
import json
import shutil
import csv


def build_documents(root, rows, groups, summary):
    if summary.get('friend2_prompt_variant_evidence',{}).get('available'):
        from analysis.overall_documents import build_overall
        return build_overall(root,rows,groups,summary)
    report = root / 'report'
    slides = root / 'slides'
    report.mkdir(exist_ok=True); slides.mkdir(exist_ok=True)
    primary = [g for g in groups if g['contributor']=='teammate' and g['run_kind']=='pilot' and 'acronym' in g['task']]
    n = summary
    table_rows = [['Requested model / task', 'N', 'Legacy flag', 'Strict completed', 'Truncated']]
    for g in sorted(primary,key=lambda g:(g['model_requested'],g['task'])):
        table_rows.append([g['model_requested']+' / '+g['task'],str(g['strict_denominator']),str(g['legacy_stored_correct']),str(g['strict_correct']),str(g['truncated'])])
    paragraphs = [
        ('Paper 8: Acronyms and Shift Ciphers', [
            'AIRIS Research Hackathon | Combined evidence report | 23 November 2026',
            'Status: incomplete reproduction and extension evaluation. This report combines supplied teammate run files with the user\'s saved cipher pilots. It describes stored evidence and does not claim verified checkpoint identities, completed extension tests, or participant manual review that has not been recorded.',
            'The paper claim. Embers of Autoregression predicts that model performance on deterministic tasks can depend on how common the task, input, or correct output is. We investigated acronym formation and Caesar shift-cipher decoding. The requested open models were Qwen3-30B-A3B and Qwen3-32B.',
            'Teammate reproduction. The acronym task joins the first letters of seven words. Three official conditions compare common targets/common inputs (acronym1_11), rare targets/common inputs (acronym1_51), and common targets/rare inputs (acronym1_15). A second requested model has a smaller pilot. These are related tests of the paper\'s probability claims, not the same task as the user\'s cipher pilot.',
            'User reproduction and extensions. Thirty paired sentences were prepared in ROT-13 and ROT-12, giving 60 test items. We expected thinking and fixed web-retrieved cipher guidance to improve ROT-12 more than ROT-13. A full two-model, two-thinking-state, two-guidance-state plan would require 480 responses. That full plan was not completed.',
            'Prediction record. The team reported submitting its predictions. The exact submitted text and receipt were not supplied with these files. The expectations above summarize the plan; this report does not certify a preregistration timestamp.',
            'Setup. Work used Python and a shared open-model API. The user\'s logged calls used temperature 0.6, top_p 0.95, and output limits of 1024 or 4096. Legacy code used other defaults, and many legacy request settings are not preserved per call. A saved Wikipedia explanation was provided as guidance in one returned user pilot; this was fixed retrieved context, not live model browsing.',
        ]),
        ('Observed results and scoring', [
            f'The combined evidence contains {n["top_level_source_records"]} top-level records: {n["records_by_contributor"]["teammate"]} from teammate run files and {n["records_by_contributor"]["user"]} from user logs. There are {n["returned_response_records"]} returned-response records, {n["final_request_error_records"]} final request-error records, and {n["retry_history_events"]} separately logged legacy retry events. These are not a guaranteed count of every network attempt; earlier unsaved terminal calls and cancelled requests may be absent.',
            'Source copies are not new runs. Root MASTER files, results/master files, and per-run export packages contain copies of source material. The rebuild imports canonical source runs once and preserves source paths and row numbers. Repeated calls to the same item are retained when they represent different attempts.',
            'Strict metric. A stored response is correct only when finish_reason is stop and the returned answer matches the expected text after trimming surrounding whitespace. A separate normalized metric permits limited quotes, code fences, and simple acronym separators. Neither is claimed to reproduce the paper\'s exact scoring. Correct-looking reasoning from a truncated response is not a completed answer.',
            f'Fourteen identical shortened ROT-12 outputs are quarantined. Across the remaining {n["usable_stored_response_records"]} stored response records, strict rescoring yields {n["strict_completed_stored_matches"]} completed matches and {n["strict_failure_candidates"]} nonmatches or incomplete outputs. These totals combine different tasks and settings, so they are audit counts, not a pooled benchmark accuracy.',
            'Legacy-score sensitivity. The legacy acronym parser searched for the known target anywhere in cleaned response text, before separating reasoning. It could also substitute reasoning when final content was empty. This makes its high stored scores different from completed-answer scores. The table below shows both rules without treating either as a causal model comparison.',
            'TABLE',
            'Matched IDs. On the stored legacy flags for acronym1_11 IDs 0 through 32, the requested 30B model has 30/33 correct and the requested 32B model has 32/33. The previous equal-score statement and hard-coded significance claims were removed. Model identity, source provenance, and differing completion behavior prevent an architecture conclusion.',
        ]),
        ('Failure analysis grounded in actual outputs', [
            f'The corrected review queue contains {n["strict_failure_candidates"]} eligible cases under the explicitly revised completed-answer rule. This is a reanalysis of existing outputs, not new model runs. Many cases are truncations that the permissive legacy rule counted as correct. Participant review is currently confirmed for {n["participant_reviews_confirmed"]} cases; creating or AI-annotating a queue does not satisfy the by-hand requirement.',
            'Truncated decoding. Two user ROT-13 pilots repeatedly decoded early words and exhausted 1024 output tokens without completing the sentence. One had web guidance. This shows noncompletion under the chosen budget; it does not show that the model cannot decode the sentence with a larger budget.',
            'Incorrect ROT-12 answer. A completed user response returned "How would you like them done in a little while?" instead of "But this time, there may also be another reason." Its stated shift rule was correct, but its shown letter mapping and final sentence were wrong. A second ROT-12 response returned another unrelated sentence.',
            'Synonym substitution. A user ROT-13 response changed "their own path" to "their own way". Ciphertext cngu decodes exactly to path. This preserves meaning while violating the exact transformation. It is compatible with paraphrasing or regularization, but no measured output probabilities establish a cause.',
            'Parser artifacts. A legacy raw response ends while quoting "comcast entitle"; its parsed value is ENTITLE. This is not evidence that the model deliberately chose that word as its final acronym. Other smoke outputs contain the correct acronym but store PUNCTUATION as the parsed prediction. These require parser-aware annotations.',
            'Letter order. One stored completed acronym output is APPLEID rather than APPLIED. A different truncated text repeatedly combines letters as DEPOSTI rather than DEPOSIT. Describe the visible ordering errors; attention weights, token attractors, and specific Apple-ID associations were not measured.',
            'Correct answers are retained. The user\'s ROT-13_4 response exactly matches "I will not give up even for a moment." The combined master also retains every legacy stored success and its rescored result, including disagreements between metrics. We did not select only failures.',
            'Evidence quality. All fourteen teammate ROT-12 rows store the same text, "Okay, let\'s see. I need t...". They cannot support detailed independent decoding analysis without full originals. The 33-row legacy 32B pilot has uniform latency and token fields and no original API response IDs; its provenance still needs clarification. These observations do not establish fabrication or intent.',
        ]),
        ('Limitations, corrections, and reproducibility', [
            'What the evidence establishes. It documents variable completion behavior, extraction/scoring sensitivity, and concrete incorrect or paraphrased outputs on deterministic tasks. It does not establish the paper\'s probability effect in a controlled two-checkpoint reproduction. A small difference between legacy acronym conditions cannot show that instruction tuning removed a probability bias.',
            'Thinking extension: not established. No matched, verified thinking-on/off run set was supplied. Requested switches and visible explanations do not independently confirm the effective model mode.',
            'Guidance extension: not established. The user has one returned guided pilot and an unguided pilot with a different system instruction. Both truncate. Teammate reasoning/retrieval percentages in earlier documents were literal report text without supporting run files and have been removed from active outputs.',
            'Infrastructure. Request throttling, authentication failures, resets, and timeouts are kept separate from model-answer errors. The logs do not establish the exact reason request slots remained occupied. We make no claim that all retries resolved, all responses completed, or all latencies and token counts were measured correctly in old exports.',
            'Remaining requirements. Participants must read at least 30 real failure responses and complete the review fields with their names and observations. The original user pilot file, full teammate cipher outputs, checkpoint/mode verification, and surprise-twist results remain missing. These limitations are stated openly; the supplied brief permits an honest incomplete reproduction, but unmet requirements may affect evaluation.',
            'Rebuild. After installing requirements, run python3 rebuild_evidence.py from this directory. It makes no API calls and regenerates master CSV/JSONL files, review queues, this report, and seven slides. Run python3 -m unittest discover -s tests to check scoring and provenance behavior. Live generation is separate, sequential, dry-run by default, and requires --live plus a shared-server URL.',
            'Sources. McCoy et al., Embers of Autoregression, arXiv:2309.13638 and PNAS 2024; official prompts/stimuli at github.com/tommccoy1/embers-of-autoregression; saved guidance from en.wikipedia.org/wiki/Caesar_cipher; AIRIS Research Hackathon Problem Statements, supplied PDF. The arXiv preprint and published paper differ, so numerical baselines must identify the version.',
            'Disclosure. ChatGPT assisted planning, scripts, debugging, log inspection, annotations, corrections, reports, and slides. The teammate documents identify Antigravity assistance; participants should confirm that tool list. Experimental responses came from supplied shared-server records, not paid-model answers. All current annotations are AI-assisted drafts pending participant verification. Predictions are team-reported, not independently verified here.',
        ]),
    ]
    md=[]
    for title, texts in paragraphs:
        md.append('# '+title+'\n')
        for text in texts:
            if text=='TABLE':
                md += ['| '+' | '.join(table_rows[0])+' |', '| '+' | '.join(['---']*5)+' |']
                md += ['| '+' | '.join(r)+' |' for r in table_rows[1:]]
                md.append('')
            else:md.append(text+'\n')
    report_text='\n'.join(md)
    (report/'report.md').write_text(report_text,encoding='utf-8')
    (root/'MASTER_RESEARCH_LOG.md').write_text(report_text,encoding='utf-8')
    (root/'results/master/MASTER_RESEARCH_LOG.md').write_text(report_text,encoding='utf-8')
    comparison=['# Descriptive comparison of supplied evidence\n','Different source runs and metrics are kept separate. Checkpoint and effective-thinking verification remain unresolved. No unsupported significance tests or intervention numbers are generated.\n']
    comparison += ['| '+' | '.join(table_rows[0])+' |','| '+' | '.join(['---']*5)+' |']
    comparison += ['| '+' | '.join(r)+' |' for r in table_rows[1:]]
    comparison += ['\nThe table counts stored legacy correct flags and a stricter completed exact-answer rule. Neither licenses an architecture or training-mechanism claim. See analysis/run_summary.csv for all source groups and denominators.','\nMatched stored flags for IDs 0..32: '+json.dumps(summary['matched_stored_flags'])]
    for path in [root/'MODEL_COMPARISON.md',root/'results/master/MODEL_COMPARISON.md']:
        path.write_text('\n'.join(comparison),encoding='utf-8')
    inventory='''# Current experiment inventory

Source runs: ten legacy JSON files in runs/, plus the contributed user JSONL files in evidence/user/redacted/. Generated master copies are not extra runs.

Prepared: three 1000-item acronym sets and four 100-item cipher sets. All answer keys pass deterministic checks. User prepared 60 selected cipher items locally; that full selected file has not been supplied.

Observed: legacy acronym smoke/pilot outputs; fourteen quarantined identical cipher excerpts; five legacy cipher API errors; user cipher pilots and collection attempts. See MASTER_RUN_METADATA.json for current computed counts.

Not established: a verified two-checkpoint reproduction, matched thinking and guidance extension results, or the surprise twist. Human review remains pending until participants fill the review sheet.

Every active table is generated by rebuild_evidence.py. Historical reports are preserved in evidence/legacy_generated/ and an external backup; they contain superseded claims and are not current results.
'''
    (root/'experiment_inventory.md').write_text(inventory)
    (root/'results/master/EXPERIMENT_INVENTORY.md').write_text(inventory)

    slide_data=[
        ('Embers of Autoregression: what we tested',[
            'Two task families: acronym formation and ROT-13 / ROT-12 decoding.',
            'Question: does familiarity affect a deterministic transformation?',
            'Requested models: Qwen3-30B-A3B and Qwen3-32B; checkpoint identities remain unverified.',
            'This is an incomplete reproduction with an evidence-based failure analysis.'
        ]),
        ('Plan and predictions',[
            'Acronyms: compare common/rare target words and common/rare input words.',
            'Ciphers: prepare 30 matched sentences per shift; 60 items total.',
            'Prediction: thinking improves ROT-12 more than ROT-13.',
            'Prediction: fixed web-retrieved guidance improves ROT-12 more than ROT-13.',
            'Full cipher plan: 480 responses. The controlled matrix was not completed.'
        ]),
        ('What was actually saved',[
            f'{n["top_level_source_records"]} top-level source records; not all network attempts.',
            f'{n["returned_response_records"]} returned-response records and {n["final_request_error_records"]} final request errors.',
            f'{n["retry_history_events"]} additional legacy retry-history events recorded separately.',
            f'{n["quarantined_excerpt_records"]} identical shortened cipher outputs are quarantined.',
            'Root and results/master copies count once. Correct answers and technical failures are preserved.'
        ]),
        ('Scoring changed the interpretation',[
            'Legacy parser: target found anywhere in cleaned text can count as correct.',
            'Revised strict metric: completed stored answer must equal the target.',
            'Truncated reasoning is not a completed final answer; a normalized score is secondary.',
            'Metrics are disclosed separately. No pooled architecture comparison is claimed.'
        ]),
        ('Failure examples we can show',[
            'ROT-13: path becomes way. Meaning is similar; the deterministic rule is violated.',
            'ROT-12: a completed answer gives an unrelated fluent sentence.',
            'Acronym: APPLEID instead of APPLIED is a letter-order mismatch in stored output.',
            'Some parsed words come from truncated prompt quotations rather than a final answer.',
            'Repeated explanation can exhaust the output budget without completing the task.'
        ]),
        ('What the extensions do not yet establish',[
            'No matched, verified thinking-on/off result set was supplied.',
            'One guided user pilot also changes its system instruction and truncates.',
            'Earlier teammate intervention percentages lacked supporting run logs and were removed.',
            'Throttling, connection errors, uncertain model labels, and missing originals limit inference.',
            'We cannot claim thinking or retrieval reduced the probability gap.'
        ]),
        ('Takeaways and remaining work',[
            'Completion and scoring choices strongly affect how these logs are described.',
            'Observed decoding errors support case studies, not a measured internal mechanism.',
            f'{n["participant_reviews_confirmed"]} participant reviews currently confirmed; at least 30 are required.',
            'Next: verify checkpoints/modes, recover originals, complete the controlled matrix and twist.',
            'Disclose AI assistance. An honest incomplete reproduction is more defensible than unsupported numbers.'
        ]),
    ]
    (slides/'presentation.md').write_text('\n\n---\n\n'.join('# '+title+'\n\n'+'\n'.join('- '+s for s in lines) for title,lines in slide_data))

    # PDF creation uses a standard document library; no server/browser is needed.
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleR',fontName='Helvetica-Bold',fontSize=20,leading=24,spaceAfter=12,textColor=colors.HexColor('#172C42')))
    styles.add(ParagraphStyle(name='BodyR',fontName='Helvetica',fontSize=9.7,leading=13.4,spaceAfter=8))
    styles.add(ParagraphStyle(name='CellR',fontName='Helvetica',fontSize=8,leading=10))
    story=[]
    for i,(title,texts) in enumerate(paragraphs):
        if i:story.append(PageBreak())
        story.append(Paragraph(html.escape(title),styles['TitleR']))
        for text in texts:
            if text=='TABLE':
                t=Table([[Paragraph(html.escape(c),styles['CellR']) for c in row] for row in table_rows],colWidths=[210,35,70,85,68])
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEF4F7')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#D8E1E8')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
                story += [t,Spacer(1,8)]
                from reportlab.graphics.shapes import Drawing, String
                from reportlab.graphics.charts.barcharts import HorizontalBarChart
                chart_groups=[next(g for g in primary if g['model_requested']=='qwen3-30b-a3b' and g['task']==task) for task in ['acronym1_11','acronym1_51','acronym1_15']]
                drawing=Drawing(490,145)
                chart=HorizontalBarChart();chart.x=112;chart.y=23;chart.width=290;chart.height=106
                chart.data=[tuple(g['legacy_stored_correct'] for g in chart_groups),tuple(g['strict_correct'] for g in chart_groups)]
                chart.categoryAxis.categoryNames=['Common/common','Rare output','Rare input'];chart.categoryAxis.labels.fontSize=8
                chart.valueAxis.valueMin=0;chart.valueAxis.valueMax=105;chart.valueAxis.valueStep=20;chart.valueAxis.labels.fontSize=7
                chart.bars[0].fillColor=colors.HexColor('#087F8C');chart.bars[1].fillColor=colors.HexColor('#A95B2D')
                chart.barLabelFormat='%d';chart.barLabels.fontSize=7;chart.barLabels.dx=3;chart.barLabels.boxAnchor='w'
                drawing.add(chart)
                drawing.add(String(112,5,'Count out of 100 per 30B pilot condition',fontName='Helvetica',fontSize=8))
                story.append(drawing)
                story.append(Paragraph('Teal: legacy flag. Brown: strict completed match. These are different scoring rules, not a controlled architecture comparison.',styles['CellR']))
            else:story.append(Paragraph(html.escape(text),styles['BodyR']))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#536477'))
        canvas.drawString(43,25,'Paper 8 | Corrected combined evidence | AI-assisted; participant verification pending')
        canvas.drawRightString(552,25,str(doc.page))
    SimpleDocTemplate(str(report/'Combined_Report.pdf'),pagesize=(595.28,841.89),leftMargin=43,rightMargin=43,topMargin=36,bottomMargin=45,title='Paper 8: Corrected Combined Evidence Report').build(story,onFirstPage=footer,onLaterPages=footer)

    from reportlab.pdfgen.canvas import Canvas
    canvas=Canvas(str(slides/'Presentation.pdf'),pagesize=(960,540))
    canvas.setTitle('Paper 8: Corrected Combined Evidence')
    for number,(title,lines) in enumerate(slide_data,1):
        canvas.setFillColor(colors.HexColor('#172C42'));canvas.rect(0,0,960,540,fill=1,stroke=0)
        heading=Paragraph(html.escape(title),ParagraphStyle('heading',fontName='Helvetica-Bold',fontSize=29,leading=34,textColor=colors.white))
        w,height=heading.wrap(865,100);heading.drawOn(canvas,46,484-height)
        y=405
        for line in lines:
            para=Paragraph(html.escape(line),ParagraphStyle('line',fontName='Helvetica',fontSize=18,leading=25,textColor=colors.HexColor('#E5EFF6')))
            w,height=para.wrap(820,90);para.drawOn(canvas,66,y-height)
            canvas.setFillColor(colors.HexColor('#50C3C5'));canvas.circle(48,y-11,3,fill=1,stroke=0)
            y-=height+20
        canvas.setFont('Helvetica',10);canvas.setFillColor(colors.HexColor('#B5C6D4'))
        canvas.drawString(45,22,'AIRIS | Source-backed reanalysis | Pending participant review')
        canvas.drawRightString(915,22,f'{number} / 7');canvas.showPage()
    canvas.save()

    # A separate supplement makes the full first 30 records easier to read.
    # It is not part of the four-page report and is never counted as human review.
    with (root/'analysis/REVIEW_FIRST_30.csv').open(newline='',encoding='utf-8') as file:
        review_items=list(csv.DictReader(file))
    packet=[]
    for number,row in enumerate(review_items,1):
        if number>1:packet.append(PageBreak())
        packet.append(Paragraph(f'Review candidate {number} of {len(review_items)}',styles['TitleR']))
        for label,value in [('Record ID',row['record_id']),('Source',row['source_file']),('Item / requested model',row['item_id']+' / '+row['model_requested']),('Source quality',row['source_quality']),('Finish reason',row['finish_reason']),('Expected answer',row['expected']),('AI draft category',row['category']),('AI draft note',row['draft_notes'])]:
            packet.append(Paragraph(html.escape(label+': '+value),styles['BodyR']))
        packet.append(Paragraph('Full stored model text follows, with line breaks compacted for reading. Original formatting remains in the source log and CSV. Read it before verifying the annotation.',styles['BodyR']))
        packet.append(Paragraph(html.escape(' '.join(row['raw_text'].split())),ParagraphStyle('ReviewRaw',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=8)))
    if packet:
        SimpleDocTemplate(str(report/'Review_Packet_30.pdf'),pagesize=(595.28,841.89),leftMargin=43,rightMargin=43,topMargin=36,bottomMargin=45,title='Thirty review candidates: full stored responses, not completed human review').build(packet,onFirstPage=footer,onLaterPages=footer)

    ledger='''# Corrections applied

- Original project backed up externally; original run JSON files preserved.
- Imported both contributors' supplied records without counting generated copies twice.
- Replaced unsupported cipher/intervention results and significance claims with source-based status.
- Quarantined fourteen identical shortened ROT-12 outputs.
- Kept legacy scores alongside explicit strict and normalized completion-aware scores.
- Removed answer-key-aware parsing and reasoning-to-final substitution from the live runner.
- Corrected matched stored outcomes to 30/33 versus 32/33; no causal or significance claim.
- Removed invented input/output token splits and assembly timestamps presented as request times.
- Preserved API errors and retry events separately from model-answer outcomes.
- Rebuilt review queues with AI/deterministic draft labels and preserved participant note fields.
- Made live requests opt-in, sequential, and nonretrying on connection/rate-limit errors.
- Generated four-page report and seven-slide PDF from shared computed evidence.
- Added a separate full-text review packet for the first 30 eligible candidates;
  its existence is not participant verification and it is not part of the report.

Still unresolved: participant review, exact prediction receipt, original user pilot file,
full teammate cipher outputs, checkpoint/mode verification, and twist results.
'''
    (root/'CORRECTIONS.md').write_text(ledger)
