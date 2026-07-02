#!/usr/bin/env python3
"""Spirit Strikers poker borders @ 600 DPI with 1/8in bleed.
Full-bleed colored bespoke frame + rounded art window. Outputs PNG + raw BGRA
(+ manifest) for the kritarunner card assembler. Adapted from build_bespoke.py.
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter

DPI = 600
W, H = 1650, 2250          # 2.75 x 3.75 in  (2.5x3.5 trim + 1/8in bleed)
BLEED = 75                 # 1/8in @600  -> trim box (75,75)-(1575,2175)=1500x2100
SAFE  = 75                 # 1/8in inside trim -> safe (150,150)-(1500,2100)
TRIM  = (BLEED, BLEED, W-BLEED, H-BLEED)
SAFEB = (BLEED+SAFE, BLEED+SAFE, W-BLEED-SAFE, H-BLEED-SAFE)
TRIM_R = 84                # card corner radius @600 (~0.14in)
BORDER = 44                # visible border width inside trim (thin frame)
WIN = (BLEED+BORDER, BLEED+BORDER, W-BLEED-BORDER, H-BLEED-BORDER)  # art window
WIN_R = 60
SS = 2

OUT = "/Users/blu/card-borders/poker-deck/borders"
os.makedirs(OUT, exist_ok=True)

# element key -> (display, style, shadow, mid, highlight)
ELEMENTS = {
 "fire":     ("Fire - Lizard","flame",  "#5e0f1e","#e0264c","#ffcf4a"),
 "water":    ("Water - Frog","aqua",    "#06382a","#1c8a3e","#cffaea"),
 "wood":     ("Wood - Monkey","crystal","#0e1f55","#2b54d6","#dce9ff"),
 "electric": ("Electric - Bee","molten","#7a4f00","#f4c20d","#fff3c0"),
 "earth":    ("Earth - Rockfish","stone","#33200c","#a86a36","#e6c79a"),
 "spirit":   ("Spirit - Dragon","nebula","#1f0a3e","#8b34b8","#f7d0ff"),
 "metal":    ("Metal - Crow","chrome",  "#1f2530","#5b6b82","#eef2f7"),
}

def hx(h): h=h.lstrip("#"); return np.array([int(h[i:i+2],16) for i in (0,2,4)],float)

def frame_mask():
    """full-bleed outer rectangle MINUS rounded art window."""
    w,h = W*SS, H*SS
    outer = Image.new("L",(w,h),255)                       # ink to the very edge (bleed)
    win = Image.new("L",(w,h),0)
    ImageDraw.Draw(win).rounded_rectangle(
        [WIN[0]*SS, WIN[1]*SS, WIN[2]*SS-1, WIN[3]*SS-1], radius=WIN_R*SS, fill=255)
    band = ImageChops.subtract(outer, win)
    return band.resize((W,H), Image.LANCZOS)

def window_mask_img():
    w,h = W*SS, H*SS
    win = Image.new("L",(w,h),0)
    ImageDraw.Draw(win).rounded_rectangle(
        [WIN[0]*SS, WIN[1]*SS, WIN[2]*SS-1, WIN[3]*SS-1], radius=WIN_R*SS, fill=255)
    return win.resize((W,H), Image.LANCZOS)

MASK = frame_mask(); Mf = np.asarray(MASK,float)/255.0

xs=np.linspace(0,1,W); ys=np.linspace(0,1,H)
Y,X=np.meshgrid(ys,xs,indexing="ij")
cxd=np.minimum(X,1-X); cyd=np.minimum(Y,1-Y)
CORNER=np.exp(-(cxd/0.11)**2)*np.exp(-(cyd/0.15)**2)*(1.0-0.45*Y)
BOTTOM=np.exp(-((1-Y)/0.09)**2)
TOPG=np.clip((0.34-Y)/0.34,0,1)**1.7

def blur(a,r):
    im=Image.fromarray(((a-a.min())/(np.ptp(a)+1e-9)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im,float)/255.0-0.5
def soft(a,r):
    im=Image.fromarray(np.clip((a+1)*127.5,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im,float)/127.5-1.0
def softw(mask,r,amp=5.0):
    im=Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.clip(np.asarray(im,float)/255.0*amp,0,1)

def field(style, seed):
    rng=np.random.default_rng(seed)
    sp=(rng.random((H,W))>0.994).astype(float)-(rng.random((H,W))>0.994).astype(float)
    flake=soft(sp,1.6)*0.55 + rng.normal(0,1,(H,W))*0.015
    if style=="chrome":
        peaks=[(0.07,0.45,0.02),(0.16,0.85,0.03),(0.31,0.33,0.018),(0.50,1.05,0.05),(0.64,0.42,0.022),(0.78,0.66,0.028),(0.90,0.5,0.02)]
        spec=sum(a*np.exp(-((xs-p)/w)**2) for p,a,w in peaks)
        Fx=-0.34+0.36*np.sin(np.pi*xs)+spec+np.convolve(rng.normal(0,1,W),np.ones(5)/5,"same")*0.05
        F=np.tile(Fx,(H,1)); F+=(Y-0.5)*0.35+0.45*np.exp(-((Y-0.55)/0.05)**2); g,c,b,fk=0.35,0.55,0.30,0.9
    elif style=="molten":
        spec=sum(a*np.exp(-((xs-p)/w)**2) for p,a,w in [(0.18,0.7,0.04),(0.5,1.0,0.05),(0.8,0.6,0.04)])
        F=np.tile(-0.30+0.34*np.sin(np.pi*xs)+spec,(H,1))+blur(rng.normal(0,1,(H,W)),16)*0.55+0.10*(0.5-Y); g,c,b,fk=0.42,0.55,0.46,0.85
    elif style=="flame":
        licks=np.tile(np.convolve(rng.normal(0,1,W),np.ones(7)/7,"same"),(H,1))*0.38
        F=-0.2+0.3*np.sin(np.pi*X)+licks+(Y-0.5)*0.65+blur(rng.normal(0,1,(H,W)),9)*0.45; g,c,b,fk=0.20,0.45,0.55,0.6
    elif style=="aqua":
        ripple=0.55*np.exp(-((Y-0.16)/0.05)**2)+0.4*np.exp(-((Y-0.48)/0.11)**2)+0.3*np.exp(-((Y-0.8)/0.06)**2)
        F=-0.25+0.30*np.sin(np.pi*X)+ripple+(0.5-Y)*0.30+blur(rng.normal(0,1,(H,W)),20)*0.28; g,c,b,fk=0.55,0.55,0.45,0.45
    elif style=="crystal":
        diag=0.5*X+0.5*Y; anti=0.5*(X-Y)+0.5
        facet=(0.9*np.exp(-((diag-0.28)/0.032)**2)+0.65*np.exp(-((diag-0.6)/0.042)**2)
              +0.55*np.exp(-((anti-0.4)/0.038)**2)+0.4*np.exp(-((anti-0.74)/0.048)**2))
        F=-0.2+0.2*np.sin(np.pi*X)+facet; g,c,b,fk=0.40,0.55,0.36,0.7
    elif style=="stone":
        gr=blur(rng.normal(0,1,(H,W)),2)*0.8+blur(rng.normal(0,1,(H,W)),5)*0.5
        F=-0.06+0.10*np.sin(np.pi*X)+gr; g,c,b,fk=0.08,0.32,0.22,0.40
    elif style=="nebula":
        r=np.sqrt((X-0.5)**2+((Y-0.5)*1.6)**2)
        F=-0.15+(0.5-r)*0.7+blur(rng.normal(0,1,(H,W)),22)*0.7+blur(rng.normal(0,1,(H,W)),7)*0.35; g,c,b,fk=0.30,0.45,0.40,0.5
    F=F+TOPG*g+CORNER*c+BOTTOM*b+flake*fk
    return np.clip(F,-1,1.25)

def ramp(F, shadow, mid, hi):
    Fp=np.clip(F,0,1)[...,None]; Fn=np.clip(-F,0,1)[...,None]
    return np.clip(mid[None,None,:]+(hi-mid)[None,None,:]*Fp+(shadow-mid)[None,None,:]*Fn,0,255)

def bgra(im):
    a=np.array(im.convert("RGBA")); return a[:,:,[2,1,0,3]].tobytes()

manifest={"canvas":[W,H],"dpi":DPI,"bleed":BLEED,"safe":SAFE,"trim":TRIM,"safebox":SAFEB,
          "window":WIN,"win_r":WIN_R,"elements":{}}

for idx,(key,(name,style,sh,mid,hi)) in enumerate(ELEMENTS.items()):
    F=field(style, 7+idx)
    col=ramp(F, hx(sh), hx(mid), hx(hi))
    r2=np.random.default_rng(200+idx)
    bdens=0.996 if style=="nebula" else 0.9986
    bw=softw(r2.random((H,W))>bdens,1.4)[...,None]
    col=col*(1-bw*0.50)+np.clip(hx(hi)*1.05,0,255)[None,None,:]*(bw*0.50)
    ddens=0.992 if style=="stone" else 0.9988
    dw=softw(r2.random((H,W))>ddens,1.7)[...,None]
    col=col*(1-dw*0.45)+np.clip(hx(sh)*1.2,0,255)[None,None,:]*(dw*0.45)
    rgba=np.dstack([col, Mf*255]).astype(np.uint8)
    im=Image.fromarray(rgba)
    im.save(os.path.join(OUT,f"border_{key}.png"))
    open(os.path.join(OUT,f"border_{key}.bgra"),"wb").write(bgra(im))
    manifest["elements"][key]={"name":name,"style":style,"hex":mid,"file":f"border_{key}.bgra"}
    print("border",key,style)

# window base (clip shape for the art-paint inherit-alpha layer): faint neutral fill
win = window_mask_img()
wf = np.asarray(win,float)/255.0
wbase = np.zeros((H,W,4),np.uint8)
wbase[:,:,0]=38; wbase[:,:,1]=37; wbase[:,:,2]=44       # near-panel dark
wbase[:,:,3]=(wf*255).astype(np.uint8)
Image.fromarray(wbase).save(os.path.join(OUT,"window_base.png"))
open(os.path.join(OUT,"window_base.bgra"),"wb").write(wbase[:,:,[2,1,0,3]].tobytes())

# guides: trim (magenta) + safe (cyan) + window (yellow) thin outlines on transparent
g=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(g)
d.rounded_rectangle([TRIM[0],TRIM[1],TRIM[2]-1,TRIM[3]-1],radius=TRIM_R,outline=(255,0,200,255),width=4)
d.rounded_rectangle([SAFEB[0],SAFEB[1],SAFEB[2]-1,SAFEB[3]-1],radius=max(0,TRIM_R-SAFE),outline=(0,220,255,255),width=3)
d.rounded_rectangle([WIN[0],WIN[1],WIN[2]-1,WIN[3]-1],radius=WIN_R,outline=(255,220,0,200),width=2)
g.save(os.path.join(OUT,"guides.png"))
open(os.path.join(OUT,"guides.bgra"),"wb").write(bgra(g))

json.dump(manifest,open(os.path.join(OUT,"borders_manifest.json"),"w"),indent=2)
print("BORDERS DONE", W, "x", H, "@", DPI, "dpi")
