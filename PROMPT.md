# PROMPT.md — Recreate Card Forge from scratch

> Paste this prompt into an AI coding agent to rebuild this tool. It is self-contained:
> purpose, UI, behaviors, file structure, and the implementation tricks that matter.

---

Build **Card Forge**: a card-game production studio for a 49-card deck (7 categories ×
7 elements). It has two halves: (A) a single-file browser **deck editor**, and (B) a set
of Python **build scripts** that generate every visual asset procedurally and assemble
print-ready files. Python side uses only `numpy`, `Pillow`, `scipy`, `potracer`
(pure-Python potrace), and `PyMuPDF`; the Krita assemblers run under Krita's
`kritarunner`. The editor is vanilla HTML/JS/canvas — no framework, no build step.

## The deck

- Grid: 7 rows (categories: Characters, Locations, Vehicles, Relics, Story Elements,
  Motives, Elements) × 7 columns (elements, fixed order: water, wood, electric, fire,
  metal, earth, spirit). Card number = row-major 1..49.
- Faction palette (lock it everywhere): fire `#c22c37`, water `#1c6baf`, wood `#85dc7b`,
  electric `#d3cf61`, earth `#684a36`, spirit `#64318f`, metal `#5a6068`.
- Print spec: poker 2.5×3.5 in + 1/8 in bleed @ 600 DPI → canvas **1650×2250 px**,
  bleed 75 px, trim (75,75)-(1575,2175), safe 75 px inside trim, visible border 44 px,
  art window = trim inset by border with **60 px rounded corners**, trim radius 84 px.
- `plan.json` is the contract every component reads: `{canvas, window, rows, cols,
  cells:[{row, col, num, category, element, hex, card, art:{file,x,y,w,h}|null, blank,
  label, filename}]}`.

## HEADLINE FEATURE — the drag-and-drop deck editor (`deck-editor.html`)

A dark-UI (bg `#141416`, panel `#1e1e22`, ink `#e8e4dc`, gold accent `#c9a24a`) sticky
header + a CSS grid: 120 px row-label column plus 7 card columns, column headers tinted
in each element's hex. Every cell is a `<canvas>` (210 px wide, poker aspect) with an
absolutely-positioned draggable overlay div.

**The magic behavior:** drag any card's artwork onto another card and they **swap
positions — and each artwork instantly recolors to its new element and light/dark mode.**
Frames, element columns, and the numbered corner marbles never move; they belong to the
grid position. This works because of a strict ownership split:

- position owns: border PNG (by column element), the two corner marble PNGs (by card
  number), interior fill
- artwork owns: only its cutout image + window-fit rectangle (`artOf` map keyed
  `"row_col"`; a drop just swaps two entries and redraws the two cells)
- ink color is applied at *draw time*: line art is drawn through a `lineArt(img, col)`
  helper that copies the image to an offscreen canvas, walks `getImageData`, and for each
  pixel sets RGB to the ink color if `alpha > THIN`, else alpha 0. Recoloring and line
  thickness are the same operation.

Header controls and behaviors:

- **Light/Dark** segmented toggle: light = white interiors + near-black ink `[18,18,18]`;
  dark = `#18181c` interiors + near-white ink `[242,242,242]`. Element-emblem cards
  (bottom row, ids `element-<elem>`) always keep a dark interior and are drawn unrecolored.
- **line thickness** range slider (40–210, default 110): it is the alpha threshold in
  `lineArt` — higher threshold = thinner strands. Re-renders all 49 cells oninput.
- **⬇ Light PNG / ⬇ Dark PNG**: render all 49 cells into one big offscreen sheet canvas
  (gutter + labels), temporarily switching mode, then `canvas.toBlob` → object URL →
  synthetic `<a download>` click.
- **⬇ arrangement.json**: dump `[{row, col, num, element, card}]` for the build scripts.
- **Reset**: restore `artOf` from `plan.json`.
- Cell rendering order: rounded-rect interior → recolored art (or emblem as-is, over a
  small dark rounded backing) → border PNG → top-left marble `marbles/NN_top.png` →
  bottom-right marble `marbles/NN_bot.png` at `D=286·scale`, offset `(bleed+5)·scale`.
