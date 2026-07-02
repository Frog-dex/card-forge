#!/usr/bin/env python3
"""White-card version of the deck: black line-art on WHITE interior (the original
line drawings), with the colored border + corner marbles kept. For review/working."""
import os, json
from PIL import Image, ImageDraw, ImageFont
from corner_badges import make_badge

ROOT="/Users/blu/card-borders/poker-deck"; BORD=ROOT+"/borders"; ARTDIR=ROOT+"/art"
P=json.load(open(ROOT+"/plan.json")); ROWS=P["rows"]; COLS=P["cols"]
TW=240; TH=round(TW*2250/1650); PAD=16; LBLH=34; GUT=140; TOP=84
SW=GUT+7*(TW+PAD)+PAD; SH=TOP+7*(TH+LBLH+PAD)+PAD
sheet=Image.new("RGB",(SW,SH),(232,228,220)); d=ImageDraw.Draw(sheet)
def font(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial.ttf"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p,sz)
            except: pass
    return ImageFont.load_default()
F=font(20); Fs=font(15); Fh=font(26)
bcache={k:Image.open(BORD+f"/border_{k}.png").convert("RGBA").resize((TW,TH),Image.LANCZOS) for k in COLS}
sx=TW/1650.0; sy=TH/2250.0
d.text((PAD,26),"Spirit Strikers - WHITE version (original line art, black on white)",font=Fh,fill=(60,45,25))
HEX={"water":"#1c6baf","wood":"#85dc7b","electric":"#d3cf61","fire":"#c22c37","metal":"#5a6068","earth":"#684a36","spirit":"#64318f"}
for c,k in enumerate(COLS):
    x=GUT+c*(TW+PAD); rgb=tuple(int(HEX[k][i:i+2],16) for i in (1,3,5))
    d.text((x+TW/2,TOP-22),k.upper(),font=Fs,fill=rgb,anchor="mm")
cellmap={(c["row"],c["col"]):c for c in P["cells"]}
for r,cat in enumerate(ROWS):
    ry=TOP+r*(TH+LBLH+PAD); d.text((10,ry+TH/2),cat,font=F,fill=(50,40,25),anchor="lm")
    for c in range(7):
        cell=cellmap[(r,c)]; x=GUT+c*(TW+PAD)
        card=Image.new("RGBA",(TW,TH),(255,255,255,255))           # WHITE interior
        if cell.get("art"):
            a=cell["art"]; raw=open(ARTDIR+"/"+a["file"],"rb").read()
            cut=Image.frombytes("RGBA",(a["w"],a["h"]),raw,"raw","BGRA")
            blk=Image.new("RGBA",cut.size,(20,20,20,255)); blk.putalpha(cut.getchannel("A"))  # line shape -> BLACK
            blk=blk.resize((max(1,round(a["w"]*sx)),max(1,round(a["h"]*sy))),Image.LANCZOS)
            card.alpha_composite(blk,(round(a["x"]*sx),round(a["y"]*sy)))
        card.alpha_composite(bcache[cell["element"]])
        card.alpha_composite(make_badge(cell["num"],cell["element"]).resize((TW,TH),Image.LANCZOS))
        sheet.paste(card,(x,ry),card)
        lbl=(cell["card"].replace("card-","#") if cell.get("card") else "BLANK")
        d.text((x+TW/2,ry+TH+4),f"{cell['num']} {lbl}",font=Fs,fill=(90,80,65),anchor="ma")
out=ROOT+"/_CONTACT-SHEET-WHITE.png"; sheet.save(out); print("wrote",out,sheet.size)
