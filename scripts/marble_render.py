#!/usr/bin/env python3
"""
marble_render.py  —  Procedural glass-marble renderer for Spirit Strikers corner badges.

GOAL: every card gets its OWN two marbles (top = element symbol, bottom = number),
so 49 cards x 2 = 98 unique marbles. Uniqueness comes from a per-marble seed that
drives the internal swirl + tiny highlight jitter. The faction BASE COLOR and the
LIGHT DIRECTION stay locked across the deck so the 98 still read as one cohesive set.

The marble is built as a stack of physically-motivated layers, each a float field
computed from the sphere's surface normal N=(x,y,z):

  1. BASE COLOR      faction hex (locked per element)
  2. INTERNAL SWIRL  seeded vein/turbulence pattern, tinted within the faction hue   [UNIQUE]
  3. DIFFUSE         Lambert N·L  -> lit toward the light, dark on the far side
  4. AMBIENT         floor so the shadow side isn't dead black (glass gathers light)
  5. FORM SHADOW     extra darkening on the lower-right rim (where it needs to be dark)
  6. FRESNEL RIM     bright glassy edge line (pow(1-z))
  7. TRANSMISSION    soft warm bounce-glow on the rim opposite the light
  8. SPECULAR        the crisp white reflection hotspot near top-left  + soft softbox  [the "reflection"]
  9. ALPHA           antialiased circular cutout (supersampled)

Pure stdlib + numpy + Pillow. No external image assets — the orb is 100% coded.
"""
import os, math, json, hashlib
import numpy as np
from PIL import Image

BORD = "/Users/blu/card-borders/poker-deck/borders"

# ---- locked deck-wide constants ------------------------------------------------
LIGHT = np.array([-0.50, -0.58, 0.64])      # key light: upper-LEFT, slightly front (image y is DOWN)
LIGHT = LIGHT / np.linalg.norm(LIGHT)
VIEW  = np.array([0.0, 0.0, 1.0])           # camera looks straight on
HALF  = (LIGHT + VIEW); HALF /= np.linalg.norm(HALF)

def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float) / 255.0

def _rng(seed):
    return np.random.default_rng(seed)

# ---- fractal value noise (seeded, smooth) -------------------------------------
def _fractal(size, seed, octaves=5, persistence=0.55, base=8):
    """Sum of upsampled white-noise octaves -> smooth fractal field in [0,1]."""
    rng = _rng(seed)
    out = np.zeros((size, size), np.float32)
    amp, tot, freq = 1.0, 0.0, base
    for _ in range(octaves):
        g = rng.random((freq, freq)).astype(np.float32)
        layer = np.asarray(
            Image.fromarray((g * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC),
            np.float32) / 255.0
        out += amp * layer
        tot += amp
        amp *= persistence
        freq = max(2, int(freq * 2))
    out /= tot
    out -= out.min()
    rng_span = out.max() - out.min() or 1.0
    return out / rng_span

# ---- sphere geometry ----------------------------------------------------------
def _sphere(size):
    """Return surface normals X,Y,Z and a soft alpha for a unit sphere filling the frame."""
    lin = np.linspace(-1.0, 1.0, size, dtype=np.float32)
    X, Y = np.meshgrid(lin, lin)
    r2 = X * X + Y * Y
    inside = r2 <= 1.0
    Z = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))
    # antialiased alpha: 1 inside, feather over the last ~1.5px at this resolution
    edge = 1.5 / (size / 2.0)
    r = np.sqrt(r2)
    alpha = np.clip((1.0 - r) / edge, 0.0, 1.0)
    X = np.where(inside, X, 0.0); Y = np.where(inside, Y, 0.0)
    return X, Y, Z, alpha, r

