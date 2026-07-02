# How We Made Our Card Game

The Spirit Strikers deck is 49 poker cards — 7 categories × 7 elements — built from
hand-drawn line art and a pile of Python. This is the production story, from pencil
drawings to print-ready `.kra` files, in the order it actually happened.

## 1. Getting the drawings out

The source art lives in a PDF of cropped drawings. `scripts/extract_crops_pdf.py` pulls
every embedded image out at **native resolution** (PyMuPDF, first image per page) instead
of rasterizing pages — no resampling loss before the pipeline even starts.

## 2. Tracing the line art (killing pixelation at the root)

The cutouts are small. Upscaling them to card resolution made fat, stair-stepped lines.
The fix (`scripts/trace_lineart.py`) was to stop treating the art as pixels:

- threshold the cutout's alpha into a binary mask
- trace it with **potrace** into bezier curves (gotcha: potracer requires a `bool` array —
  a `uint8` 0/1 mask silently collapses into one giant block)
- tessellate the beziers and rasterize every closed polygon at 2× supersample
- combine polygons with an **XOR parity fill** so holes (eyes, gaps between strokes)
  punch through correctly — and if the parity lands inverted, detect it cheaply: the
  canvas corner is never a stroke, so `if acc[0,0]: acc = ~acc`
- optionally **erode** the mask a few pixels for uniform line thinning, then LANCZOS
  down to an anti-aliased mask

`scripts/bake_vector_art.py` batch-bakes all card cutouts at 3× source size — crisp
strands of line work at any print size, with extra thinning (`thin=3`) for the dense
Locations scene cards.

## 3. Borders at print spec

Cards are poker size: **2.5×3.5 in + 1/8 in bleed at 600 DPI = 1650×2250 px**, trim at
(75,75)–(1575,2175), art window inset 44 px with a 60 px corner radius.

