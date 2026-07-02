#!/usr/bin/env python3
"""V2 element emblems — clean 'vector-built' recreation, ~100% faithful:
  - crisp geometric hexagon frame (same orientation as the originals, th=58deg)
  - radial-gradient circular disc in the element color
  - the ORIGINAL glyph (drop/sprout/tornado/flame/wheel/triangle/yin-yang),
    re-smoothed from its mask: upscale -> blur -> threshold -> AA downsample
Outputs elements/v2/emblem_<elem>.png (768px, transparent) + _emblems-v2.png montage.
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT="/Users/blu/card-borders/poker-deck"
ELEMDIR=os.path.join(ROOT,"elements"); V2=os.path.join(ELEMDIR,"v2"); os.makedirs(V2,exist_ok=True)
HEX={"water":"#1c6baf","wood":"#85dc7b","electric":"#d3cf61","fire":"#c22c37","metal":"#c9ccd2","earth":"#684a36","spirit":"#64318f"}
ORDER=["water","wood","electric","fire","metal","earth","spirit"]
S=768; SS=3; W=S*SS; TH=math.radians(58)   # same orientation the originals were traced at
def hx(h): h=h.lstrip("#"); return np.array([int(h[i:i+2],16) for i in (0,2,4)],float)
def mix(a,b,t): return a*(1-t)+b*t

def hexpoly(cx,cy,r,th=TH):
    return [(cx+r*math.cos(th+k*math.pi/3), cy+r*math.sin(th+k*math.pi/3)) for k in range(6)]

def build(elem):
    col=hx(HEX[elem]); dark=np.array([21,22,26],float)
    cx=cy=W/2; R=W*0.465
    # --- frame: dark hexagon, tinted; crisp light rim + subtle inner bevel
    img=Image.new("RGBA",(W,W),(0,0,0,0)); d=ImageDraw.Draw(img)
    frame_col=tuple(int(v) for v in mix(dark,col,0.16))+(255,)
    d.polygon(hexpoly(cx,cy,R),fill=frame_col)
    d.line(hexpoly(cx,cy,R*0.995)+[hexpoly(cx,cy,R*0.995)[0]],fill=(216,212,200,255),width=int(W*0.010))
    d.line(hexpoly(cx,cy,R*0.90)+[hexpoly(cx,cy,R*0.90)[0]],fill=tuple(int(v) for v in mix(col,np.array([255]*3,float),0.35))+(90,),width=int(W*0.006))
    # --- disc: radial gradient (light toward top-left)
    discR=R*0.645
    yy,xx=np.mgrid[0:W,0:W]
    fx,fy=cx-discR*0.42, cy-discR*0.45
    dist=np.hypot(xx-fx,yy-fy)/(discR*1.55)
    g=np.clip(1.0-dist,0,1)**1.25
    lo=mix(col,dark,0.45); hi=mix(col,np.array([255]*3,float),0.42)
    grad=(lo[None,None,:]+(hi-lo)[None,None,:]*g[...,None]).astype(np.uint8)
    mask=Image.new("L",(W,W),0); ImageDraw.Draw(mask).ellipse([cx-discR,cy-discR,cx+discR,cy+discR],fill=255)
    disc=Image.fromarray(np.dstack([grad,np.array(mask)]))
    img.alpha_composite(disc)
    # thin dark ring around disc
    d=ImageDraw.Draw(img)
    d.ellipse([cx-discR,cy-discR,cx+discR,cy+discR],outline=tuple(int(v) for v in mix(dark,col,0.25))+(255,),width=int(W*0.008))
    # --- glyph: original mask, smoothed
    sp=os.path.join(ELEMDIR,f"symbol_{elem}.png")
    a=Image.open(sp).convert("RGBA").getchannel("A"); bb=a.getbbox(); a=a.crop(bb)
    BLUR={"metal":2.2,"spirit":2.2,"earth":3.5}.get(elem,5.5)   # thin-featured glyphs need gentler smoothing
    big=a.resize((a.width*6,a.height*6),Image.LANCZOS).filter(ImageFilter.GaussianBlur(BLUR))
    smooth=big.point(lambda v:255 if v>118 else 0).filter(ImageFilter.GaussianBlur(1.6))
    tgt=int(discR*2*0.74); sc=tgt/max(smooth.size)
    gm=smooth.resize((max(1,int(smooth.width*sc)),max(1,int(smooth.height*sc))),Image.LANCZOS)
    gx,gy=int(cx-gm.width/2),int(cy-gm.height/2)
    hi_g=Image.new("RGBA",gm.size,(255,255,255,110)); hi_g.putalpha(gm.point(lambda v:int(v*0.42)))
    dk_g=Image.new("RGBA",gm.size,(16,14,18,255));   dk_g.putalpha(gm)
    img.alpha_composite(hi_g,(gx-int(W*0.006),gy-int(W*0.008)))   # top-left highlight lip
    img.alpha_composite(dk_g,(gx,gy))
    out=img.resize((S,S),Image.LANCZOS)
    out.save(os.path.join(V2,f"emblem_{elem}.png"))
    return out

try: F=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",16)
except: F=ImageFont.load_default()
cell=200
mont=Image.new("RGB",(cell*7,cell+26),(40,40,44)); md=ImageDraw.Draw(mont)
for i,e in enumerate(ORDER):
    g=build(e); t=g.copy(); t.thumbnail((cell-12,cell-12))
    mont.paste(t,(i*cell+6,6),t); md.text((i*cell+cell//2,cell+6),e,font=F,fill=(225,220,210),anchor="ma")
mont.save(os.path.join(ROOT,"_emblems-v2.png"))
print("v2 emblems ->",V2,"| montage _emblems-v2.png")
