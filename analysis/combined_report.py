"""Simple four-page synthesis, grounded in all three supplied experiment sets."""
from collections import defaultdict
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo
import csv


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def primary_findings(rows):
    groups = defaultdict(list)
    for row in rows:
        if row['run_kind'] == 'friend2_primary':
            groups[(row['task'], row['intervention'])].append(row)
    result = []
    for (task, condition), items in sorted(groups.items()):
        result.append({
            'task': task, 'condition': condition, 'records': len(items),
            'completed_with_target': sum(r['completed_visible_target_contains'] is True for r in items),
            'strict_exact': sum(r['strict_correct'] is True for r in items),
            'unfinished': sum(r['finish_reason'] == 'length' for r in items),
            'source_file': items[0]['source_file'],
            'source_rows': ','.join(str(r['source_record']) for r in items),
            'record_ids': ','.join(r['record_id'] for r in items),
            'meaning': 'Completed visible text contains the target; extra explanation is allowed. Diagnostic, not paper accuracy or answer-only accuracy.',
        })
    return result


def build_report(root, rows, groups, summary):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.graphics.shapes import Drawing, String, Rect
    from analysis.review_cases import curated_reviews

    primary = primary_findings(rows)
    lookup = {r['condition']: r for r in primary}
    checks = sum(not r['api_error'] and r['oracle_matches_expected'] for r in rows)
    assert len(primary) == 21 and sum(r['records'] for r in primary) == 63
    wrong = [r for r in curated_reviews(rows) if r['review_group'] == 'Wrong completed answer']
    write_csv(root/'analysis/COMBINED_PRIMARY_FINDINGS.csv', primary)
    write_csv(root/'analysis/KEY_ERROR_EVIDENCE.csv', [{
        'example': f'F{i}', 'category': r['category'], 'task': r['task'],
        'expected': r['expected'], 'observed': r['observed_answer'],
        'explanation': r['draft_notes'], 'finish_reason': r['finish_reason'],
        'record_id': r['record_id'], 'source_file': r['source_file'], 'source_row': r['source_record'],
        'verification': 'AI-assisted comparison with independently computed answer; not participant manual review',
    } for i, r in enumerate(wrong, 1)])
    index = []
    for row in rows:
        if row['run_kind'] in {'friend2_primary', 'friend2_extension','friend2_phase2'} or row['record_id'] in {r['record_id'] for r in wrong}:
            index.append({'record_id': row['record_id'], 'report_section': 'Multi-task pilot' if row['run_kind']=='friend2_primary' else 'Prompt extensions' if row['run_kind']=='friend2_extension' else 'New spacing/budget/few-shot tests' if row['run_kind']=='friend2_phase2' else 'Completed error example',
                          'task': row['task'], 'condition': row['intervention'], 'source_file': row['source_file'], 'source_row': row['source_record'],
                          'finish_reason': row['finish_reason'], 'strict_exact': row['strict_correct'],
                          'completed_with_target': row['completed_visible_target_contains'], 'api_error': bool(row['api_error'])})
    write_csv(root/'analysis/REPORT_EVIDENCE_INDEX.csv', index)

    def rate(condition):
        r = lookup[condition]
        return f"{r['completed_with_target']}/{r['records']}"

    overview = [['Experiment set', 'Rows', 'Replies', 'Errors', 'What it adds']]
    families = [
        ('Acronym + early cipher runs', lambda r: r['contributor']=='teammate' and r['run_kind']!='expanded_smoke', 'Acronym frequency conditions; early cipher records'),
        ('Additional cipher attempts', lambda r: r['contributor'] in {'user','new_live'}, 'Completed ROT-12/13 errors, one success, and setup failures'),
        ('Multi-task pilot', lambda r: r['run_kind']=='friend2_primary', '21 conditions: ciphers, sorting, reversal, functions, articles'),
        ('Cipher prompt extensions', lambda r: r['run_kind']=='friend2_extension', 'Two requested models; Direct, Standard and Table prompts'),
        ('New spacing / budget / examples', lambda r: r['run_kind']=='friend2_phase2', 'Character spacing, budget labeled 4096, and three examples'),
        ('Final short-budget campaign', lambda r: r['run_kind']=='expanded_smoke', 'Counting and additional reversal, sorting, swapping, arithmetic and Pig Latin checks'),
    ]
    for title, predicate, detail in families:
        selected = [r for r in rows if predicate(r)]
        overview.append([title, str(len(selected)), str(sum(not bool(r['api_error']) for r in selected)), str(sum(bool(r['api_error']) for r in selected)), detail])
    assert sum(int(r[1]) for r in overview[1:]) == len(rows)

    multi = [['Test family', 'Completed replies containing the expected answer', 'What we learn']]
    comparisons = [
        ('Cipher familiarity', f"ROT-13 {rate('rot13_shift13')}; ROT-12 {rate('rot12_shift12')}; ROT-2 {rate('rot2_shift2')}", 'ROT-12 and ROT-2 do not finish; this is a completion gap, not six proven wrong decodings.'),
        ('Alphabetical sorting', f"Forward {rate('alphabetical_fwd')}; reverse {rate('reverse_alphabetical_rev')}", 'Forward finishes on all three; reverse finishes on none.'),
        ('Number sorting', f"Ascending {rate('ascending')}; descending {rate('descending')}", 'Both directions run out of output budget.'),
        ('Linear functions', f"Familiar {rate('fahrenheit_actual')}; altered {rate('fake_linear')}", 'Both finish with the target. The altered formula does not fail in these examples.'),
        ('ROT-13 output groups', '; '.join(f"{label} {rate(condition)}" for label, condition in [('Ordinary','rot13dec_highprob'),('Medium','rot13dec_mediumprob'),('Reordered','rot13dec_lowprob'),('Altered word','rot13dec_adversarial')]), 'One ordinary reply finishes; the other groups all truncate. Only three items per group.'),
        ('ROT-12 output groups', f"Ordinary {rate('rot12dec_highprob')}; reordered {rate('rot12dec_lowprob')}", 'All six truncate; there is no observed gap between these groups.'),
        ('Word reversal', '; '.join(f"{label} {rate(condition)}" for label, condition in [('Ordinary','revdec_highprob'),('Medium','revdec_mediumprob'),('Reordered','revdec_lowprob'),('Altered word','revdec_adversarial')]), 'Unusual outputs sometimes succeed. Familiar wording is not required for every answer.'),
        ('Article swapping', f"Ordinary {rate('swap_highprob')}; reordered {rate('swap_lowprob')}", 'All six truncate; neither group has a completed answer.'),
    ]
    multi += [list(r) for r in comparisons]
    acronym = [['Requested label / condition', 'Exact completed', 'Unfinished']]
    order = {'acronym1_11': 0, 'acronym1_15': 1, 'acronym1_51': 2}
    for g in sorted([g for g in groups if g['contributor']=='teammate' and g['run_kind']=='pilot' and 'acronym' in g['task']], key=lambda g:(g['model_requested'],order[g['task']])):
        label = {'acronym1_11':'common input / output', 'acronym1_15':'rarer input', 'acronym1_51':'rarer output'}[g['task']]
        acronym.append([('30B-A3B' if g['model_requested']=='qwen3-30b-a3b' else '32B')+' / '+label, f"{g['strict_correct']}/{g['strict_denominator']}", str(g['truncated'])])

    audit = summary['friend2_prompt_variant_evidence']
    extension = [['Requested label', 'Cipher', 'Direct: exact / replies', 'Standard: exact / replies', 'Table: exact / replies']]
    phase1_lookup={(c['model_requested'],c['task'],c['prompt_variant']):c for c in audit['cells']}
    for model in ['qwen3-30b-a3b','qwen3-32b']:
        for task in ['rot13dec','rot12dec']:
            values=[]
            for mode in ['direct_mode','thinking_mode','retrieved_guidance']:
                c=phase1_lookup[(model,task,mode)]
                values.append(f"{c['strict_completed_exact']} / {c['returned_item_responses']}")
            extension.append(['30B-A3B' if model=='qwen3-30b-a3b' else '32B','ROT-13' if task=='rot13dec' else 'ROT-12',*values])
    phase2=[['New test (3 planned per label)', 'Requested 30B-A3B', 'Requested 32B']]
    phase2_lookup={(c['model_requested'],c['task'],c['condition']):c for c in audit['phase2_cells']}
    if phase2_lookup:
        for label,task,condition in [('Spacing / ROT-13','rot13dec','char_spaced_stimuli'),('Spacing / ROT-12','rot12dec','char_spaced_stimuli'),('Budget labeled 4096 / ROT-12','rot12dec','budget_4096_tokens'),('Three examples / ROT-12','rot12dec','fewshot_3shot')]:
            values=[]
            for model in ['qwen3-30b-a3b','qwen3-32b']:
                c=phase2_lookup[(model,task,condition)]
                value=f"{c['returned_records']} replies; {c['truncated_records']} unfinished"
                if c['request_error_records']:
                    value+=f"; {c['request_error_records']} API "+('error' if c['request_error_records']==1 else 'errors')
                values.append(value)
            phase2.append([label,*values])
    error_table = [['Case / task', 'Expected', 'Actual completed answer', 'Specific error']]
    for i, r in enumerate(wrong, 1):
        expected = r['expected']
        actual = r['observed_answer']
        if i == 1:
            expected, actual = '...their own path...', '...their own way...'
        error_table.append([f"F{i}: "+('ROT-13' if r['task']=='rot13dec' else 'ROT-12' if r['task']=='rot12dec' else 'Acronym'), expected, actual, r['category']])
    requirements = [
        ['Hackathon item', 'Evidence and current status'],
        ['Central claim + two open models', 'Task/output conditions tested. Two Qwen labels requested; two distinct backends remain unverified.'],
        ['Extension + prior prediction', 'Team reports submitting its original prediction. Prompt variants and new exploratory tests are logged; verified thinking/internet effects remain unestablished.'],
        ['30 failures read by hand', f"Excel shows only 5 clear completed errors. A separate 30-case packet adds 25 unfinished replies. {summary['participant_reviews_confirmed']} participant reviews confirmed; this requirement is not certified."],
        ['Surprise twist', 'No twist results were supplied.'],
        ['Code, report, slides, all logs', 'Offline rebuild, this four-page report, five slides, a simple Excel sheet, recorded outputs/errors, source references and AI disclosure are included.'],
    ]

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('ReportTitle',fontName='Helvetica-Bold',fontSize=19,leading=23,spaceAfter=10,textColor=colors.HexColor('#172C42')))
    styles.add(ParagraphStyle('ReportBody',fontName='Helvetica',fontSize=9.3,leading=12.5,spaceAfter=7))
    styles.add(ParagraphStyle('ReportSmall',fontName='Helvetica',fontSize=8,leading=10.5,spaceAfter=5))
    styles.add(ParagraphStyle('ReportCell',fontName='Helvetica',fontSize=8.1,leading=10.3))
    styles.add(ParagraphStyle('ReportHeading',fontName='Helvetica-Bold',fontSize=11,leading=14,spaceBefore=7,spaceAfter=5,textColor=colors.HexColor('#172C42')))
    story, markdown = [], []

    def para(text, small=False):
        story.append(Paragraph(escape(text),styles['ReportSmall' if small else 'ReportBody']))
        markdown.extend([text,''])

    def heading(text):
        story.append(Paragraph(escape(text),styles['ReportHeading']))
        markdown.extend(['## '+text,''])

    def page(title):
        if story: story.append(PageBreak())
        story.append(Paragraph(escape(title),styles['ReportTitle']))
        markdown.extend(['# '+title,''])

    def table(data, widths):
        cells = [[Paragraph(('<b>'+escape(str(v))+'</b>') if i==0 else escape(str(v)),styles['ReportCell']) for v in row] for i,row in enumerate(data)]
        t = Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF2F5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.25,colors.HexColor('#D8E1E8')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.extend([t,Spacer(1,7)])
        markdown.extend(['| '+' | '.join(data[0])+' |','| '+' | '.join(['---']*len(data[0]))+' |',*['| '+' | '.join(str(v) for v in row)+' |' for row in data[1:]],''])

    def chart():
        drawing = Drawing(509,85)
        drawing.add(String(0,72,'Completed with target, out of 3 replies per condition',fontName='Helvetica',fontSize=8))
        for y,label,condition in [(49,'ROT-13 ordinary','rot13dec_highprob'),(31,'ROT-13 reordered','rot13dec_lowprob'),(13,'Reversal reordered','revdec_lowprob')]:
            count=lookup[condition]['completed_with_target']
            drawing.add(String(0,y,label,fontName='Helvetica',fontSize=8))
            drawing.add(Rect(126,y-2,270,11,fillColor=colors.HexColor('#EEF3F5'),strokeColor=None))
            if count:drawing.add(Rect(126,y-2,90*count,11,fillColor=colors.HexColor('#087F8C'),strokeColor=None))
            drawing.add(String(407,y,f'{count}/3',fontName='Helvetica-Bold',fontSize=8))
        story.append(drawing)
        markdown.extend(['Chart: ordinary ROT-13 1/3; reordered ROT-13 0/3; reordered reversal 2/3. Different tasks are shown separately; these are small descriptive counts.',''])

    page('Paper 8: Combined Experiments and Findings')
    para('Team Kybers: Kaashvi Saini, Prachi Vats, Ashwin Anand, Aliyah Anand',True)
    para('AIRIS Research Hackathon | Embers of Autoregression | Experiments: 23 November 2026 | Updated '+datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %B %Y'),True)
    para('We tested exact rule-following across ciphers, acronyms, sorting, word reversal, linear functions and article swapping. The strongest completed mistakes are a changed word in ROT-13, two unrelated ROT-12 sentences, an extra acronym letter and letters in the wrong order. Other tests completed correctly. Many responses ran out of output budget, so they must be reported as unfinished rather than as proven wrong answers.')
    heading('The paper claim we tested')
    para('The paper predicts that familiar tasks, inputs and outputs are easier for language models even when the rule is deterministic. Its arXiv abstract reports GPT-4 cipher accuracy of 51% for high-probability outputs and 13% for low-probability outputs [1]. We tested related conditions on requested Qwen3-30B-A3B and Qwen3-32B labels. A shift comparison tests task familiarity; changing sentence wording or order tests a different question about output probability. These are separate comparisons.')
    heading('All supplied experiment sets are included')
    table(overview,[125,42,42,40,260])
    para(f"Total: {summary['top_level_source_records']} source records, {summary['returned_response_records']} returned outputs and {summary['final_request_error_records']} request errors. These are recorded rows, not a claim of that many independent calls. The 60 prepared cipher cases (30 per shift) are a test plan; preparing them does not mean every case was run. Fourteen repeated shortened cipher excerpts are excluded from scoring.")
    heading('How we checked the tests')
    para(f'All {checks} returned-record answer keys pass rule checks: letter shifts, initials, sorting, reversal, counting, arithmetic and article swapping. Pig Latin references were checked by encoding them back to the input; decoding can be ambiguous. The 3,400 supplied acronym/cipher stimulus keys also pass. Each example links to a file and row. Generated copies and published-author logs are not counted as new team experiments.')
    para('We keep three outcomes separate: (1) completed exact answer, (2) completed visible text containing the target with extra explanation, and (3) unfinished response (finish_reason=length). The second is a diagnostic, not answer-only accuracy. API errors are not wrong model answers. Source code and logs do not independently verify backend identity; some requests for 32B returned a 30B label.')

    page('Replication Findings: Ciphers and Other Tasks')
    para('The multi-task pilot has 63 records in 21 conditions, with three examples per condition. The table covers all 21 conditions. Fractions below count completed visible replies containing the expected answer; they do not count text found only in reasoning. All 20 completed replies contain the target, but include explanations; 43 replies are unfinished. None are answer-only exact matches.')
    table(multi,[104,190,215])
    chart()
    heading('Acronym pilots: included as supporting evidence')
    table(acronym,[300,110,99])
    para('The acronym table uses the stricter completed exact-answer rule. Older correct flags sometimes counted target letters inside unfinished reasoning, so those old flags are not the headline result. The legacy 32B pilot lacks original API envelopes and has uniform latency/token fields; its 32/33 result cannot establish an architecture advantage.',True)
    para('Relation to the paper: some completion patterns fit the familiarity prediction, but do not prove its cause. Both linear formulas work, and unusual reversal outputs sometimes work. Three items per condition, repeated payloads and missing backend evidence prevent a strong numerical replication of the paper.',True)
    heading('What the final folder adds')
    para('Its 56 additional responses contain eight completed one-word counting answers and 48 unfinished replies. Common-word and rare-word counting each finish correctly in 4/5 cases on the requested 30B label; every target is 1. This is a basic check, not evidence of a frequency gap. All other added tasks are unfinished. The source code uses different short budgets for the two model labels (250 versus 150), so we exclude claims that one model is better. All 82 source files were audited; duplicate exports match the original run logs.',True)

    page('Extensions: Thinking, Guidance and New Tests')
    heading('Original predictions and prompt comparisons')
    para('We predicted thinking and internet-sourced guidance would help ROT-12 more than ROT-13; the team reports submitting that prediction. The saved first extension compares Direct (answer-only instruction), Standard (ordinary prompt, named thinking_mode in the source), and Table (authored substitution table). Direct still generates reasoning, and Table has no logged web retrieval. These are prompt comparisons; actual thinking-on/off and internet effects remain unestablished.')
    table(extension,[89,52,121,126,121])
    para('Each cell planned four items. Fractions show exact completed answers / received replies, excluding API errors. Phase 1 has 48 item opportunities, 54 attempt records, 42 replies (33 unfinished) and 12 errors; six items have no reply. The full 12-cell table, including missing items, errors and unfinished counts, is analysis/friend2_extension_cells.csv. We select the first returned reply per item without choosing on correctness.',True)
    para('A useful matched case: for requested 30B-A3B, ROT-12 item 2, Direct and Standard both truncated with empty final content. Table returned exactly "Well, it was not exactly planned from the beginning." This is one observed completion, not a reliable general benefit. All five exact Phase-1 replies used Table; four Standard replies contained the target with explanations. The separate web-sourced pilot truncated and changed its system instruction, so it does not isolate internet guidance.')
    heading('Added in the updated ZIP: three exploratory interventions')
    table(phase2,[179,165,165])
    para('The new log adds 24 attempts: 20 replies, all unfinished, and four API errors. No new condition produced a completed answer. Spacing changes the input presentation; the larger-budget and three-example conditions use ROT-12. These additional hypotheses are exploratory: no evidence of a prior submitted prediction was supplied for them.')
    para('The budget is labeled 4096 in the condition and source code; per-call configuration and token usage are absent. The complete target appears in reasoning in 6/6 budget replies and 4/6 three-example replies. That is a text-containment diagnostic, not proof the task was solved internally. These trials did not deliver completed answers; they do not prove that more compute or examples can never help.')
    para('Some source flags wrongly call these 20 unfinished replies untruncated. We use the server finish reason and keep the original flags. Spacing prompts also contain an unfilled template label; no measurements show how letters were tokenized. The data cannot establish a tokenization cause. Seven identical-payload groups, including two new cross-model budget pairs, leave model identity and independent calls uncertain.',True)

    page('Meaningful Errors, Validity and Hackathon Status')
    para('These five replies finished and chose wrong content. The simple Manual_Error_Review.xlsx contains only these five cases, with short explanations and space for your check. Source details are in cell comments and analysis/KEY_ERROR_EVIDENCE.csv. Unfinished replies and correct answers with extra explanation are excluded from the Excel sheet.')
    table(error_table,[70,152,178,109])
    para('Why the cipher errors matter: ROT-13 cngu must decode to path, not its synonym way. In F2, the explanation even states N becomes H although shifting N back by 12 gives B. These are checkable rule violations. They are compatible with an influence of fluent language, but these examples alone do not establish a pretraining-probability mechanism.')
    heading('An additional useful trace: doubting the literal answer')
    para('In an altered-word ROT-13 case, the trace decodes principals, then says the intended word is probably principles and starts rechecking. The answer key really is principals. A reordered case similarly questions the phrase another may. These are qualitative signs of conflict with natural wording, not completed wrong answers: both runs truncate. They help explain why we separate internal discussion from the final response.')
    heading('What this supports for the hackathon')
    table(requirements,[134,375])
    para('The defensible conclusion is a partial reproduction: real exact-rule errors and uneven completion were observed, alongside successful counterexamples. The tests and calculations are traceable; a causal explanation, reliable effect size, two verified checkpoints, and completed thinking/internet ablations are not established. The supplied brief explicitly accepts an honestly explained unsuccessful reproduction [2].')
    heading('Sources and disclosure')
    para('[1] McCoy et al., Embers of Autoregression, arXiv:2309.13638 (2023 preprint; PNAS 2024): https://arxiv.org/abs/2309.13638. Official stimuli: https://github.com/tommccoy1/embers-of-autoregression. [2] Supplied AIRIS Research Hackathon Problem Statements PDF. Additional resource: saved Wikipedia Caesar-cipher excerpt. Experimental evidence: supplied run files and redacted source logs; see MASTER_RAW_RESPONSES.jsonl and analysis/REPORT_EVIDENCE_INDEX.csv.',True)
    para('ChatGPT assisted planning, code, debugging, checking logs, annotations, report and slides. Supplied documents also name Antigravity and an @verifier role; participants should confirm the complete tool list. These annotations are AI-assisted, not a certification of human review. No experimental outputs or missing results were generated during this report rebuild.',True)

    def footer(canvas, doc):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#536477'))
        canvas.drawString(43,25,'Paper 8 | Combined results from all supplied experiments | AI-assisted')
        canvas.drawRightString(552,25,f'{doc.page} / 4')
    SimpleDocTemplate(str(root/'report/Combined_Report.pdf'),pagesize=(595.28,841.89),leftMargin=43,rightMargin=43,topMargin=34,bottomMargin=43,title='Paper 8: Combined Experiments and Findings').build(story,onFirstPage=footer,onLaterPages=footer)
    text = '\n'.join(markdown)
    for path in [root/'report/report.md',root/'MASTER_RESEARCH_LOG.md',root/'results/master/MASTER_RESEARCH_LOG.md']:
        path.write_text(text,encoding='utf-8')
    comparison=['# Current descriptive comparisons','',
                'Primary conditions are in analysis/COMBINED_PRIMARY_FINDINGS.csv. Completed target containment, strict exact completion and target-in-reasoning diagnostics are distinct. Checkpoints and independent calls remain unverified.','']
    for title,data in [('Phase 1: exact completed / received replies',extension),('Phase 2: all returned replies are unfinished',phase2)]:
        comparison.extend(['## '+title,'','| '+' | '.join(data[0])+' |','| '+' | '.join(['---']*len(data[0]))+' |',*['| '+' | '.join(str(v) for v in row)+' |' for row in data[1:]],''])
    comparison.append('See analysis/friend2_phase2_cells.csv and PHASE2_CASE_AUDIT.csv. Source truncation flags are retained; finish_reason governs classification. Target text in reasoning is not called internally solved. No causal tokenization, architecture, thinking-switch or internet-retrieval claim is established.')
    for path in [root/'MODEL_COMPARISON.md',root/'results/master/MODEL_COMPARISON.md']:
        path.write_text('\n'.join(comparison)+'\n',encoding='utf-8')
    return primary
