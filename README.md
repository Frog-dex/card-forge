# Card Forge

<img src="docs/box.jpg" width="260" align="right" alt="Card Forge box art">

A card-game production studio, built to make the **Spirit Strikers** 49-card deck: a
browser-based drag-and-drop deck editor plus a chain of Python build scripts that turn
hand-drawn line art into print-ready poker cards — procedural marble borders, 98 unique
glass-marble corner badges, Krita `.kra` paint files with inherit-alpha clipping, and
contact sheets for sign-off.

Everything visual is generated in code. No stock textures, no flat PNG reuse.

![Card Forge home page](docs/screenshots/home.png)

## Features

### In the browser (static HTML, zero dependencies)

- **Studio hub** (`index.html`) — box art, the seven factions rendered as live cards,
  the pipeline at a glance and the Sovereign Software shelf.
- **Deck editor** (`deck-editor.html`) — a 7×7 grid (7 categories × 7 elements) rendered
  live on `<canvas>`. Drag any artwork onto another card — or **tap one card, then another**
  on touch screens / with the keyboard — to swap positions; the line art instantly recolors
  to the destination element. Frames and numbered marbles stay put. Light/dark interiors, a
  live line-thickness slider, **undo** (Ctrl/⌘-Z), **📁 Load art…** to pick local
  `card-NN.png` cutouts without a server path, **import/export `arrangement.json`**, and
  labeled full-deck PNG sheets.
- **Card inspector** (`inspector.html`) — any card at print resolution with toggleable
  trim / safe-area / art-window guides, trim-to-cut preview, light/dark interior, a print
  spec sheet, swipe or ←/→ to browse, deep links (`inspector.html#46`) and a one-click
  **600 DPI PNG** export.
- **Marble gallery** (`marbles.html`) — all 98 corner marbles grouped by faction, filter
  chips, symbol/number toggle and a lightbox with a 3D pointer-tilt and moving glint.

### The print pipeline (Python)

- **Procedural marble renderer** (`scripts/marble_render.py`) — every corner badge is a
  9-layer physically-motivated glass orb (diffuse, fresnel rim, transmission glow, crisp
  specular…). 49 cards × 2 marbles = 98 unique orbs from per-(card, slot) SHA-1 seeds,
  yet the deck stays cohesive because the light direction and faction colors are locked.
  Full recipe in [MARBLE-RECIPE.md](MARBLE-RECIPE.md).
- **Print-spec borders** (`scripts/build_marble_borders.py`, `scripts/build_poker_borders.py`)
  — full-bleed faction frames at 600 DPI (1650×2250 px = 2.5×3.5 in + 1/8 in bleed), with
  trim/safe/window guide overlays.
- **Vector-traced line art** (`scripts/trace_lineart.py`, `scripts/bake_vector_art.py`) —
  potrace tracing + XOR parity fill + uniform thinning kills upscale pixelation at the root.
- **Krita assembly** (`scripts/build_poker_kra.py`, `scripts/build_49_marble_kra.py`) —
  kritarunner scripts that build layered `.kra` files where every paintable layer is an
  **inherit-alpha** clipping layer: paint freely, nothing spills outside the shape.
- **Deck variants** (`scripts/deck_variant.py`) — WHITE (black line art on white) and BLACK
  (white line art on dark) versions that differ *only* in the cutouts; colors identical.
- **Contact sheets** (`scripts/contact_sheet.py`, `scripts/white_contact.py`,
  `scripts/front_preview.py`) — labeled 7×7 review sheets and clean single-card fronts.

Read the full story in [MAKING-OF.md](MAKING-OF.md), and see [PROMPT.md](PROMPT.md) for a
self-contained prompt to rebuild the whole tool with an AI coding agent.

## Quick Start

