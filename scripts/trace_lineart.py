#!/usr/bin/env python3
"""Vectorize the card line art (potrace) and render it crisp at card resolution.
mask -> potrace curves -> bezier tessellation -> XOR parity fill at 2x supersample
-> optional uniform thinning. Kills upscale pixelation + fat lines at the root.
CLI: trace_lineart.py <card-id> [thin_px]  -> writes _VECTOR-compare-<id>.png
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import potrace
from scipy import ndimage

CUT="/Users/blu/spirit-strikers-deck/images/cards-bw-cutout"
ROOT="/Users/blu/card-borders/poker-deck"

def bez(p0,p1,p2,p3,n=16):
    t=np.linspace(0,1,n)[:,None]
    return ((1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t**2*p2+t**3*p3)

def trace_mask(mask):
    """binary mask (H,W) -> list of closed polygons (numpy Nx2, source coords)"""
    bmp=potrace.Bitmap(mask.astype(bool))   # potracer REQUIRES bool; uint8 0/1 collapses to one block
    path=bmp.trace(turdsize=3, alphamax=1.0, opttolerance=0.2)
    polys=[]
    P=lambda pt: np.array([pt.x,pt.y],float)
    for curve in path:
        pts=[]
        prev=P(curve.start_point)
        for seg in curve:
            if seg.is_corner:
                pts.append(P(seg.c)); pts.append(P(seg.end_point))
                prev=P(seg.end_point)
            else:
                p=bez(prev,P(seg.c1),P(seg.c2),P(seg.end_point))
                pts.extend(list(p)); prev=P(seg.end_point)
        polys.append(np.array(pts))
    return polys

def render_vector(cutout_alpha, target_w, target_h, thin_px=0, ss=2):
    """render traced line art at target size; XOR parity fill handles holes."""
    src_h,src_w=cutout_alpha.shape
    mask=cutout_alpha>90
    polys=trace_mask(mask)
    sx,sy=target_w*ss/src_w, target_h*ss/src_h
    acc=np.zeros((target_h*ss,target_w*ss),bool)
    for poly in polys:
        if len(poly)<3: continue
        im=Image.new("1",(target_w*ss,target_h*ss),0)
        ImageDraw.Draw(im).polygon([(float(x*sx),float(y*sy)) for x,y in poly],fill=1)
        acc^=np.array(im,bool)
    if acc[0,0] or acc.mean()>0.6:      # parity landed inverted -> flip (corner is never a stroke)
        acc=~acc
    if thin_px>0:
        acc=ndimage.binary_erosion(acc,iterations=thin_px*ss)
    out=Image.fromarray((acc*255).astype(np.uint8)).resize((target_w,target_h),Image.LANCZOS)
    return out   # L-mode anti-aliased mask

def compare(cid, thin=0):
    cut=Image.open(f"{CUT}/{cid}.png").convert("RGBA")
    al=np.array(cut.getchannel("A"))
    # target: art at ~90% of card window (like the real pipeline)
    winW,winH=1462,2062
    s=min(winW*0.9/cut.width, winH*0.9/cut.height)
    tw,th=int(cut.width*s),int(cut.height*s)
    # OLD: raw upscale of the tiny cutout
    old=cut.getchannel("A").resize((tw,th),Image.LANCZOS)
    # NEW: vector-traced render (+ optional thinning)
    new=render_vector(al,tw,th,thin_px=thin)
    # side-by-side on white, black ink
    pad=30; W=tw*2+pad*3; H=th+90
    sheet=Image.new("RGB",(W,H),(255,255,255)); d=ImageDraw.Draw(sheet)
    try: f=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf",30)
    except: f=ImageFont.load_default()
    for i,(m,lab) in enumerate([(old,"CURRENT (pixel upscale)"),(new,f"VECTOR-TRACED (thin={thin})")]):
        ink=Image.new("RGBA",(tw,th),(15,15,15,255)); ink.putalpha(m)
        x=pad+i*(tw+pad); sheet.paste(ink,(x,70),ink)
        d.text((x+tw//2,20),lab,font=f,fill=(30,30,30),anchor="ma")
    out=f"{ROOT}/_VECTOR-compare-{cid}.png"; sheet.save(out); print("wrote",out,sheet.size)

if __name__=="__main__":
    cid=sys.argv[1] if len(sys.argv)>1 else "card-14"
    thin=int(sys.argv[2]) if len(sys.argv)>2 else 0
    compare(cid,thin)
