#!/usr/bin/env python3
"""Render a single labeled 7x7 contact sheet PNG from plan.json for sign-off."""
import os, json
from PIL import Image, ImageDraw, ImageFont
from corner_badges import make_badge

ROOT="/Users/blu/card-borders/poker-deck"
BORD=os.path.join(ROOT,"borders")
ARTSRC="/Users/blu/spirit-strikers-deck/images/cards-bw-cutout"
ARTDIR="/Users/blu/card-borders/poker-deck/art"
P=json.load(open(os.path.join(ROOT,"plan.json")))
cells=P["cells"]; ROWS=P["rows"]; COLS=P["cols"]

TW=240; TH=round(TW*2250/1650)        # card thumb
PAD=16; LBLH=34; GUT=140; TOP=84
SW=GUT+7*(TW+PAD)+PAD
SH=TOP+7*(TH+LBLH+PAD)+PAD
sheet=Image.new("RGB",(SW,SH),(18,17,21))
d=ImageDraw.Draw(sheet)
def font(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial.ttf","/Library/Fonts/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p,sz)
            except: pass
    return ImageFont.load_default()
F=font(20); Fs=font(15); Fh=font(26)

# cache thumb borders per element + window base
bcache={}
for k in COLS:
    b=Image.open(os.path.join(BORD,f"border_{k}.png")).convert("RGBA").resize((TW,TH),Image.LANCZOS)
    bcache[k]=b
wb=Image.open(os.path.join(BORD,"window_base.png")).convert("RGBA").resize((TW,TH),Image.LANCZOS)
sx=TW/1650.0; sy=TH/2250.0

d.text((PAD,26),"Spirit Strikers - 49 poker cards (7 categories x 7 elements)  |  600 DPI, 2.5x3.5in + 1/8in bleed",font=Fh,fill=(227,199,102))

# column headers (elements)
for c,k in enumerate(COLS):
    x=GUT+c*(TW+PAD); hexc={ "fire":"#c22c37","water":"#1c6baf","wood":"#85dc7b","electric":"#d3cf61","earth":"#684a36","spirit":"#64318f","metal":"#5a6068"}[k]
    rgb=tuple(int(hexc[i:i+2],16) for i in (1,3,5))
    d.text((x+TW/2,TOP-22),k.upper(),font=Fs,fill=rgb,anchor="mm")

cellmap={(c["row"],c["col"]):c for c in cells}
for r,cat in enumerate(ROWS):
    ry=TOP+r*(TH+LBLH+PAD)
    d.text((10,ry+TH/2),cat,font=F,fill=(236,233,225),anchor="lm")
    for c in range(7):
        cell=cellmap[(r,c)]
        x=GUT+c*(TW+PAD)
        card=Image.new("RGBA",(TW,TH),(26,26,30,255))
        card.alpha_composite(wb)
        if cell["art"]:
            a=cell["art"]
            raw=open(os.path.join(ARTDIR,a["file"]),"rb").read()
            art=Image.frombytes("RGBA",(a["w"],a["h"]),raw,"raw","BGRA")
            art=art.resize((max(1,round(a["w"]*sx)),max(1,round(a["h"]*sy))),Image.LANCZOS)
            card.alpha_composite(art,(round(a["x"]*sx),round(a["y"]*sy)))
        card.alpha_composite(bcache[cell["element"]])
        card.alpha_composite(make_badge(cell["num"],cell["element"]).resize((TW,TH),Image.LANCZOS))
        sheet.paste(card,(x,ry),card)
        lbl=(cell["card"].replace("card-","#") if cell["card"] else "BLANK")
        d.text((x+TW/2,ry+TH+4),f"{cell['label'][:2]} {lbl} {cell['element']}",font=Fs,fill=(154,151,143),anchor="ma")

out=os.path.join(ROOT,"_CONTACT-SHEET.png")
sheet.save(out)
print("wrote",out,sheet.size)
