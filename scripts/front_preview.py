#!/usr/bin/env python3
"""Render clean single-card FRONTS (cropped to trim, no guides) for review."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
from corner_badges import make_badge, W, H, BLEED

ROOT="/Users/blu/card-borders/poker-deck"; BORD=ROOT+"/borders"; ARTDIR=ROOT+"/art"
P=json.load(open(ROOT+"/plan.json"))
TRIM=(BLEED,BLEED,W-BLEED,H-BLEED)

def render(num):
    cell=next(c for c in P["cells"] if c["num"]==num)
    elem=cell["element"]
    cv=Image.new("RGBA",(W,H),(0,0,0,0))
    cv.alpha_composite(Image.open(BORD+"/window_base.png").convert("RGBA"))   # dark card interior (placeholder bg)
    if cell.get("art"):
        a=cell["art"]; raw=open(ARTDIR+"/"+a["file"],"rb").read()
        cv.alpha_composite(Image.frombytes("RGBA",(a["w"],a["h"]),raw,"raw","BGRA"),(a["x"],a["y"]))
    cv.alpha_composite(Image.open(BORD+f"/border_{elem}.png").convert("RGBA"))
    cv.alpha_composite(make_badge(num,elem))
    return cv.crop(TRIM)                                                       # cut to trim

nums=[int(x) for x in sys.argv[1:]] or [1,5]
cards=[render(n) for n in nums]
sc=0.42; tw,th=int(1500*sc),int(2100*sc)
gap=46; sheet=Image.new("RGB",(tw*len(cards)+gap*(len(cards)+1), th+gap+34),(244,240,232))
d=ImageDraw.Draw(sheet)
try: f=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",18)
except: f=ImageFont.load_default()
for i,(n,c) in enumerate(zip(nums,cards)):
    c=c.resize((tw,th),Image.LANCZOS)
    x=gap+i*(tw+gap); sheet.paste(c,(x,gap),c)
    cell=next(cc for cc in P["cells"] if cc["num"]==n)
    d.text((x+tw//2, gap+th+6), f"#{n}  {cell['category']} / {cell['element']}", font=f, fill=(40,30,20), anchor="ma")
out=ROOT+"/_FRONT-preview.png"; sheet.save(out); print("wrote",out,sheet.size)