- Preload every image once into a url→Image cache (`crossOrigin="anonymous"`, resolve
  null on error so missing art degrades gracefully). Serve via `python3 -m http.server`.

## Python pipeline (scripts/, in dependency order)

1. **`build_marble_borders.py`** — faction borders. Frame mask = full-bleed white
   rectangle minus the rounded window (draw at 2×, LANCZOS down). Fill = procedural
   "polished marble" float field: top-left key light `(1-Y)*0.6+(1-X)*0.4`, gaussian
   specular streaks, two octaves of gaussian-blurred noise veining; map field through a
   shadow/mid/highlight color ramp per faction (`mid` = faction hex, shadow = ×0.42,
   highlight = lighten 0.62). Save `border_<elem>.png` **and** raw `.bgra` bytes
   (`np.array(rgba)[:,:,[2,1,0,3]].tobytes()` — Krita wants BGRA), plus `window_base.png`
   (dark fill in the window shape — the clip shape for painting), `guides.png` (magenta
   trim / cyan safe / yellow window outlines), and `borders_manifest.json` (geometry +
   palette; single source of truth).
2. **`marble_render.py`** — THE marble renderer (see MARBLE-RECIPE.md). Unit sphere from
   a meshgrid; normals N=(x,y,z); 9 layers: (1) base faction color; (2) seeded internal
   swirl: domain-warped veins `0.5+0.5·sin(bands·π·(Xr+0.6·Yr+warp·turbulence))` where
   turbulence is summed upsampled white-noise octaves, coordinates rotated by a random
   per-marble angle **and multiplied by a refraction term `1/(0.42+0.58·z)`** so the
   pattern compresses toward the rim like real glass; tint only along the faction hue;
   (3) Lambert diffuse `clamp(N·L)^1.35`; (4) ambient floor 0.22; (5) form shadow: up to
   40% darkening on the rim away from the light; (6) fresnel rim `(1-z)^3.2` in a
   lightened faction tone; (7) transmission glow on the rim opposite the light;
   (8) specular: crisp `(N·H)^(170·gloss)` hotspot + broad softbox sheen + tiny
   lower-right catch light; (9) antialiased circular alpha, rendered at 3× supersample,
   LANCZOS down. Light locked deck-wide at `(-0.50,-0.58,0.64)` normalized. Uniqueness:
   `seed = int(sha1(f"SS-marble-{card}-{slot}")[:8], 16)` — reproducible forever.
3. **`build_marbles_98.py`** — batch 49×2 marbles at locked intensity (amp 0.22, bands
   2.8) at exactly the placement size (286 px, WYSIWYG). Top marble gets the element
   symbol tinted light-faction with a subtle dark rim; bottom gets the card number
   **debossed**: glyph as L-mode alpha, composite a light "lower lip" copy offset
   (+3,+4) px under a dark fill — reads carved into the glass. Save `marbles/NN_top.png`
   / `NN_bot.png`.
4. **`corner_badges.py`** — `make_badge(num, elem)` returns a full-canvas RGBA with the
   top-left symbol marble and bottom-right number marble at `TRIM_OFF = bleed+5` px.
   Crop each marble's transparent padding (`getchannel("A").getbbox()`) before resizing —
   otherwise a dark gap shows between orb and border. Prefer per-card unique marbles
   from `marbles/`, fall back to shared faction marble + live deboss.
5. **`trace_lineart.py` / `bake_vector_art.py`** — vectorize cutout line art: alpha>90
   mask → `potrace.Bitmap(mask.astype(bool))` (**must be bool** — uint8 collapses to one
   block) → trace(turdsize=3) → tessellate beziers (16 steps) → rasterize each closed
   polygon at 2× and **XOR** them together (parity fill = holes punch through); if
   `acc[0,0]` is filled the parity landed inverted → invert; optional
   `binary_erosion` for uniform thinning (3 px for dense scene cards, 2 otherwise);
   LANCZOS down to an anti-aliased mask; bake at 3× source as black ink + alpha.