# ---- the renderer -------------------------------------------------------------
def render_marble(base_hex, seed, size=300, ss=3,
                  swirl_amp=0.16, swirl_bands=2.4, gloss=0.92, glow=0.18):
    """Render one glossy faction marble as an RGBA PIL.Image (size x size).
       seed -> unique internal swirl + sub-pixel highlight jitter (deck stays cohesive)."""
    S = size * ss
    X, Y, Z, alpha, r = _sphere(S)
    base = hx(base_hex)
    rng = _rng(seed)

    # --- (2) internal swirl: domain-warped 'marble' veins, compressed toward the rim (refraction) ---
    refr = 1.0 / (0.42 + 0.58 * Z)                       # glass refraction: pattern bunches at the edge
    th = rng.uniform(0, math.pi)                          # per-marble swirl rotation
    Xr = (X * math.cos(th) - Y * math.sin(th)) * refr
    Yr = (X * math.sin(th) + Y * math.cos(th)) * refr
    turb = _fractal(S, seed * 7 + 1, octaves=5)          # turbulence drives the vein warp
    warp = 1.7 + rng.uniform(-0.4, 0.6)
    veins = 0.5 + 0.5 * np.sin(swirl_bands * math.pi * (Xr + 0.6 * Yr + warp * turb))
    cloud = _fractal(S, seed * 13 + 5, octaves=4)        # broad lightness clouds
    swirl = (veins - 0.5) * 0.7 + (cloud - 0.5) * 0.6    # signed, ~[-0.65,0.65]

    # tint the base color along its own light/dark axis (stays inside the faction hue)
    lift = 1.0 + swirl_amp * swirl                        # multiplicative lightness vein
    col = base[None, None, :] * lift[..., None]
    # deepen saturation in the dark veins, desaturate the bright ones (subtle, glassy)
    sat = (1.0 + 0.10 * swirl)[..., None]
    mean = col.mean(axis=2, keepdims=True)
    col = np.clip(mean + (col - mean) * sat, 0.0, 1.6)

    # --- (3)(4) diffuse + ambient ---
    NdotL = np.clip(X * LIGHT[0] + Y * LIGHT[1] + Z * LIGHT[2], 0.0, 1.0)
    ambient = 0.22
    shade = ambient + (1.0 - ambient) * (NdotL ** 1.35)

    # --- (5) form shadow: push the lower-right rim darker (where it needs to be dark) ---
    farness = np.clip(-(X * LIGHT[0] + Y * LIGHT[1]), 0.0, 1.0)   # 1 on the side away from light
    rim = np.clip((r - 0.55) / 0.45, 0.0, 1.0)                    # 0 center -> 1 edge
    form = 1.0 - 0.40 * farness * (rim ** 1.6)                    # darken far rim up to 40%
    shade = shade * form

    rgb = col * shade[..., None]

    # --- (6) fresnel rim light: bright glassy edge ---
    fres = (1.0 - Z) ** 3.2
    rimcol = np.clip(base * 1.3 + 0.35, 0.0, 1.0)                 # lightened, slightly desaturated faction tone
    rgb += 0.55 * fres[..., None] * rimcol[None, None, :]

    # --- (7) transmission: soft bounce-glow on the rim opposite the light (lower-right) ---
    gx, gy = -LIGHT[0], -LIGHT[1]
    gdir = np.clip(X * gx + Y * gy, 0.0, 1.0) * (rim ** 2.0)
    glowcol = np.clip(base * 1.5 + 0.25, 0.0, 1.0)
    rgb += glow * gdir[..., None] * glowcol[None, None, :]

    # --- (8) specular: crisp white hotspot near top-left + soft softbox sheen ---
    NdotH = np.clip(X * HALF[0] + Y * HALF[1] + Z * HALF[2], 0.0, 1.0)
    jx, jy = rng.uniform(-0.04, 0.04, 2)                          # tiny per-marble highlight jitter
    # crisp primary glint
    spec1 = NdotH ** (170.0 * gloss)
    # soft secondary sheen (broad softbox)
    Hs = np.array([HALF[0] + jx, HALF[1] + jy, HALF[2]]); Hs /= np.linalg.norm(Hs)
    NdotHs = np.clip(X * Hs[0] + Y * Hs[1] + Z * Hs[2], 0.0, 1.0)
    spec2 = NdotHs ** 12.0
    spec = np.clip(spec1 * 1.0 + spec2 * 0.28, 0.0, 1.0)
    rgb += spec[..., None] * np.array([1.0, 1.0, 1.0])[None, None, :]

    # a faint second tiny catch-light lower-right (reflected environment) for that wet-glass read
    Hc = np.array([0.42, 0.5, 0.76]); Hc /= np.linalg.norm(Hc)
    catch = np.clip(X * Hc[0] + Y * Hc[1] + Z * Hc[2], 0.0, 1.0) ** 60.0
    rgb += 0.45 * catch[..., None]

    rgb = np.clip(rgb, 0.0, 1.0)
    out = np.dstack([(rgb * 255).astype(np.uint8),
                     (alpha * 255).astype(np.uint8)])
    img = Image.fromarray(out, "RGBA")
    if ss != 1:
        img = img.resize((size, size), Image.LANCZOS)
    return img


# ---- deck mapping helpers -----------------------------------------------------
def load_manifest():
    return json.load(open(os.path.join(BORD, "borders_manifest.json")))

def card_seed(card_id, slot):
    """Stable unique seed per (card, slot). slot: 0=top symbol, 1=bottom number."""
    h = hashlib.sha1(f"SS-marble-{card_id}-{slot}".encode()).hexdigest()
    return int(h[:8], 16)


if __name__ == "__main__":
    # quick smoke test: one marble per element
    m = load_manifest()["elements"]
    cols = list(m.items())
    pad, D = 16, 300
    sheet = Image.new("RGB", (len(cols) * (D + pad) + pad, D + 2 * pad), (24, 24, 28))
    for i, (k, v) in enumerate(cols):
        mb = render_marble(v["hex"], card_seed(i + 11, 0), size=D)
        sheet.paste(mb, (pad + i * (D + pad), pad), mb)
    sheet.save("_marble_elements.png")
    print("wrote _marble_elements.png", sheet.size)
