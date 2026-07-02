#!/usr/bin/env python3
"""Corner marble badges (Pokemon-style, upright-only collector card).
make_badge(num, elem_key) -> full-canvas RGBA (1650x2250):
  TOP-LEFT marble     = element SYMBOL (debossed glyph from symbol_<elem>.png)
  BOTTOM-RIGHT marble = the NUMBER (debossed)
Both upright. Marbles fuse into the corner border (outer edge ~0.5mm inside cut)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W,H=1650,2250
BLEED=75; BORDER=44; SAFEM=75
WIN=(BLEED+BORDER,BLEED+BORDER,W-BLEED-BORDER,H-BLEED-BORDER)
SAFE=(BLEED+SAFEM,BLEED+SAFEM,W-BLEED-SAFEM,H-BLEED-SAFEM)
BORD="/Users/blu/card-borders/poker-deck/borders"
ELEMDIR="/Users/blu/card-borders/poker-deck/elements"
D=286                      # marble diameter (+10%, nestled into the corner border)
SAFEGAP=5                  # marble outer edge ~0.2mm inside trim -> hugs the corner, covers the dark window, no crop
TRIM_OFF=BLEED+SAFEGAP     # 87px from canvas edge
FONT="/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"

def hx(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def dark(c,f): return tuple(int(v*(1-f)) for v in c)
def light(c,f): return tuple(int(v+(255-v)*f) for v in c)

import json as _json
def _marble(elem_key):
    sphere=Image.open(os.path.join(BORD,f"marble_{elem_key}.png")).convert("RGBA")
    bb=sphere.getchannel("A").getbbox()           # strip the ~5% transparent padding so the sphere fills its box
    if bb: sphere=sphere.crop(bb)
    sphere=sphere.resize((D,D),Image.LANCZOS)
    bm=_json.load(open(os.path.join(BORD,"borders_manifest.json")))
    return sphere, hx(bm["elements"][elem_key]["hex"])

def _deboss(badge, alpha, base, target):
    """deboss a glyph (L-mode alpha) into the marble: dark fill + light lower lip."""
    w,h=alpha.size; s=target/max(w,h)
    nw,nh=max(1,int(w*s)),max(1,int(h*s))
    a=alpha.resize((nw,nh),Image.LANCZOS)
    cx,cy=D//2,D//2
    lip=Image.new("RGBA",(nw,nh),light(base,0.45)); lip.putalpha(a.point(lambda v:int(v*0.6)))
    dk =Image.new("RGBA",(nw,nh),dark(base,0.62));  dk.putalpha(a)
    badge.alpha_composite(lip,(cx-nw//2+3, cy-nh//2+4))
    badge.alpha_composite(dk ,(cx-nw//2,   cy-nh//2))

def marble_number(elem_key, label):
    badge, base=_marble(elem_key)
    try: font=ImageFont.truetype(FONT,int(D*0.5))
    except Exception: font=ImageFont.load_default()
    tmp=Image.new("L",(D,D),0)
    ImageDraw.Draw(tmp).text((D//2,D//2),label,font=font,fill=255,anchor="mm")
    bbox=tmp.getbbox()
    if bbox: _deboss(badge, tmp.crop(bbox), base, int(D*0.46))
    return badge

def marble_symbol(elem_key):
    badge, base=_marble(elem_key)
    p=os.path.join(ELEMDIR,f"symbol_{elem_key}.png")
    if os.path.exists(p):
        a=Image.open(p).convert("RGBA").getchannel("A")
        bbox=a.getbbox()
        if bbox: _deboss(badge, a.crop(bbox), base, int(D*0.56))
    return badge

MARBLES="/Users/blu/card-borders/poker-deck/marbles"   # per-card unique marbles (build_marbles_98.py)
def _card_marble(num, slot):
    """Load the pre-baked unique marble for this card+slot, or None to fall back."""
    p=os.path.join(MARBLES,f"{num:02d}_{slot}.png")
    if os.path.exists(p):
        im=Image.open(p).convert("RGBA")
        return im if im.size==(D,D) else im.resize((D,D),Image.LANCZOS)
    return None

def make_badge(num, elem_key, **_):
    tl=_card_marble(num,"top")                 # top-left = element symbol (unique per card)
    if tl is None: tl=marble_symbol(elem_key)  # fallback: shared marble + live deboss
    br=_card_marble(num,"bot")                 # bottom-right = number (unique per card)
    if br is None: br=marble_number(elem_key, str(num))
    canvas=Image.new("RGBA",(W,H),(0,0,0,0))
    canvas.alpha_composite(tl,(TRIM_OFF, TRIM_OFF))                 # top-left
    canvas.alpha_composite(br,(W-TRIM_OFF-D, H-TRIM_OFF-D))         # bottom-right
    return canvas

if __name__=="__main__":
    # prototype: card #1 = water. show element symbol (TL) + number (BR) on colored marble.
    elem,num="water",1
    base=Image.new("RGBA",(W,H),(13,13,16,255))
    base.alpha_composite(Image.open(os.path.join(BORD,"window_base.png")).convert("RGBA"))
    base.alpha_composite(Image.open(os.path.join(BORD,f"border_{elem}.png")).convert("RGBA"))
    base.alpha_composite(make_badge(num,elem))
    base.thumbnail((520,720),Image.LANCZOS)
    out="/Users/blu/card-borders/poker-deck/_PROTO-corner-49.png"
    base.convert("RGB").save(out); print("wrote",out,base.size)
