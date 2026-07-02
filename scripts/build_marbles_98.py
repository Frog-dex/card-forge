#!/usr/bin/env python3
"""Batch-render all 98 unique card marbles (49 cards x 2) as flat glossy PNGs.

top = element SYMBOL engraved   bottom = card NUMBER engraved
Each marble is procedurally lit + uniquely swirled (see MARBLE-RECIPE.md), then the
glyph is debossed in, and the result is saved baked/flat to  marbles/<num>_top|bot.png .

Locked style (Blu): swirl intensity = middle (amp 0.22 / bands 2.8), flat PNG output.
"""
import os, json
from PIL import Image, ImageDraw, ImageFont
from marble_render import render_marble, card_seed, load_manifest
import corner_badges as cb

ROOT = "/Users/blu/card-borders/poker-deck"
OUT  = os.path.join(ROOT, "marbles"); os.makedirs(OUT, exist_ok=True)
D    = cb.D                      # 286 — matches placement size (WYSIWYG, no resize)
AMP, BANDS = 0.22, 2.8           # locked middle intensity

manifest = load_manifest()["elements"]
plan = json.load(open(os.path.join(ROOT, "plan.json")))["cells"]

def engrave_symbol(marble, elem, base):
    """COLORED element symbol (light tint of the element), not a black engraving (Blu)."""
    p = os.path.join(cb.ELEMDIR, f"symbol_{elem}.png")
    if os.path.exists(p):
        a = Image.open(p).convert("RGBA").getchannel("A"); bb = a.getbbox()
        if bb:
            a = a.crop(bb); target = int(D * 0.56)
            w, h = a.size; s = target / max(w, h); nw, nh = max(1, int(w*s)), max(1, int(h*s))
            a = a.resize((nw, nh), Image.LANCZOS); cx, cy = D // 2, D // 2
            rim = Image.new("RGBA", (nw, nh), cb.dark(base, 0.5)); rim.putalpha(a.point(lambda v: int(v*0.55)))
            col = Image.new("RGBA", (nw, nh), cb.light(base, 0.55)); col.putalpha(a)
            marble.alpha_composite(rim, (cx - nw//2, cy - nh//2 + 3))   # subtle dark rim for depth
            marble.alpha_composite(col, (cx - nw//2, cy - nh//2))       # colored symbol
    return marble

def engrave_number(marble, label, base):
    font = ImageFont.truetype(cb.FONT, int(D * 0.5))
    tmp = Image.new("L", (D, D), 0)
    ImageDraw.Draw(tmp).text((D // 2, D // 2), label, font=font, fill=255, anchor="mm")
    bb = tmp.getbbox()
    if bb: cb._deboss(marble, tmp.crop(bb), base, int(D * 0.46))
    return marble

n = 0
for c in plan:
    num, elem = c["num"], c["element"]
    hexv = manifest[elem]["hex"]
    base = cb.hx(hexv)
    # TOP — element symbol (slot 0)
    top = render_marble(hexv, card_seed(num, 0), size=D, swirl_amp=AMP, swirl_bands=BANDS)
    engrave_symbol(top, elem, base)
    top.save(os.path.join(OUT, f"{num:02d}_top.png"))
    # BOTTOM — card number (slot 1)
    bot = render_marble(hexv, card_seed(num, 1), size=D, swirl_amp=AMP, swirl_bands=BANDS)
    engrave_number(bot, str(num), base)
    bot.save(os.path.join(OUT, f"{num:02d}_bot.png"))
    n += 2

print(f"wrote {n} marbles ({len(plan)} cards x 2) to {OUT}")
