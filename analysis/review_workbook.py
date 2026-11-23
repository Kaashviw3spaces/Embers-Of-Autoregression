"""A deliberately small Excel sheet: only five completed content errors."""
from pathlib import Path


def build(root, reviews):
    from openpyxl import Workbook, load_workbook
    from openpyxl.comments import Comment
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.worksheet.page import PageMargins
    cases=list(reviews)
    assert len(cases)==30 and len({r['input'].strip().casefold() for r in cases})==30
    path=Path(root)/'Manual_Error_Review.xlsx'
    previous={}
    if path.exists():
        old=load_workbook(path)
        for row in old.active.iter_rows(min_row=5):
            if row[0].comment:
                rid=row[0].comment.text.split('\n',1)[0]
                previous[rid]=(row[5].value,row[6].value)
        old.close()
    wb=Workbook();ws=wb.active;ws.title='Review'
    wb.properties.title='30 distinct experiment review cases'
    wb.properties.description='AI-assisted observations; participant review is not pre-certified.'
    ws.sheet_view.showGridLines=False;ws.sheet_view.zoomScale=90
    ws.merge_cells('A1:G1');ws['A1']='Manual review: 30 distinct cases'
    ws['A1'].font=Font(name='Calibri',size=17,bold=True,color='173047')
    ws.merge_cells('A2:G2');ws['A2']='5 completed wrong answers + 25 unfinished replies. No repeated inputs. Mark your check after reading; source details are in number-cell comments.'
    ws['A2'].font=Font(name='Calibri',size=10,color='526477');ws['A2'].alignment=Alignment(wrap_text=True,vertical='center')
    headers=['No.','Task','Expected answer','Actual answer','What went wrong','Your check','Your note']
    for col,label in enumerate(headers,1):
        cell=ws.cell(4,col,label);cell.font=Font(name='Calibri',size=11,bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='173047');cell.alignment=Alignment(wrap_text=True,vertical='center')
    problems=['Changes path to way.','Wrong sentence. N should decode to B.','Returns an unrelated sentence.','Adds an extra L.','Swaps I and E.']
    for number,r in enumerate(cases,1):
        problem=problems[number-1] if number<=5 else 'Unfinished: '+r['draft_notes']
        if len(problem)>150:problem=problem[:147]+'...'
        index=number+4
        check,note=previous.get(r['record_id'],('Not checked',''))
        task={'rot13dec':'ROT-13','rot12dec':'ROT-12','rot2dec':'ROT-2','sort_reversealphabetical':'Reverse A-Z','sort_ascending':'Sort numbers','article_swap_prev':'Article swap'}.get(r['task'],'Acronym')
        actual=r['observed_answer'] if number<=5 else 'Unfinished. Ending: '+ ' '.join(r['evidence_excerpt'].split())[-120:]
        values=[number,task,r['expected'],actual,problem,check or 'Not checked',note or '']
        for col,value in enumerate(values,1):
            cell=ws.cell(index,col,value);cell.font=Font(name='Calibri',size=11,color='173047')
            cell.alignment=Alignment(wrap_text=True,vertical='center')
            cell.fill=PatternFill('solid',fgColor='F2F6F8' if number%2 else 'FFFFFF')
            cell.border=Border(bottom=Side(style='hair',color='D2DCE4'))
        for col in [6,7]:ws.cell(index,col).fill=PatternFill('solid',fgColor='FFF4D2')
        source=f"{r['record_id']}\nSource: {r['source_file']}\nRow: {r['source_record']}\nFinish reason: {r['finish_reason']}\nInput: {r['input']}\nFull response is in the source log and MASTER_RAW_RESPONSES.jsonl."
        ws.cell(index,1).comment=Comment(source,'Source reference')
        ws.row_dimensions[index].height=76
    for letter,width in zip('ABCDEFG',[5,12,38,38,29,14,24]):ws.column_dimensions[letter].width=width
    ws.row_dimensions[1].height=29;ws.row_dimensions[2].height=31;ws.row_dimensions[3].height=8;ws.row_dimensions[4].height=30
    ws.freeze_panes='C5';ws.auto_filter.ref='A4:G34'
    dropdown=DataValidation(type='list',formula1='"Not checked,Agree,Disagree"',allow_blank=False)
    dropdown.errorTitle='Choose a review status';dropdown.error='Select Not checked, Agree, or Disagree.';dropdown.showErrorMessage=True
    ws.add_data_validation(dropdown);dropdown.add('F5:F34')
    ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A4;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
    ws.sheet_properties.pageSetUpPr.fitToPage=True
    ws.print_options.horizontalCentered=True;ws.print_area='A1:G34';ws.print_title_rows='1:4'
    ws.page_margins=PageMargins(left=.25,right=.25,top=.3,bottom=.3,header=.1,footer=.15)
    ws.oddFooter.center.text='30 distinct cases | Wrong answers and unfinished replies are separate'
    wb.save(path)
    return path
