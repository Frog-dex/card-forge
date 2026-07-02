#!/usr/bin/env python3
"""Render a corner-number badge (full-canvas RGBA, TR+BL marbles with the deck
number inset) for every cell in plan.json. Saves BGRA for the kritarunner
assembler and updates plan.json with the badge filename."""
import os, json
import numpy as np
from corner_badges import make_badge, W, H

ROOT="/Users/blu/card-borders/poker-deck"
BADGES=os.path.join(ROOT,"badges"); os.makedirs(BADGES,exist_ok=True)
P=json.load(open(os.path.join(ROOT,"plan.json")))

for c in P["cells"]:
    img=make_badge(c["num"], c["element"])
    fn=f"badge_{c['num']:02d}.bgra"
    a=np.array(img)[:,:,[2,1,0,3]].tobytes()
    open(os.path.join(BADGES,fn),"wb").write(a)
    c["badge"]=fn

json.dump(P, open(os.path.join(ROOT,"plan.json"),"w"), indent=2)
print(f"badges: {len(P['cells'])} written to {BADGES}")
