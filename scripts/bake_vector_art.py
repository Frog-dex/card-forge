#!/usr/bin/env python3
"""Batch: vector-trace all 29 card cutouts and bake crisp high-res line art.
Output: /Users/blu/spirit-strikers-deck/images/cards-vector/card-NN.png
(RGBA, black ink + smooth alpha, 3x source size, uniform thinning:
 thin=3 for Locations scene cards, thin=2 for everything else)."""
import os, json, time
import numpy as np
from PIL import Image
from trace_lineart import render_vector

CUT="/Users/blu/spirit-strikers-deck/images/cards-bw-cutout"
OUT="/Users/blu/spirit-strikers-deck/images/cards-vector"; os.makedirs(OUT,exist_ok=True)
ROOT="/Users/blu/card-borders/poker-deck"

plan=json.load(open(os.path.join(ROOT,"plan.json")))
cat_of={c["card"]:c["category"] for c in plan["cells"] if c.get("card") and str(c["card"]).startswith("card-")}

t0=time.time(); done=[]
for fn in sorted(os.listdir(CUT)):
    if not fn.endswith(".png"): continue
    cid=fn[:-4]
    cut=Image.open(os.path.join(CUT,fn)).convert("RGBA")
    al=np.array(cut.getchannel("A"))
    thin=3 if cat_of.get(cid)=="Locations" else 2
    tw,th=cut.width*3,cut.height*3
    m=render_vector(al,tw,th,thin_px=thin)          # L-mode smooth mask
    ink=Image.new("RGBA",(tw,th),(15,15,15,255)); ink.putalpha(m)
    ink.save(os.path.join(OUT,fn))
    done.append((cid,thin,f"{tw}x{th}"))
    print(f"{cid} thin={thin} {tw}x{th} ({time.time()-t0:.0f}s)",flush=True)
print(f"BAKED {len(done)} vector art files -> {OUT} in {time.time()-t0:.0f}s")
