"""Shared working-directory paths for the Card Forge build scripts.

The pipeline was written against Blu's working tree. Every script now reads its
roots from here, so you can run it anywhere by setting two env vars:

  CARD_FORGE_ROOT  the poker-deck working dir (borders/, art/, marbles/, plan.json …)
  SS_DECK_DIR      the spirit-strikers-deck dir holding the original line-art cutouts

Defaults are unchanged from the original scripts, so nothing moves for the author.
"""
import os

FORGE_ROOT = os.environ.get("CARD_FORGE_ROOT", "/Users/blu/card-borders/poker-deck")
DECK_ROOT = os.environ.get("SS_DECK_DIR", "/Users/blu/spirit-strikers-deck")


def find_font(*candidates):
    """First font file that exists: $CARD_FORGE_FONT, then the given candidates,
    then common Linux/Windows fallbacks. Returns None if nothing is found, in which
    case callers fall back to Pillow's built-in default font."""
    extra = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for p in [os.environ.get("CARD_FORGE_FONT"), *candidates, *extra]:
        if p and os.path.exists(p):
            return p
    return None