6. **`plan_cards.py`** — build `plan.json`: map card ids to categories (from
   `card-categories.json`), infer each card's element from faction keywords in its
   description (frog→water, crow→metal, …), place one card per element column per
   category row (overflow parks in the lowest free column), fit art to ~90% of the
   window centered (~72% for emblems), dump placed art as `.bgra` + rect, fill the
   Elements row with the 7 gem emblems, number cells 1..49.
7. **`extract_crops_pdf.py`** (PyMuPDF: extract embedded page images at native
   resolution), **`recreate_emblems.py`** (crop 7 gems from a sheet photo; near-black →
   transparent via `alpha = clip((max_rgb-26)/40)`), **`extract_symbols.py`** (glyph =
   dark pixels inside the gem's central disc: threshold at 50% of the disc's 75th
   percentile luminance), **`extract_elements_v2.py`** (rebuilt vector-style emblems:
   hexagon frame + radial-gradient disc + re-smoothed glyph).
8. **`build_poker_kra.py`** (kritarunner) — 49 layered `.kra` files. Per card:
   `BACKGROUND (working only)` dark fill → `ART` group [window_base clip shape,
   art-reference placed at its plan rect, empty `PAINT-HERE` with
   **`setInheritAlpha(True)`**] → `BORDER` group [border, `border-shade` inherit-alpha]
   → corner-number layer → hidden `GUIDES` group. Inherit Alpha = programmatic clipping
   mask: paint can never leave the window/border shape. Pixel data via
   `layer.setPixelData(QByteArray(bgra_bytes), x, y, w, h)`.
   **kritarunner gotchas:** ASCII-only document/layer names (unicode breaks its stdout),
   stdout is not surfaced — write a sentinel file to prove completion, honor an env var
   (`SS_ROOT`) for the working dir.
9. **`pack_49_marbles.py` + `build_49_marble_kra.py`** — one 3780×3780 canvas, 7×7 grid
   of clean 480 px lit orbs (no glyphs), each in its own group: `marble` layer (the
   alpha shape) + `PAINT-HERE (inherit alpha)` above it. The artist paints 49 circles
   one at a time with zero spill.
10. **`deck_variant.py`** — WHITE and BLACK deck sheets differing only in line-art ink
    (near-black on white / near-white on dark); recolor = new solid fill + copied alpha.
    Emblems keep a cropped dark rounded backing that hugs the emblem, not the card.
11. **`contact_sheet.py` / `white_contact.py` / `front_preview.py`** — labeled 7×7
    review sheets (240 px thumbs, element-tinted column headers, card labels) and clean
    single-card fronts cropped to trim.

## File structure

```
card-forge/
├── deck-editor.html          # the editor (single file)
├── plan.json                 # generated by plan_cards.py
├── card-categories.json      # card-id -> category
├── MARBLE-RECIPE.md          # the 9-layer marble documentation
├── borders/                  # border_<elem>.png, window_base.png, guides.png,
│                             # marble_<elem>.png, borders_manifest.json
├── elements/                 # emblem_<elem>.png, symbol_<elem>.png
├── marbles/                  # NN_top.png / NN_bot.png  (98 files)
├── sample-art/               # line-art cutouts card-NN.png (editor art source)
└── scripts/                  # all Python above
```

## Acceptance checks

- `python3 -m http.server 8080` → `deck-editor.html` shows 49 cards; dragging art
  between two cells swaps them and recolors instantly; the thickness slider visibly
  thins strands; exports download.
- Re-running `build_marbles_98.py` reproduces byte-identical swirls (seeded).
- All 98 marbles share one light direction; no two share a swirl.
- `.kra` files open in Krita with working inherit-alpha clipping on every PAINT-HERE.
- Borders/marbles at 1650×2250 @ 600 DPI with correct trim/safe/window guides.