The site is plain static HTML — serve the repo root and open it (pages `fetch()` the
plan and manifest, so `file://` won't work):

```bash
cd card-forge
python3 -m http.server 8080
# then open  http://localhost:8080/
```

| Page | What it's for |
|---|---|
| `index.html` | the hub |
| `deck-editor.html` | arrange the deck; export **⬇ Light/Dark PNG** sheets and **⬇ arrangement.json** |
| `inspector.html#N` | inspect card *N* at print size, export a 600 DPI PNG |
| `marbles.html` | browse the 98 corner marbles |

> **Line art:** the character/scene cutouts are Blu's original drawings and are not
> bundled. Without them everything still runs — borders, marbles, the element-emblem row,
> and a faint element glyph marking each art slot. To see artwork, either drop PNG cutouts
> named `card-NN.png` into `sample-art/`, open any page with `?art=path/to/cutouts/`
> (remembered per browser), or use **📁 Load art…** in the deck editor.

### Build scripts

The Python scripts need `numpy` and `Pillow`; some also use `scipy`, `potracer`
(pure-Python potrace), and `PyMuPDF`:

```bash
pip3 install -r requirements.txt
```

The pipeline, in order:

```bash
python3 scripts/build_marble_borders.py   # 7 faction borders + guides + window base
python3 scripts/plan_cards.py             # 7x7 plan.json + placed art crops
python3 scripts/build_marbles_98.py       # 98 unique corner marbles
python3 scripts/contact_sheet.py          # labeled 7x7 review sheet
python3 scripts/deck_variant.py           # _DECK-WHITE.png + _DECK-BLACK.png
```

Krita assembly (needs [Krita](https://krita.org) and its `kritarunner` CLI):

```bash
kritarunner -s build_poker_kra            # 49 layered .kra card files
kritarunner -s build_49_marble_kra        # one .kra with 49 paintable clipping groups
```

> **Paths:** every script reads its roots from `scripts/forge_paths.py`, so they run
> anywhere via env vars (defaults are the author's original working tree):
>
> | Variable | Meaning |
> |---|---|
> | `CARD_FORGE_ROOT` | poker-deck working dir (`borders/`, `elements/`, `art/`, `marbles/`, `plan.json`) |
> | `SS_DECK_DIR` | spirit-strikers-deck dir with the original line-art cutouts |
> | `SS_DRAWINGS_PDF` | source PDF for `extract_crops_pdf.py` |
> | `CARD_FORGE_FONT` | font for engraved numbers (falls back to Arial Rounded → DejaVu/Liberation) |
> | `SS_ROOT`, `SS49_DIR`, `SS49_OUT` | Krita builders (`SS_ROOT` falls back to `CARD_FORGE_ROOT`) |
>
> For example, regenerate all 98 marbles from this repo's own assets:
>
> ```bash
> mkdir -p /tmp/forge && cp -r borders elements plan.json /tmp/forge/
> CARD_FORGE_ROOT=/tmp/forge python3 scripts/build_marbles_98.py
> ```
>
> Lint with `ruff check scripts` (config in `ruff.toml`).

## How it works

1. **Plan** — `plan_cards.py` lays 49 cards on a 7×7 grid: rows are categories
   (Characters, Locations, Vehicles, Relics, Story Elements, Motives, Elements), columns
   are elements (water, wood, electric, fire, metal, earth, spirit). Each card's art is
   pre-fit into the border window and dumped as raw BGRA for Krita. Output: `plan.json`.
2. **Borders** — a rounded-rectangle window mask is subtracted from a full-bleed
   rectangle; a procedural "polished marble" gloss field (top-left key light + specular
   streaks + blurred-noise veining) is color-ramped through each faction's
   shadow/mid/highlight palette.
3. **Marbles** — `marble_render.py` shades a unit sphere from its surface normals through
   9 layers, then `build_marbles_98.py` engraves the element symbol (top) or card number
   (bottom) as a deboss: dark fill offset by a light lower lip, so the glyph reads carved
   *into* the glass.
4. **Assembly** — the `.kra` builders stack BACKGROUND / ART / BORDER / GUIDES groups and
   set `inheritAlpha` on every paint layer, giving artists per-shape clipping for free.
5. **Review** — contact sheets and the deck editor render the exact same assets at thumb
   scale, so what you sign off is what prints.

Faction palette (single source of truth, `borders/borders_manifest.json`):
fire `#c22c37` · water `#1c6baf` · wood `#85dc7b` · electric `#d3cf61` ·
earth `#684a36` · spirit `#64318f` · metal `#5a6068`.

## Screenshots

| Deck editor | Card inspector (guides on) |
|---|---|
| ![deck editor](docs/screenshots/deck-editor.png) | ![card inspector](docs/screenshots/inspector.png) |

| Marble gallery | Marble viewer |
|---|---|
| ![marble gallery](docs/screenshots/marbles.png) | ![marble lightbox](docs/screenshots/marbles-lightbox.png) |

On a phone — the inspector stacks, the editor scrolls sideways and swaps by tapping:

<img src="docs/screenshots/mobile-inspector.png" width="220" alt="inspector on mobile"> <img src="docs/screenshots/mobile-editor.png" width="220" alt="deck editor on mobile">

### Raw assets

| Fire border (600 DPI, full bleed) | Spirit gem emblem | Corner marble (card 1, symbol) | Trim/safe/window guides |
|---|---|---|---|
| ![fire border](borders/border_fire.png) | ![spirit emblem](elements/emblem_spirit.png) | ![marble](marbles/01_top.png) | ![guides](borders/guides.png) |

All 98 corner marbles live in [`marbles/`](marbles/) — every one a unique swirl.

## Repo layout

```
index.html              studio hub
deck-editor.html        drag-and-drop / tap-to-swap deck editor
inspector.html          single-card print inspector + 600 DPI export
marbles.html            98-marble gallery with tilt viewer
assets/                 shared forge.css + forge.js (card compositor, data loader)
plan.json               the 7x7 deck plan (cards, elements, art placement)
card-categories.json    card-id -> category mapping
MARBLE-RECIPE.md        how every glass marble is built (the 9 layers)
MAKING-OF.md            the full production story
PROMPT.md               recreate this tool from scratch with an AI agent
borders/                7 faction border PNGs + window base + guides + manifest
elements/               7 gem emblems + 7 extracted element glyphs
marbles/                98 unique corner marbles (NN_top / NN_bot)
sample-art/             drop line-art cutouts here to feed the editor
scripts/                the 20 Python build scripts + forge_paths.py (shared paths)
docs/                   box art, shelf boxes, screenshots
requirements.txt        Python deps for the build scripts
```

## Publish

```bash
gh repo create Frog-dex/card-forge --public --source . --push
```

## The Sovereign Software shelf

Every box on the Spirit Strikers software shelf. Put the discs in the terminal here: https://frog-dex.github.io/terrace-world/library.html#software

| <a href="https://github.com/Frog-dex/terrace-world"><img src="docs/shelf/terrace-world.jpg" width="150" alt="Terrace World box"></a> | <img src="docs/shelf/snowberry-os.jpg" width="150" alt="Snowberry OS box"> | <img src="docs/shelf/lizard-widget.jpg" width="150" alt="Lizard Widget box"> | <img src="docs/shelf/frog-widget.jpg" width="150" alt="Frog Widget box"> |
|:--:|:--:|:--:|:--:|
| **Terrace World**<br>the game | **Snowberry OS**<br>early build, not released yet | **Lizard Widget**<br>add-on, not released yet | **Frog Widget**<br>add-on, not released yet |

| <a href="https://github.com/Frog-dex/3d-models-pack"><img src="docs/shelf/models-pack.jpg" width="150" alt="3D Models Pack box"></a> | <a href="https://github.com/Frog-dex/plan-and-code"><img src="docs/shelf/plan-and-code.jpg" width="150" alt="Plan & Code box"></a> | <a href="https://github.com/Frog-dex/krita-agent"><img src="docs/shelf/krita-agent.jpg" width="150" alt="Krita Agent box"></a> | <a href="https://github.com/Frog-dex/card-forge"><img src="docs/shelf/card-forge.jpg" width="150" alt="Card Forge box"></a> |
|:--:|:--:|:--:|:--:|
| **3D Models Pack**<br>thirteen free models | **Plan & Code**<br>plan a page, hand it to an AI | **Krita Agent**<br>AI tools inside Krita | **Card Forge**<br>card-making studio |

## License

MIT © 2026 Blu Inman. The Spirit Strikers artwork, characters, and brand remain
© Blu Inman — the code is free, the world is his.
