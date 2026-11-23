"""Five-slide editable PowerPoint and matching vector PDF, using audited counts."""
from html import escape
import json


def build(root,rows,summary):
    from pptx import Presentation
    from pptx.util import Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
    from pptx.enum.text import MSO_ANCHOR
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from analysis.combined_report import primary_findings
    from analysis.review_cases import curated_reviews

    W,H=960,540
    navy='#0D1B2A';paper='#F6F8FA';teal='#087F8C';mint='#5BD5C0';amber='#E5A24B';red='#B54446';ink='#173047';muted='#536777';white='#FFFFFF'
    prs=Presentation();prs.slide_width=Pt(W);prs.slide_height=Pt(H)
    prs.core_properties.title='Team Kybers | Embers of Autoregression'
    prs.core_properties.author='Kaashvi Saini, Prachi Vats, Ashwin Anand, Aliyah Anand'
    pdf=Canvas(str(root/'slides/Presentation.pdf'),pagesize=(W,H));pdf.setTitle('Team Kybers | Paper 8')
    slide=None;dark=False;outline=[];bounds=[]
    def rgb(c):return RGBColor.from_string(c.lstrip('#'))
    def rect(x,y,w,h,fill,border=None,radius=9):
        s=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,Pt(x),Pt(y),Pt(w),Pt(h))
        if radius:s.adjustments[0]=.12
        s.fill.solid();s.fill.fore_color.rgb=rgb(fill)
        if border:s.line.color.rgb=rgb(border);s.line.width=Pt(.7)
        else:s.line.fill.background()
        pdf.setFillColor(HexColor(fill));pdf.setStrokeColor(HexColor(border or fill))
        pdf.roundRect(x,H-y-h,w,h,radius,fill=1,stroke=bool(border))
        return s
    def text(value,x,y,w,size=20,color=ink,bold=False):
        font='Helvetica-Bold' if bold else 'Helvetica';lines=[]
        for paragraph in str(value).split('\n'):
            line=''
            for word in paragraph.split():
                attempt=(line+' '+word).strip()
                if line and stringWidth(attempt,font,size)>w*.96:lines.append(line);line=word
                else:line=attempt
            lines.append(line)
        leading=size*1.16;height=leading*len(lines)+5
        bounds.append((len(prs.slides),value,x,y,w,height))
        assert x>=0 and x+w<=W+1 and y+height<=H+1,(len(prs.slides),value,y,height)
        box=slide.shapes.add_textbox(Pt(x),Pt(y),Pt(w),Pt(height))
        frame=box.text_frame;frame.clear();frame.word_wrap=False;frame.margin_left=frame.margin_right=frame.margin_top=frame.margin_bottom=0
        frame.vertical_anchor=MSO_ANCHOR.TOP
        for i,line in enumerate(lines):
            p=frame.paragraphs[0] if i==0 else frame.add_paragraph();p.text=line
            p.font.name='Arial';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=rgb(color)
            p.space_before=Pt(0);p.space_after=Pt(0);p.line_spacing=Pt(leading)
            pdf.setFillColor(HexColor(color));pdf.setFont(font,size);pdf.drawString(x,H-y-size-i*leading,line)
        return height
    def arrow(x1,y,x2,color=teal):
        s=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Pt(x1),Pt(y),Pt(x2-4),Pt(y));s.line.color.rgb=rgb(color);s.line.width=Pt(1.5)
        pdf.setStrokeColor(HexColor(color));pdf.setLineWidth(1.5);pdf.line(x1,H-y,x2-3,H-y)
        tri=slide.shapes.add_shape(MSO_SHAPE.CHEVRON,Pt(x2-8),Pt(y-5),Pt(8),Pt(10));tri.fill.solid();tri.fill.fore_color.rgb=rgb(color);tri.line.fill.background()
        path=pdf.beginPath();path.moveTo(x2-7,H-y+4);path.lineTo(x2,H-y);path.lineTo(x2-7,H-y-4);pdf.drawPath(path,stroke=1)
    def start(kicker,title,notes,is_dark=False):
        nonlocal slide,dark
        dark=is_dark;slide=prs.slides.add_slide(prs.slide_layouts[6])
        bg=navy if dark else paper
        slide.background.fill.solid();slide.background.fill.fore_color.rgb=rgb(bg)
        pdf.setFillColor(HexColor(bg));pdf.rect(0,0,W,H,fill=1,stroke=0)
        text(kicker.upper(),54,29,850,11,mint if dark else teal,True)
        if title:text(title,54,55,855,32,white if dark else ink,True)
        slide.notes_slide.notes_text_frame.text=notes
        outline.extend(['# '+(title or kicker),'',notes,''])
    def end():
        c='#AABAC9' if dark else muted
        text('TEAM KYBERS | AIRIS | PAPER 8',54,516,700,9,c)
        text(str(len(prs.slides))+' / 5',860,516,60,9,c)
        pdf.showPage()
    primary={r['condition']:r for r in primary_findings(rows)}
    points=[('ROT-13 / ordinary','rot13dec_highprob',teal),('ROT-13 / reordered','rot13dec_lowprob',amber),
            ('Reversal / ordinary','revdec_highprob',teal),('Reversal / reordered','revdec_lowprob',amber),
            ('Alphabetical / forward','alphabetical_fwd',teal),('Alphabetical / reverse','reverse_alphabetical_rev',amber)]
    phase1=summary['friend2_prompt_variant_evidence'];phase2=phase1['phase2']
    cells={c['prompt_variant']:c for c in phase1['cells'] if c['model_requested']=='qwen3-30b-a3b' and c['task']=='rot12dec'}
    chart_data={'source_records':summary['top_level_source_records'],'returned_outputs':summary['returned_response_records'],'request_errors':summary['final_request_error_records'],
                'primary':[{'label':label,'completed_with_target':primary[key]['completed_with_target'],'n':primary[key]['records'],'condition':key} for label,key,_ in points],
                'rot12_30b':{key:{'exact':c['strict_completed_exact'],'replies':c['returned_item_responses']} for key,c in cells.items()},
                'phase2':phase2,'source_index':'analysis/REPORT_EVIDENCE_INDEX.csv'}

    start('AIRIS 2026 | Embers of Autoregression','',
          'Team Kybers: Kaashvi Saini, Prachi Vats, Ashwin Anand, Aliyah Anand. Problem: the paper predicts that task, input and output familiarity affect exact deterministic tasks. We test related conditions using supplied Qwen logs. This is a partial reproduction; backend identities are not independently verified. Reference: https://arxiv.org/abs/2309.13638.',True)
    text('Clear rules.\nUnexpected mistakes.',54,100,565,45,white,True)
    text('Does familiarity change how Qwen follows exact rules?',54,231,535,24,'#D8E4EC')
    text('We tested ciphers and other rule-based tasks from Embers of Autoregression.',54,316,520,19,'#B9CBD9')
    rect(650,112,256,246,'#152B3E')
    text('ROT-13: ONE CHECKABLE ERROR',670,131,213,11,mint,True)
    text('cngu',670,166,210,39,white,True)
    text('Required',670,229,100,13,'#B9CBD9');text('path',670,251,100,28,mint,True)
    text('Observed',792,229,100,13,'#B9CBD9');text('way',792,251,90,28,'#FFADAB',True)
    text('The cipher fixes the word.',670,313,215,13,'#D8E4EC')
    text('TEAM KYBERS',54,427,850,12,mint,True)
    text('Kaashvi Saini  |  Prachi Vats  |  Ashwin Anand  |  Aliyah Anand',54,453,850,20,white,True)
    end()

    start('Method + results','Same rules. Different completion.',
          'Workflow: supplied paper inputs -> requested Qwen API -> saved responses -> independent deterministic answer-key checks -> error review. Counts include all canonical source rows once: '+str(summary['top_level_source_records'])+' records, '+str(summary['returned_response_records'])+' returned outputs, '+str(summary['final_request_error_records'])+' request errors. Fourteen shortened cipher excerpts are excluded from scoring. Graph: completed visible text containing the expected answer, n=3 per condition; explanations allowed. This is a diagnostic, not answer-only accuracy. The primary logs do not record per-call model identity. Source: analysis/COMBINED_PRIMARY_FINDINGS.csv.')
    for x,value,label in [(54,summary['top_level_source_records'],'recorded entries'),(352,summary['returned_response_records'],'model replies'),(650,summary['final_request_error_records'],'request errors')]:
        text(str(value),x,105,125,28,teal,True);text(label,x+95,116,185,14,muted)
    for i,label in enumerate(['Paper inputs','Qwen API','Saved logs','Rule checks','Error review']):
        x=54+i*174;rect(x,158,151,40,'#E8F0F3');text(label,x+11,168,131,15,ink,True)
        if i<4:arrow(x+153,178,x+171)
    text('SMALL MULTI-TASK PILOT',54,219,850,11,teal,True)
    for i,(label,key,color) in enumerate(points):
        y=248+i*34;count=primary[key]['completed_with_target'];n=primary[key]['records']
        text(label,54,y-2,225,16,ink)
        rect(294,y+2,480,12,'#E2EAF0',radius=0)
        if count:rect(294,y+2,480*count/n,12,color,radius=0)
        text(f'{count}/{n}',798,y-3,100,17,ink,True)
    text('Completed visible replies containing the expected answer; 3 items per condition. Explanations allowed.',54,471,852,13,muted)
    end()

    wrong=[r for r in curated_reviews(rows) if r['review_group']=='Wrong completed answer']
    start('Failure analysis','Five clear errors.',
          'All five examples have finish_reason=stop. F1 ROT-13 changes path to way. F2 ROT-12 returns How would you like them done in a little while? instead of But this time, there may also be another reason. F3 ROT-12 returns I cannot understand the people around me, but they are very polite. instead of I think everyone has their own path, and they can make it happen. F4 LITERAL -> LITERALL adds L. F5 APPLIED -> APPLEID swaps I and E. Full source IDs, file rows and actual responses: analysis/KEY_ERROR_EVIDENCE.csv and Manual_Error_Review.xlsx. No causal claim about training probability is established.')
    rect(54,106,852,100,white)
    text('ROT-13',72,120,160,12,teal,True);text('cngu',72,145,175,30,ink,True)
    text('Expected',290,121,200,12,muted);text('path',290,145,200,30,teal,True)
    arrow(465,164,536)
    text('Actual',573,121,250,12,muted);text('way',573,145,250,30,red,True)
    for i,r in enumerate(wrong[1:3]):
        x=54+i*437;rect(x,224,415,154,white)
        text('ROT-12 | WRONG SENTENCE',x+17,238,380,12,teal,True)
        text('Expected: '+r['expected'],x+17,265,380,15,ink)
        text('Actual: '+r['observed_answer'],x+17,319,380,15,red)
    for i,(expected,actual,description) in enumerate([('LITERAL','LITERALL','Extra letter'),('APPLIED','APPLEID','Wrong letter order')]):
        x=54+i*437;rect(x,395,415,84,'#E8F0F3')
        text('ACRONYM | '+description.upper(),x+17,407,380,11,teal,True)
        text(expected,x+17,433,160,24,ink,True);arrow(x+172,448,x+205);text(actual,x+220,433,178,24,red,True)
    text('All five replies finished normally. Full text and source references are in the simple review sheet.',54,489,850,12,muted)
    end()

    start('Extensions','Can guidance help a cipher finish?',
          'Original predictions: thinking and internet-sourced guidance help ROT-12 more than ROT-13; the team reports submitting its prediction. Actual first extension is a prompt comparison, not verified thinking on/off or internet access. Direct still has reasoning; Table is authored guidance. Left chart: requested qwen3-30b-a3b, ROT-12, Direct 0/4 exact, Standard 0/4, Table 1/4. Same item 2: Direct and Standard truncated with empty final content; Table returned Well, it was not exactly planned from the beginning. New exploratory spacing/budget/few-shot log: 24 attempts, 20 returned responses, all length-ended, four errors. Budget 4096 is stated in source code/condition, not measured usage. No complete answer in that log. Sources: friend2_extension_cells.csv, friend2_phase2_cells.csv and PHASE2_CASE_AUDIT.csv.')
    text('ROT-12 | REQUESTED 30B-A3B',54,113,445,12,teal,True)
    text('Exact completed answers, out of 4 replies',54,140,445,17,ink,True)
    for i,(label,key) in enumerate([('Direct','direct_mode'),('Standard','thinking_mode'),('Table','retrieved_guidance')]):
        y=195+i*62;value=cells[key]['strict_completed_exact'];n=cells[key]['returned_item_responses']
        text(label,54,y,120,18,ink,True);rect(181,y+6,248,16,'#E2EAF0',radius=0)
        if value:rect(181,y+6,248*value/n,16,teal,radius=0)
        text(f'{value}/{n}',446,y-1,75,20,teal,True)
    text('Same item: Table finishes correctly;\nDirect and Standard stop at the limit.',54,408,445,17,ink)
    rect(552,115,354,337,white)
    text('ADDITIONAL TRIALS',572,134,312,12,teal,True)
    for i,label in enumerate(['Letter spacing','More budget (4096 in code)','Three worked examples']):
        rect(572,167+i*37,314,29,'#E8F0F3');text(label,584,173+i*37,290,14,ink)
    text(str(phase2['truncated_records'])+' unfinished replies',572,300,310,27,'#AF6D20',True)
    text(str(phase2['request_error_records'])+' API errors',572,340,310,21,muted,True)
    text('0 completed answers\nfrom 24 attempts',572,383,310,17,ink)
    text('Direct still reasons. Table is authored guidance. Thinking and internet effects remain unverified.',54,478,850,13,muted)
    end()

    start('Conclusion','Useful evidence. Careful conclusions.',
          'Observed: five completed rule-violating answers, a matched guided ROT-12 completion, and correct counterexamples in other deterministic tasks. The final campaign adds 56 short-budget responses: eight completed word counts (all targets 1), 48 unfinished; uneven source budgets prevent a fair architecture comparison. Overall reproduction is partial: distinct checkpoint identities, effective thinking switches and an internet effect are not established. The 30-case supplementary packet contains five completed wrong answers and 25 unfinished responses; zero participant reviews are confirmed in the supplied files. The five-row Excel sheet is not a claim of 30 human-reviewed completed errors. No surprise-twist result was supplied. AI assistance: ChatGPT; supplied documents also name Antigravity and an @verifier role. References and all evidence are in the report and source index.',True)
    rect(54,130,410,265,'#152B3E');rect(492,130,414,265,'#152B3E')
    text('Observed',75,150,365,24,mint,True)
    text('5 completed answers\nbreak exact rules.',75,198,362,22,white,True)
    text('One guided ROT-12 item finishes\nwhen two prompt controls do not.',75,266,362,18,'#D5E2EB')
    text('Other tasks give correct\ncounterexamples.',75,336,362,18,'#D5E2EB')
    text('Still open',514,150,365,24,amber,True)
    text('Verified model identities\nand thinking controls.',514,200,363,19,'#D5E2EB')
    text('A causal explanation based\non training probability.',514,265,363,19,'#D5E2EB')
    text('Participant review of 30 failures\nand the surprise-twist result.',514,329,363,18,'#D5E2EB')
    rect(54,421,852,60,teal);text('A partial reproduction, with traceable logs.',74,437,814,26,white,True)
    end()
    assert len(prs.slides)==5
    prs.save(str(root/'slides/Presentation.pptx'));pdf.save()
    (root/'slides/presentation.md').write_text('\n'.join(outline),encoding='utf-8')
    (root/'slides/CHART_DATA.json').write_text(json.dumps(chart_data,indent=2)+'\n')
    (root/'analysis/SLIDE_LAYOUT_CHECK.json').write_text(json.dumps({'slides':5,'all_text_boxes_within_page':True,'text_boxes_checked':len(bounds),'team':'Kybers','authors':['Kaashvi Saini','Prachi Vats','Ashwin Anand','Aliyah Anand'],'source':'Audited canonical results; no inference calls'},indent=2)+'\n')
