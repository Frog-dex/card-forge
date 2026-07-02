#!/usr/bin/env python3
"""Card borders from the REAL coded site assets: marble gloss + real faction
palette pulled from spiritstriker.app. Recolors the actual marble sphere into
each faction color and renders a polished marble frame. Same output format as
build_poker_borders.py (PNG + BGRA + borders_manifest.json)."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter

DPI=600; W,H=1650,2250; BLEED=75; SAFE=75
TRIM=(BLEED,BLEED,W-BLEED,H-BLEED); SAFEB=(BLEED+SAFE,BLEED+SAFE,W-BLEED-SAFE,H-BLEED-SAFE)
TRIM_R=84; BORDER=44
WIN=(BLEED+BORDER,BLEED+BORDER,W-BLEED-BORDER,H-BLEED-BORDER); WIN_R=60
SS=2
OUT="/Users/blu/card-borders/poker-deck/borders"
ASSET="/Users/blu/card-borders/poker-deck/site-assets"
os.makedirs(OUT,exist_ok=True)

# Element palette sampled from the canonical gem sheet fbn-0543.jpg
# (metal is white #ededec in the sheet; darkened here to a silver->near-black
#  gunmetal so the border reads, per Blu)
ELEMENTS={
 "fire":     ("Fire - Lizard","#c22c37"),
 "water":    ("Water - Frog","#1c6baf"),
 "wood":     ("Wood - Monkey","#85dc7b"),
 "electric": ("Electric - Bee","#d3cf61"),
 "earth":    ("Earth - Rockfish","#684a36"),
 "spirit":   ("Spirit - Dragon","#64318f"),
 "metal":    ("Metal - Crow","#5a6068"),
}
def hx(h): h=h.lstrip("#"); return np.array([int(h[i:i+2],16) for i in (0,2,4)],float)
def shade(c,f): return c*(1-f)
def light(c,f): return c+(255-c)*f

def frame_mask():
    w,h=W*SS,H*SS
    outer=Image.new("L",(w,h),255)
    win=Image.new("L",(w,h),0)
    ImageDraw.Draw(win).rounded_rectangle([WIN[0]*SS,WIN[1]*SS,WIN[2]*SS-1,WIN[3]*SS-1],radius=WIN_R*SS,fill=255)
    return ImageChops.subtract(outer,win).resize((W,H),Image.LANCZOS)
def window_mask_img():
    w,h=W*SS,H*SS
    win=Image.new("L",(w,h),0)
    ImageDraw.Draw(win).rounded_rectangle([WIN[0]*SS,WIN[1]*SS,WIN[2]*SS-1,WIN[3]*SS-1],radius=WIN_R*SS,fill=255)
    return win.resize((W,H),Image.LANCZOS)
MASK=frame_mask(); Mf=np.asarray(MASK,float)/255.0

xs=np.linspace(0,1,W); ys=np.linspace(0,1,H)
Y,X=np.meshgrid(ys,xs,indexing="ij")
def blur(a,r):
    im=Image.fromarray(((a-a.min())/(np.ptp(a)+1e-9)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im,float)/255.0-0.5

def marble_field(seed):
    """polished marble gloss: top-left light + specular streak + soft veining."""
    rng=np.random.default_rng(seed)
    L=(1-Y)*0.6+(1-X)*0.4
    F=(L-0.5)*1.4
    F+=0.75*np.exp(-((Y-0.10)/0.06)**2)+0.30*np.exp(-((X-0.16)/0.08)**2)   # specular
    F+=blur(rng.normal(0,1,(H,W)),14)*0.55+blur(rng.normal(0,1,(H,W)),3)*0.18  # veins
    return np.clip(F-0.08,-1,1.2)

def ramp(F,sh,mid,hi):
    Fp=np.clip(F,0,1)[...,None]; Fn=np.clip(-F,0,1)[...,None]
    return np.clip(mid[None,None,:]+(hi-mid)[None,None,:]*Fp+(sh-mid)[None,None,:]*Fn,0,255)
def bgra(im):
    a=np.array(im.convert("RGBA")); return a[:,:,[2,1,0,3]].tobytes()

# recolor the REAL marble sphere into each faction color (luminance -> color ramp)
msrc=Image.open(os.path.join(ASSET,"marble_g_01.png")).convert("RGBA")
ma=np.asarray(msrc,float); mlum=(0.299*ma[:,:,0]+0.587*ma[:,:,1]+0.114*ma[:,:,2])/255.0
malpha=ma[:,:,3]

manifest={"canvas":[W,H],"dpi":DPI,"bleed":BLEED,"safe":SAFE,"trim":TRIM,"safebox":SAFEB,
          "window":WIN,"win_r":WIN_R,"source":"spiritstriker.app real coded assets","elements":{}}

marble_strip=Image.new("RGBA",(120*7,140),(0,0,0,0))
for idx,(key,(name,mid)) in enumerate(ELEMENTS.items()):
    m=hx(mid); sh=shade(m,0.58); hi=light(m,0.62)
    # border = marble gloss in faction color
    F=marble_field(11+idx)
    col=ramp(F,sh,m,hi)
    rgba=np.dstack([col,Mf*255]).astype(np.uint8)
    im=Image.fromarray(rgba)
    im.save(os.path.join(OUT,f"border_{key}.png"))
    open(os.path.join(OUT,f"border_{key}.bgra"),"wb").write(bgra(im))
    manifest["elements"][key]={"name":name,"style":"marble","hex":mid,"file":f"border_{key}.bgra"}
    # recolored real marble sphere swatch
    mcol=np.clip(m[None,None,:]*0.35+(hi-m)[None,None,:]*np.clip(mlum*1.4-0.2,0,1)[...,None]+m[None,None,:]*0.65,0,255)
    mcol=ramp((mlum-0.5)*2.2,sh,m,hi)
    sw=Image.fromarray(np.dstack([mcol,malpha]).astype(np.uint8))
    sw.save(os.path.join(OUT,f"marble_{key}.png"))
    marble_strip.alpha_composite(sw.resize((120,120)),(idx*120,10))
    print("marble border",key,mid)

win=window_mask_img(); wf=np.asarray(win,float)/255.0
wbase=np.zeros((H,W,4),np.uint8); wbase[:,:,0]=38;wbase[:,:,1]=37;wbase[:,:,2]=44;wbase[:,:,3]=(wf*255).astype(np.uint8)
Image.fromarray(wbase).save(os.path.join(OUT,"window_base.png"))
open(os.path.join(OUT,"window_base.bgra"),"wb").write(wbase[:,:,[2,1,0,3]].tobytes())

g=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(g)
d.rounded_rectangle([TRIM[0],TRIM[1],TRIM[2]-1,TRIM[3]-1],radius=TRIM_R,outline=(255,0,200,255),width=4)
d.rounded_rectangle([SAFEB[0],SAFEB[1],SAFEB[2]-1,SAFEB[3]-1],radius=max(0,TRIM_R-SAFE),outline=(0,220,255,255),width=3)
d.rounded_rectangle([WIN[0],WIN[1],WIN[2]-1,WIN[3]-1],radius=WIN_R,outline=(255,220,0,200),width=2)
g.save(os.path.join(OUT,"guides.png")); open(os.path.join(OUT,"guides.bgra"),"wb").write(bgra(g))

marble_strip.save(os.path.join(OUT,"_marble_swatches.png"))
json.dump(manifest,open(os.path.join(OUT,"borders_manifest.json"),"w"),indent=2)
print("MARBLE BORDERS DONE")
