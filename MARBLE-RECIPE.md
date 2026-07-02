# Spirit Strikers — Marble Recipe (how every circle is made)

**98 marbles total** = 49 cards × 2 (top = element **symbol**, bottom = **number**).
Each is rendered 100% in code (`marble_render.py`) — no flat PNG reuse. Every marble is
**unique** via a per-(card,slot) seed, but the deck stays cohesive because two things are
**locked across all 98**: the faction **base color** and the **light direction**.

---

## Locked across the whole deck

| Thing | Value | Why locked |
|------|-------|-----------|
| Light source | upper-LEFT, slightly front → `LIGHT = (-0.50, -0.58, 0.64)` | every marble lit the same → reads as one set |
| Camera/view | straight on `(0,0,1)` | — |
| Base color | faction hex from `borders_manifest.json` | spiritstriker.app source of truth |

Faction hex (authoritative): fire `#c22c37` · water `#1c6baf` · wood `#85dc7b` ·
electric `#d3cf61` · earth `#684a36` · spirit `#64318f` · metal `#5a6068`.

## Unique per marble (driven by `seed = sha1("SS-marble-{card}-{slot}")`)

- Internal **swirl rotation**, vein **warp**, and **cloud** pattern (the glass nebula)
- Sub-pixel **highlight jitter** on the soft sheen

Same card, top vs bottom = different slot = different seed = different swirl. Reproducible:
the same card always regenerates the identical marble.

---

## The 9 layers (built from the sphere normal N = (x, y, z))

1. **Base color** — faction hex.
2. **Internal swirl** *(unique)* — domain-warped fractal "marble" veins (`sin(bands·(rot + warp·turbulence))`)
   plus broad lightness clouds, **compressed toward the rim** by a refraction term `1/(0.42+0.58·z)`
   so it looks like you're seeing *into* glass. Tints only along the faction hue (lighter veins / deeper pockets).
3. **Diffuse** — Lambert `clamp(N·L)^1.35`: bright toward the light, dark on the far side.
4. **Ambient** — `0.22` floor so the shadow side is deep, not dead-black (glass gathers light).
5. **Form shadow** — extra darkening (up to 40%) on the **lower-right rim**, the side away from
   the light. *"Darken it where it needs to be dark."*
6. **Fresnel rim** — bright glassy edge line `(1-z)^3.2` in a lightened faction tone.
7. **Transmission glow** — soft colored bounce-light on the rim **opposite** the key light.
8. **Specular** *(the reflection)* — crisp white hotspot near top-left `(N·H)^~170` + a broad
   soft "softbox" sheen + a tiny lower-right catch-light → the wet-glass read.
9. **Alpha** — antialiased circular cutout (3× supersampled, LANCZOS down).

Then the **engraving**: the element symbol (top marble) / number (bottom marble) is debossed into
the glass — dark fill + light lower lip — so it reads as carved *inside* the orb.

---

## Tunable knobs (per render call)

| Param | Default | Effect |
|------|---------|--------|
| `swirl_amp` | 0.16 | vein lightness amplitude — higher = more visible nebula |
| `swirl_bands` | 2.4 | number of swirl bands — higher = busier glass |
| `gloss` | 0.92 | highlight tightness — higher = sharper, wetter glint |
| `glow` | 0.18 | strength of the opposite-rim transmission glow |
| `size` / `ss` | 300 / 3 | output px / supersample factor |

**Deck intensity** is the one global style choice: *subtle* (≈0.14/2.2, clean premium set)
vs *bold* (≈0.30/3.4, hand-blown glass). Mock used 0.22/2.8 (middle).

---

## Regenerate

```bash
python3 marble_render.py            # one marble per element  -> _marble_elements.png
# batch all 98 (after intensity is locked):
python3 build_marbles_98.py         # writes marbles/<card>_top.png + _bot.png  (TODO: pending go-ahead)
```

Integration: `corner_badges.make_badge()` consumes these per-card marbles instead of the
shared `borders/marble_<elem>.png`. Corner placement (TRIM_OFF=80, padding-cropped) is the
black-gap fix from the previous pass — keep it.
