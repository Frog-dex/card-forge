#!/usr/bin/env python3
"""Two deck variants that differ ONLY in the line-art cutouts:
  WHITE version -> white interior, cutout line art = BLACK
  BLACK version -> dark  interior, cutout line art = WHITE
The colored parts (element gem emblems, marble borders, corner marbles) are
IDENTICAL on both. Writes _DECK-WHITE.png and _DECK-BLACK.png."""
import os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont
from corner_badges import make_badge

THIN={"Locations":2}   # extra line-thinning for detailed/scene rows (px of erosion); default 1

ROOT="/Users/blu/card-borders/poker-deck"; BORD=ROOT+"/borders"; ARTDIR=ROOT+"/art"
P=json.load(open(ROOT+"/plan.json")); ROWS=P["rows"]; COLS=P["cols"]
TW=240; TH=round(TW*2250/1650); PAD=16; LBLH=34; GUT=140; TOP=84
SW=GUT+7*(TW+PAD)+PAD; SH=TOP+7*(TH+LBLH+PAD)+PAD
def font(sz):
    p="/System/Library/Fonts/Supplemental/Arial.ttf"
    try: return ImageFont.truetype(p,sz)
    except: return ImageFont.load_default()
F=font(20); Fs=font(15); Fh=font(26)
bcache={k:Image.open(BORD+f"/border_{k}.png").convert("RGBA").resize((TW,TH),Image.LANCZOS) for k in COLS}
badgecache={c["num"]:make_badge(c["num"],c["element"]).resize((TW,TH),Image.LANCZOS) for c in P["cells"]}
sx=TW/1650.0; sy=TH/2250.0
HEX={"water":"#1c6baf","wood":"#85dc7b","electric":"#d3cf61","fire":"#c22c37","metal":"#5a6068","earth":"#684a36","spirit":"#64318f"}
cellmap={(c["row"],c["col"]):c for c in P["cells"]}

def build(mode):
    white = (mode=="white")
    interior = (255,255,255,255) if white else (24,24,28,255)
    linecol  = (18,18,18)        if white else (242,242,242)   # cutout line art color
    sheetbg  = (232,228,220)     if white else (16,16,18)
    txt      = (55,42,26)        if white else (222,216,206)
    sheet=Image.new("RGB",(SW,SH),sheetbg); d=ImageDraw.Draw(sheet)
    d.text((PAD,26),f"Spirit Strikers - {mode.upper()} version (line art {linecol==(18,18,18) and 'black' or 'white'}; colors identical)",font=Fh,fill=txt)
    for c,k in enumerate(COLS):
        x=GUT+c*(TW+PAD); rgb=tuple(int(HEX[k][i:i+2],16) for i in (1,3,5))
        d.text((x+TW/2,TOP-22),k.upper(),font=Fs,fill=rgb,anchor="mm")
    for r,cat in enumerate(ROWS):
        ry=TOP+r*(TH+LBLH+PAD); d.text((10,ry+TH/2),cat,font=F,fill=txt,anchor="lm")
        for c in range(7):
            cell=cellmap[(r,c)]; x=GUT+c*(TW+PAD)
            is_emb=str(cell.get("card","")).startswith("element-")
            card=Image.new("RGBA",(TW,TH),interior)
            if cell.get("art"):
                a=cell["art"]; raw=open(ARTDIR+"/"+a["file"],"rb").read()
                cut=Image.frombytes("RGBA",(a["w"],a["h"]),raw,"raw","BGRA")
                if is_emb:
                    art=cut                                   # colored gem emblem — keep as-is
                    # CROPPED dark backing: hugs the emblem only (not the whole card)
                    dd=ImageDraw.Draw(card)
                    px,py=round(a["x"]*sx),round(a["y"]*sy); pw,ph=round(a["w"]*sx),round(a["h"]*sy)
                    pad=round(pw*0.07)
                    dd.rounded_rectangle([px-pad,py-pad,px+pw+pad,py+ph+pad],radius=round(pw*0.10),fill=(20,20,24,255))
                else:
                    # vector-traced art: alpha is already smooth + pre-thinned — recolor directly, no erosion
                    art=Image.new("RGBA",cut.size,linecol+(255,)); art.putalpha(cut.getchannel("A"))
                art=art.resize((max(1,round(a["w"]*sx)),max(1,round(a["h"]*sy))),Image.LANCZOS)
                card.alpha_composite(art,(round(a["x"]*sx),round(a["y"]*sy)))
            card.alpha_composite(bcache[cell["element"]])
            card.alpha_composite(badgecache[cell["num"]])
            sheet.paste(card,(x,ry),card)
            lbl=(cell["card"].replace("card-","#") if cell.get("card") else "BLANK")
            d.text((x+TW/2,ry+TH+4),f"{cell['num']} {lbl}",font=Fs,fill=txt,anchor="ma")
    out=ROOT+f"/_DECK-{mode.upper()}.png"; sheet.save(out); print("wrote",out,sheet.size)

build("white"); build("black")
