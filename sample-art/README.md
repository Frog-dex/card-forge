# sample-art/

Drop line-art cutout PNGs here (transparent background, named `card-NN.png`) to feed
the deck editor, card inspector and build scripts. The original Spirit Strikers
drawings are not bundled with this repo.

The web pages read cutouts from this folder by default. To use a different folder,
open any page with `?art=path/to/cutouts/` (the choice is remembered per browser), or
pick files directly with **📁 Load art…** in the deck editor. For the build scripts,
set `SS_DECK_DIR` (see `scripts/forge_paths.py`).
