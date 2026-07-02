#!/usr/bin/env python3
"""Pack 49 fully-lit faction marbles (one per card) into raw BGRA + manifest for a
layered .kra that Blu paints on. NO engraved glyph — these are clean lit glass orbs;
the lighting/shadow/color already match each card's faction border. Blu draws his own
art on the inherit-alpha layer above each.

Layout: 7x7 grid, one marble per cell, each big enough to paint (480px).
Output: _kra49/<nn>_<elem>.bgra  +  manifest.json  +  bg.bgra  + flat preview PNG.
Then build_49_marble_kra.py (kritarunner) turns the manifest into the .kra.
"""
import os, json
import numpy as np
from PIL import Image
from marble_render import render_marble, card_seed, load_manifest

ROOT = "/Users/blu/card-borders/poker-deck"
OUT  = os.path.join(ROOT, "_kra49"); os.makedirs(OUT, exist_ok=True)

MARB, PAD = 480, 60
CELL = MARB + PAD
COLS = ROWS = 7
CW = CH = COLS * CELL                      # 3780 x 3780
AMP, BANDS = 0.22, 2.8                     # locked middle intensity (matches the deck)
BG = (28, 27, 33)                          # dark working fill (toggle off for transparency)

elements = load_manifest()["elements"]
plan = json.load(open(os.path.join(ROOT, "plan.json")))["cells"]

# background BGRA
bgarr = np.zeros((CH, CW, 4), np.uint8)
bgarr[:, :, 0] = BG[2]; bgarr[:, :, 1] = BG[1]; bgarr[:, :, 2] = BG[0]; bgarr[:, :, 3] = 255
with open(os.path.join(OUT, "bg.bgra"), "wb") as f:
    f.write(bgarr.tobytes())

man = {"canvas": [CW, CH], "resolution": 300,
       "bg": {"file": "bg.bgra", "w": CW, "h": CH}, "marbles": []}
preview = Image.new("RGBA", (CW, CH), (BG[0], BG[1], BG[2], 255))

for cell in sorted(plan, key=lambda x: x["num"]):
    num, elem = cell["num"], cell["element"]
    r, c = divmod(num - 1, COLS)
    x = c * CELL + PAD // 2
    y = r * CELL + PAD // 2
    orb = render_marble(elements[elem]["hex"], card_seed(num, 0),
                        size=MARB, swirl_amp=AMP, swirl_bands=BANDS)   # clean lit orb, no glyph
    slug = "%02d_%s" % (num, elem)
    a = np.array(orb)[:, :, [2, 1, 0, 3]]                              # RGBA -> BGRA for Krita
    with open(os.path.join(OUT, slug + ".bgra"), "wb") as f:
        f.write(a.tobytes())
    man["marbles"].append({"name": "%02d %s" % (num, elem), "file": slug + ".bgra",
                           "x": int(x), "y": int(y), "w": MARB, "h": MARB})
    preview.alpha_composite(orb, (x, y))

with open(os.path.join(OUT, "manifest.json"), "w") as f:
    json.dump(man, f)
preview.convert("RGB").save(os.path.join(ROOT, "_PAINT49_preview.png"))
print("packed", len(man["marbles"]), "marbles ->", OUT)
print("preview -> _PAINT49_preview.png", preview.size)