The border is a mask trick: a full-bleed rectangle minus a rounded-rectangle window
(drawn at 2× and LANCZOS'd down for clean edges). Two generations of fills:

- `build_poker_borders.py` — seven bespoke procedural fields (chrome, molten, flame,
  aqua, crystal, stone, nebula) built from gaussian ridges, sine bands, and blurred
  noise, color-ramped through shadow/mid/highlight hexes, with corner and bottom glows.
- `build_marble_borders.py` — the final look: a **polished marble** gloss field (top-left
  key light, specular streaks, two octaves of blurred-noise veining) ramped through the
  real faction palette sampled from the spiritstriker.app gem sheet. It also recolors an
  actual marble-sphere photo through each faction's luminance ramp — those became the
  first-generation corner marbles.

Every border ships as PNG (for previews) *and* raw BGRA (for Krita), plus a
`borders_manifest.json` carrying the canvas geometry and faction hexes — the single
source of truth every later script reads.

Guides are their own transparent layer: magenta trim, cyan safe box, yellow window.

## 4. The gem emblems

The element gems were cropped from the canonical gem sheet (`recreate_emblems.py`) with
near-black gaps turned transparent, then `extract_symbols.py` pulled just the dark glyph
(flame, drop, sprout…) out of each gem's central disc by thresholding luminance inside a
circle — giving clean alpha-only symbols to engrave into marbles. `extract_elements_v2.py`
later rebuilt the emblems "vector-style": crisp hexagon frame, radial-gradient disc, and
the original glyph re-smoothed (upscale → blur → threshold → AA downsample).

## 5. The marble recipe (98 unique glass orbs)

The signature element. Full write-up in [MARBLE-RECIPE.md](MARBLE-RECIPE.md); the short
version: every card gets its **own two marbles** (top = element symbol, bottom = number),
rendered 100% in code by `marble_render.py` as nine stacked layers computed from a
sphere's surface normals — base faction color, seeded internal swirl, Lambert diffuse,
ambient floor, form shadow on the far rim, fresnel edge light, transmission glow opposite
the key light, crisp specular + softbox sheen, and a supersampled circular alpha.

Two things are **locked across all 98** so the deck reads as one set: the light direction
`(-0.50, -0.58, 0.64)` and the faction base color. Everything else — swirl rotation, vein
warp, cloud pattern, highlight jitter — comes from `seed = sha1("SS-marble-{card}-{slot}")`,
so every marble is unique *and* perfectly reproducible.

The best trick is the **refraction compression**: the swirl coordinates are scaled by
`1/(0.42 + 0.58·z)`, bunching the vein strands toward the rim exactly the way a pattern
inside real glass appears to — you're looking *into* the orb, not at a sticker.

The glyph is **debossed**, not printed: a dark fill offset by a light "lower lip" a few
pixels down-right, so the symbol reads carved into the glass. `build_marbles_98.py` bakes
all 98 at the locked middle intensity (swirl amp 0.22 / bands 2.8) at exactly the
placement size — WYSIWYG, no resize softening.

## 6. Corner badges

`corner_badges.py` places the two marbles at top-left and bottom-right, nestled into the
border. Placement was tuned to `TRIM_OFF = bleed + 5 px` with the marble's transparent
padding cropped off first — that was the "black gap" fix: the orb hugs the corner and
covers the dark window seam instead of floating beside it. Unique per-card marbles load
from `marbles/`; if one is missing, the badge falls back to the shared faction marble
with a live deboss.

## 7. The plan

`plan_cards.py` assigns every drawing to its grid cell: rows are categories (Characters,
Locations, Vehicles, Relics, Story Elements, Motives, Elements), columns are the seven
elements in fixed order. Each card's element is inferred from faction keywords in its
description ("frog" → water, "crow" → metal…), art is pre-fit into ~88–90% of the window
and dumped as raw BGRA, and the bottom row gets the seven gem emblems. Output:
`plan.json` — the file the editor, the sheets, and the assemblers all consume.

## 8. Krita assembly — the inherit-alpha workflow

This is where the deck becomes *paintable*. Krita's **Inherit Alpha** makes a layer clip
to the combined alpha of the layers below it in the same group — a clipping mask you can
build programmatically. Two `kritarunner` scripts exploit it:

- `build_poker_kra.py` — 49 layered card files. Each `.kra` stacks:
  `BACKGROUND (working only)` → `ART` group (window-base clip shape, art reference, and an
  empty `PAINT-HERE (inherit alpha)` layer) → `BORDER` group (border + an inherit-alpha
  `border-shade` layer) → corner marbles → hidden `GUIDES` group. Paint anywhere on
  PAINT-HERE and color stays inside the rounded window. Same for shading the border.
- `build_49_marble_kra.py` — one canvas, 49 groups, each holding a lit orb plus an
  inherit-alpha paint layer above it. Painting one marble can never spill into the next.

Hard-won kritarunner lessons baked into both: layer/doc names must be **ASCII only**
(unicode breaks its stdout), stdout isn't surfaced at all so each script writes a
**sentinel file** (`_kra_build_done.txt`) to prove completion, and pixel data goes in as
raw **BGRA** bytes via `setPixelData`.

## 9. White deck, black deck

We couldn't decide whether the deck should be black-on-white or white-on-black — so
`deck_variant.py` renders both, differing **only** in the line-art cutouts: WHITE gets a
white interior with the traced art recolored near-black; BLACK gets a dark interior with
the art recolored near-white. Borders, gem emblems, and corner marbles are pixel-identical
across both. Recoloring is trivial because the traced art is a pure alpha shape — fill a
rectangle with the ink color and copy the alpha channel over.

## 10. Contact sheets and sign-off

Nothing ships without a sheet. `contact_sheet.py` renders the labeled 7×7 grid (row and
column headers, card numbers, element colors); `white_contact.py` is its white-deck twin;
`front_preview.py` renders clean single-card fronts cropped to trim. These sheets use the
exact production assets at thumb scale, so approval on the sheet is approval on the print.

## 11. The deck editor

Finally, `deck-editor.html` — a zero-dependency, single-file editor for the *arrangement*.
It loads `plan.json` and draws every card live on a `<canvas>`: interior, recolored line
art, border, and that card's two unique marbles. Drag any artwork onto another cell and
they swap — the art recolors to its new element automatically because ink color is applied
at draw time from the destination column, while frames and numbered marbles belong to the
*position*, not the art. A slider re-thresholds line thickness in real time, Light/Dark
flips the interiors, and one click exports print-order deck sheets or `arrangement.json`.

That's the studio: draw once, trace once, and let seeds, masks, and manifests do the
other 98%.
