#!/usr/bin/env python3
"""Extract just the dark element GLYPH (flame, drop, sprout, tornado, triangle,
yin-yang, wheel) from each gem emblem -> symbol_<elem>.png (black + alpha, trimmed).
Used to deboss the element symbol into the top-left corner marble."""
import os
import numpy as np
from PIL import Image, ImageFilter

ELEMDIR="/Users/blu/card-borders/poker-deck/elements"
ELEMS=["water","wood","metal","electric","fire","earth","spirit"]

def extract(elem):
    im=Image.open(os.path.join(ELEMDIR,f"emblem_{elem}.png")).convert("RGB")
    a=np.asarray(im,float); H,W=a.shape[:2]
    lum=0.299*a[:,:,0]+0.587*a[:,:,1]+0.114*a[:,:,2]
    # central circular region = the disc holding the symbol (avoid hex frame)
    cy,cx=H/2,W/2; R=min(H,W)*0.30
    yy,xx=np.ogrid[:H,:W]
    circ=((yy-cy)**2+(xx-cx)**2)<=R*R
    bright=np.percentile(lum[circ],75)
    thr=bright*0.50
    mask=(lum<thr)&circ
    if mask.sum()<30: return None
    ys,xs=np.where(mask)
    y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    pad=6; y0=max(0,y0-pad); x0=max(0,x0-pad); y1=min(H,y1+pad); x1=min(W,x1+pad)
    sub=mask[y0:y1,x0:x1].astype(np.uint8)*255
    alpha=Image.fromarray(sub).filter(ImageFilter.GaussianBlur(0.6))
    out=np.zeros((sub.shape[0],sub.shape[1],4),np.uint8)
    out[:,:,3]=np.asarray(alpha)            # black glyph, soft edge
    Image.fromarray(out).save(os.path.join(ELEMDIR,f"symbol_{elem}.png"))
    return Image.fromarray(out)

# montage on light bg to verify
cell=160; m=Image.new("RGB",(cell*7,cell+24),(230,230,230))
from PIL import ImageDraw,ImageFont
d=ImageDraw.Draw(m)
try: f=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",16)
except: f=ImageFont.load_default()
for i,e in enumerate(ELEMS):
    g=extract(e)
    if g:
        g2=g.copy(); g2.thumbnail((cell-30,cell-30))
        # paint glyph black for preview
        blk=Image.new("RGBA",g2.size,(20,20,20,255)); blk.putalpha(g2.getchannel("A"))
        m.paste(blk,(i*cell+15,12),blk)
    d.text((i*cell+cell//2,cell+6),e,font=f,fill=(40,40,40),anchor="ma")
m.save("/Users/blu/card-borders/poker-deck/_symbols_montage.png")
print("symbols extracted ->", ELEMDIR, "| montage _symbols_montage.png")
