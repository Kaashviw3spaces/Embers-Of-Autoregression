"""Build an exact-size Kaggle card from the project's verified error example."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent


def font(size,bold=False):
    names=['/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',
           '/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf']
    for path in names:
        if Path(path).exists():return ImageFont.truetype(path,size)
    return ImageFont.load_default(size=size)


def main():
    target=ROOT/'submission_assets';target.mkdir(exist_ok=True)
    image=Image.new('RGB',(560,280),'#0D1B2A');draw=ImageDraw.Draw(image)
    draw.text((28,22),'TEAM KYBERS  |  PAPER 8',font=font(12,True),fill='#5BD5C0')
    draw.text((28,66),'Embers of',font=font(32,True),fill='white')
    draw.text((28,106),'Autoregression',font=font(32,True),fill='white')
    draw.text((28,168),'Testing exact rules',font=font(16),fill='#D5E2EB')
    draw.text((28,190),'on Qwen models',font=font(16),fill='#D5E2EB')
    draw.rounded_rectangle((342,65,532,214),radius=12,fill='#152B3E')
    draw.text((357,82),'ROT-13',font=font(11,True),fill='#5BD5C0')
    draw.text((357,108),'cngu',font=font(30,True),fill='white')
    draw.text((357,155),'EXPECTED',font=font(9),fill='#B9CBD9')
    draw.text((448,155),'ACTUAL',font=font(9),fill='#B9CBD9')
    draw.text((357,172),'path',font=font(22,True),fill='#5BD5C0')
    draw.text((448,172),'way',font=font(22,True),fill='#FFADAB')
    draw.line((28,237,532,237),fill='#087F8C',width=3)
    draw.text((28,250),'AIRIS Research Hackathon 2026',font=font(12),fill='#B9CBD9')
    path=target/'Kaggle_Thumbnail_560x280.png';image.save(path)
    assert Image.open(path).size==(560,280)
    print(path)


if __name__=='__main__':main()
