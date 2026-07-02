#!/usr/bin/env python3
"""Re-crop the 7 element gems from fbn-0543.jpg showing the WHOLE hexagon
(earlier crop was too tight and clipped the hex corners). Near-black gaps ->
transparent. Saves elements/emblem_<elem>.png + _emblems_montage.png."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC="/tmp/fbn-0543.jpg"
if not os.path.exists(SRC):
    # re-fetch fallback handled by caller; assume present
    raise SystemExit("fbn-0543.jpg missing in /tmp — re-download first")
im=Image.open(SRC).convert("RGB")
W,Hh=im.size
arr=np.asarray(im)
GEMS={"fire":(0.50,0.13),"metal":(0.20,0.32),"electric":(0.80,0.33),"spirit":(0.50,0.46),
      "earth":(0.20,0.66),"wood":(0.80,0.66),"water":(0.50,0.83)}
OUT="/Users/blu/card-borders/poker-deck/elements"; os.makedirs(OUT,exist_ok=True)
half=int(0.168*W)     # wide enough for the full hexagon, just short of neighbours

def crop(elem,fx,fy):
    cx,cy=int(fx*W),int(fy*Hh)
    x0,y0=max(0,cx-half),max(0,cy-half); x1,y1=min(W,cx+half),min(Hh,cy+half)
    sub=arr[y0:y1,x0:x1].astype(np.uint8)
    h,w=sub.shape[:2]
    mx=sub.max(2).astype(float)
    alpha=np.clip((mx-26)/40*255,0,255).astype(np.uint8)   # near-black gaps -> transparent
    rgba=np.dstack([sub,alpha]).astype(np.uint8)
    Image.fromarray(rgba,"RGBA").save(os.path.join(OUT,f"emblem_{elem}.png"))
    return Image.fromarray(rgba,"RGBA")

cell=200; ORDER=["water","wood","metal","electric","fire","earth","spirit"]
m=Image.new("RGB",(cell*7,cell+26),(220,220,220)); d=ImageDraw.Draw(m)
try: f=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",16)
except: f=ImageFont.load_default()
for i,e in enumerate(ORDER):
    g=crop(e,*GEMS[e]); g2=g.copy(); g2.thumbnail((cell-16,cell-16))
    m.paste(g2,(i*cell+8,8),g2)
    d.text((i*cell+cell//2,cell+8),e,font=f,fill=(30,30,30),anchor="ma")
m.save("/Users/blu/card-borders/poker-deck/_emblems_montage.png")
print("emblems re-cropped (half=%d) -> %s ; montage _emblems_montage.png"%(half,OUT))
