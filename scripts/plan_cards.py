#!/usr/bin/env python3
"""Build the 49-cell (7 category x 7 element) plan and precompute placed art BGRA.
Each card is colored by ITS element; blanks fill remaining cells colored by the
column element. Writes plan.json + art/<id>.bgra for the assembler."""
import os, json, struct
import numpy as np
from PIL import Image

ROOT = "/Users/blu/card-borders/poker-deck"
ARTSRC = "/Users/blu/spirit-strikers-deck/images/cards-vector"    # vector-traced crisp line art (bake_vector_art.py)
ARTSRC_FALLBACK = "/Users/blu/spirit-strikers-deck/images/cards-bw-cutout"
ARTOUT = os.path.join(ROOT, "art"); os.makedirs(ARTOUT, exist_ok=True)
ELEMDIR = os.path.join(ROOT, "elements")   # the 7 gem emblems cropped from fbn-0543.jpg
_catpaths = ["/Users/blu/card-borders/poker-deck/card-categories.json",
             "/Users/blu/Downloads/spirit-strikers-card-categories.json"]
CATS = json.load(open(next(p for p in _catpaths if os.path.exists(p))))
PLANS = json.load(open("/Users/blu/spirit-strikers-deck/content/card-plans.json"))
BM = json.load(open(os.path.join(ROOT, "borders/borders_manifest.json")))
WIN = BM["window"]; W,H = BM["canvas"]
winW, winH = WIN[2]-WIN[0], WIN[3]-WIN[1]

ELEM_ORDER = ["water","wood","electric","fire","metal","earth","spirit"]  # fixed columns 1-7 (Blu, 06-29 reorder)
HEX = {k: BM["elements"][k]["hex"] for k in ELEM_ORDER}
ROW_ORDER = ["Characters","Locations","Vehicles","Relics","Story Elements","Motives","Elements"]

# card -> element from faction keywords (+ manual fills for unknowns)
KW = {"bee":"electric","lizard":"fire","frog":"water","monkey":"wood",
      "dragon":"spirit","crow":"metal","rockfish":"earth"}
MANUAL = {"card-06":"water","card-09":"water","card-23":"earth"}
def elem_of(cid):
    if cid in MANUAL: return MANUAL[cid]
    rec = next((c for c in PLANS if c["card"]==cid), None)
    if rec:
        t=(rec.get("subject","")+" "+" ".join(rec.get("symbols",[]))).lower()
        for k,e in KW.items():
            if k in t: return e
    return "spirit"

def fit_art(cid):
    """resize card art into ~88% of window, centered; return (bgra_file,x,y,w,h)."""
    p=os.path.join(ARTSRC, cid+".png")
    if not os.path.exists(p): p=os.path.join(ARTSRC_FALLBACK, cid+".png")
    if not os.path.exists(p): return None
    im=Image.open(p).convert("RGBA")
    aw,ah=im.size
    s=min((winW*0.9)/aw,(winH*0.9)/ah)
    nw,nh=max(1,int(aw*s)),max(1,int(ah*s))
    im=im.resize((nw,nh),Image.LANCZOS)
    x=WIN[0]+(winW-nw)//2; y=WIN[1]+(winH-nh)//2
    a=np.array(im)[:,:,[2,1,0,3]].tobytes()
    fn=f"{cid}.bgra"; open(os.path.join(ARTOUT,fn),"wb").write(a)
    return {"file":fn,"x":int(x),"y":int(y),"w":nw,"h":nh}

def fit_emblem(elem):
    """gem emblem -> near-black bg made transparent, fit into ~72% of window."""
    p=os.path.join(ELEMDIR,f"emblem_{elem}.png")
    if not os.path.exists(p): return None
    im=Image.open(p).convert("RGBA")   # use the emblem's cleaned hexagon alpha as-is (don't re-derive from RGB)
    aw,ah=im.size
    s=min((winW*0.72)/aw,(winH*0.72)/ah)
    nw,nh=max(1,int(aw*s)),max(1,int(ah*s))
    im=im.resize((nw,nh),Image.LANCZOS)
    x=WIN[0]+(winW-nw)//2; y=WIN[1]+(winH-nh)//2
    fn=f"emblem_{elem}.bgra"; open(os.path.join(ARTOUT,fn),"wb").write(np.array(im)[:,:,[2,1,0,3]].tobytes())
    return {"file":fn,"x":int(x),"y":int(y),"w":nw,"h":nh}

plan=[]
for r,cat in enumerate(ROW_ORDER):
    ids = CATS.get(cat, [])
    slots=[None]*7                                  # one per element column
    overflow=[]
    for cid in ids:
        e=elem_of(cid); col=ELEM_ORDER.index(e)
        if slots[col] is None: slots[col]=(cid,e)
        else: overflow.append((cid,e))
    for cid,e in overflow:                          # park extras in lowest free column
        for c in range(7):
            if slots[c] is None: slots[c]=(cid,e); break
    for col in range(7):
        colelem=ELEM_ORDER[col]
        if slots[col]:
            cid,e=slots[col]
            art=fit_art(cid)
            plan.append({"row":r,"col":col,"category":cat,"element":colelem,"hex":HEX[colelem],
                "card":cid,"faction":e,"art":art,"blank":False,   # COLOR BY COLUMN (one of each per row)
                "label":f"{r+1}{col+1}_{cat.replace(' ','-')}_{colelem}_{cid}",
                "filename":f"SS_{r+1}{col+1}_{cat.replace(' ','-')}_{colelem}_{cid}.kra"})
        elif cat=="Elements":                                   # last row = the 7 element emblems
            plan.append({"row":r,"col":col,"category":cat,"element":colelem,"hex":HEX[colelem],
                "card":f"element-{colelem}","art":fit_emblem(colelem),"blank":False,
                "label":f"{r+1}{col+1}_Elements_{colelem}_EMBLEM",
                "filename":f"SS_{r+1}{col+1}_Elements_{colelem}_EMBLEM.kra"})
        else:
            plan.append({"row":r,"col":col,"category":cat,"element":colelem,"hex":HEX[colelem],
                "card":None,"art":None,"blank":True,
                "label":f"{r+1}{col+1}_{cat.replace(' ','-')}_{colelem}_BLANK",
                "filename":f"SS_{r+1}{col+1}_{cat.replace(' ','-')}_{colelem}_BLANK.kra"})

for i,c in enumerate(plan): c["num"]=i+1          # deck number 1..49 (row-major)
json.dump({"canvas":[W,H],"window":WIN,"rows":ROW_ORDER,"cols":ELEM_ORDER,"cells":plan},
          open(os.path.join(ROOT,"plan.json"),"w"),indent=2)
nfilled=sum(1 for c in plan if not c["blank"])
print(f"PLAN: {len(plan)} cells | {nfilled} filled | {len(plan)-nfilled} blank")
for r,cat in enumerate(ROW_ORDER):
    row=[c for c in plan if c["row"]==r]
    print(f"  {cat:14s} " + " ".join((c['card'] or '----').replace('card-','#') + ':' + c['element'][:3] for c in row))
