"""Render every page and create contact sheets for human visual inspection."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import subprocess
import json

PAPER=Path(__file__).resolve().parents[1]
ROOT=PAPER.parents[1] if PAPER.parent.name=='papers' else PAPER
OUT=ROOT/'tmp/pdfs/lean-proof-architecture'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run(['pdftoppm','-r','110','-png',str(PAPER/'lean-proof-architecture.pdf'),str(OUT/'page')],check=True)
    pages=sorted(OUT.glob('page-*.png'))
    for start in range(0,len(pages),8):
        group=pages[start:start+8]
        canvas=Image.new('RGB',(4*390,2*560),'#d0d0d0')
        draw=ImageDraw.Draw(canvas)
        for i,path in enumerate(group):
            im=Image.open(path).convert('RGB')
            thumb=ImageOps.contain(im,(375,525))
            x=(i%4)*390+(390-thumb.width)//2
            y=(i//4)*560+25
            canvas.paste(thumb,(x,y))
            draw.text(((i%4)*390+12,(i//4)*560+7),path.stem,fill='black')
        canvas.save(OUT/f'contact-{start//8+1}.png')
    print(json.dumps({'pages_rendered':len(pages),'output':str(OUT)}))

if __name__=='__main__':main()
