"""Generate README visuals from saved project tables; no model calls.

Optional documentation tools: Pillow and matplotlib. These are not needed for
the experiment pipeline; committed images are ready to display on GitHub.
"""
from pathlib import Path
import csv
import math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/assets'
TEAL='#087F8C'
AMBER='#C77D23'
INK='#173047'


def font(size,bold=False):
    for name in [
        '/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',
    ]:
        if Path(name).exists():return ImageFont.truetype(name,size)
    return ImageFont.load_default(size=size)


def error_animation():
    with (ROOT/'analysis/KEY_ERROR_EVIDENCE.csv').open(newline='') as file:
        errors={r['example']:r for r in csv.DictReader(file)}
    assert ' path,' in errors['F1']['expected'] and ' way,' in errors['F1']['observed']
    examples=[('ROT-13 | ciphertext: cngu','path','way',errors['F1']['category']),
              ('ACRONYM',errors['F4']['expected'],errors['F4']['observed'],errors['F4']['category']),
              ('ACRONYM',errors['F5']['expected'],errors['F5']['observed'],errors['F5']['category'])]
    frames=[]
    for case,(task,expected,actual,category) in enumerate(examples):
        for tick in range(10):
            im=Image.new('RGB',(960,246),'#0D1B2A');draw=ImageDraw.Draw(im)
            draw.text((34,25),'TEAM KYBERS  /  AIRIS 2026',font=font(12,True),fill='#5BD5C0')
            draw.text((34,65),'Rule-following.',font=font(35,True),fill='white')
            draw.text((34,107),'Failure modes.',font=font(35,True),fill='white')
            draw.text((35,169),'Revisiting Embers of Autoregression',font=font(16),fill='#C6D7E3')
            draw.text((35,211),'Three examples from saved completed replies',font=font(12),fill='#99ADBE')
            strength=(math.sin(tick*math.pi/9)+1)/2
            edge=(int(34+30*strength),int(84+40*strength),int(104+40*strength))
            draw.rounded_rectangle((507,27,927,204),radius=16,fill='#152B3E',outline=edge,width=2)
            draw.text((530,45),task,font=font(13,True),fill='#5BD5C0')
            draw.text((530,84),'EXPECTED',font=font(11),fill='#A7BDCD')
            draw.text((735,84),'ACTUAL',font=font(11),fill='#A7BDCD')
            size=39 if max(len(expected),len(actual))<=4 else 29
            draw.text((530,106),expected,font=font(size,True),fill='#5BD5C0')
            draw.text((735,106),actual,font=font(size,True),fill='#FFB2AE')
            draw.text((531,169),category,font=font(13),fill='#D6E4ED')
            for i in range(3):
                x=875+i*17
                draw.ellipse((x,220,x+6,226),fill='#5BD5C0' if i==case else '#3E566B')
            frames.append(im)
    frames[0].save(OUT/'readme-errors.gif',save_all=True,append_images=frames[1:],duration=190,loop=0,optimize=True)


def results_chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    with (ROOT/'analysis/COMBINED_PRIMARY_FINDINGS.csv').open(newline='') as file:
        primary={r['condition']:r for r in csv.DictReader(file)}
    with (ROOT/'analysis/friend2_extension_cells.csv').open(newline='') as file:
        guidance={r['prompt_variant']:r for r in csv.DictReader(file) if r['model_requested']=='qwen3-30b-a3b' and r['task']=='rot12dec'}
    rows=[('ROT-13 / ordinary','rot13dec_highprob'),('ROT-13 / reordered','rot13dec_lowprob'),
          ('Reversal / ordinary','revdec_highprob'),('Reversal / reordered','revdec_lowprob'),
          ('Alphabetical / forward','alphabetical_fwd'),('Alphabetical / reverse','reverse_alphabetical_rev')]
    values=[int(primary[k]['completed_with_target']) for _,k in rows]
    assert all(int(primary[k]['records'])==3 for _,k in rows)
    modes=['direct_mode','thinking_mode','retrieved_guidance']
    exact=[int(guidance[k]['strict_completed_exact']) for k in modes]
    assert all(int(guidance[k]['returned_item_responses'])==4 for k in modes)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':INK,'axes.labelcolor':INK,'xtick.color':'#536777','ytick.color':INK,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False})
    fig,(left,right)=plt.subplots(1,2,figsize=(12,4.6),gridspec_kw={'width_ratios':[1.55,1]})
    fig.patch.set_facecolor('#F7F9FB')
    for ax in [left,right]:ax.set_facecolor('#F7F9FB');ax.set_axisbelow(True)
    left.barh(range(6),values,height=.48,color=[TEAL,AMBER]*3,zorder=3)
    left.set_yticks(range(6),[label for label,_ in rows]);left.invert_yaxis()
    left.set_xlim(0,3.55);left.set_xticks([0,1,2,3]);left.xaxis.grid(True,color='#E0E7EE')
    left.tick_params(axis='y',length=0,pad=10);left.tick_params(axis='x',length=0)
    left.set_title('Completed replies with expected text',loc='left',fontsize=12,fontweight='bold',pad=18)
    left.set_xlabel('Replies out of 3 per condition',labelpad=11)
    for i,value in enumerate(values):
        left.text(value+.08,i,f'{value}/3',va='center',fontweight='bold',fontsize=10)
        if value==0:left.plot(0,i,'o',color=AMBER,markersize=3,clip_on=False)
    right.bar(range(3),exact,width=.5,color=['#B7C7D2','#B7C7D2',TEAL],zorder=3)
    right.set_xticks(range(3),['Direct','Standard','Table']);right.set_ylim(0,4.5);right.set_yticks([0,1,2,3,4]);right.yaxis.grid(True,color='#E0E7EE')
    right.tick_params(axis='both',length=0,pad=8)
    right.set_title('ROT-12 prompt comparison',loc='left',fontsize=12,fontweight='bold',pad=18)
    right.set_ylabel('Exact completed answers',labelpad=8)
    right.set_xlabel('Requested Qwen3-30B-A3B | 4 replies each',labelpad=11,fontsize=9)
    for i,value in enumerate(exact):right.text(i,value+.13,f'{value}/4',ha='center',fontweight='bold',fontsize=11)
    fig.subplots_adjust(left=.21,right=.975,top=.84,bottom=.23,wspace=.57)
    fig.text(.025,.045,'Small pilots. Left: explanations allowed. Right: answer-only exact match. See the report for methods and limits.',fontsize=9,color='#536777')
    fig.savefig(OUT/'readme-results.png',dpi=180,facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    error_animation();results_chart()
    print('README animation and results chart generated from source tables.')
