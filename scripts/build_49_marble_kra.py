"""Run via kritarunner. Build ONE .kra holding all 49 faction marbles, each as its
own clipping group so Blu paints one at a time without spilling outside the circle:

  MARBLES (parent group)
    GROUP "01 water"
      PAINT-HERE (inherit alpha ON)   <- empty; Blu paints here, clipped to the orb
      marble                          <- lit/shadowed faction orb (the alpha shape)
    ... 49 groups
  BACKGROUND (working only)           <- dark fill so the glass reads while painting

Inherit Alpha on the top layer of each group inherits ONLY that group's orb alpha ->
per-circle clipping. ASCII-only names (unicode breaks kritarunner). Verify via the
saved file + sentinel (stdout is not surfaced).
"""
import os, json
from krita import Krita
from PyQt5.QtCore import QByteArray

DIR = os.environ.get("SS49_DIR", "/Users/blu/card-borders/poker-deck/_kra49")
OUT = os.environ.get("SS49_OUT", "/Users/blu/card-borders/poker-deck/marbles-paint-49.kra")


def __main__(*args):
    man = json.load(open(os.path.join(DIR, "manifest.json")))
    cw, ch = man["canvas"]

    app = Krita.instance()
    app.setBatchmode(True)
    doc = app.createDocument(cw, ch, "SS 49 Marbles - paint", "RGBA", "U8", "", float(man["resolution"]))
    doc.setBatchmode(True)
    root = doc.rootNode()

    # BACKGROUND (working only) — added first => sits at the bottom
    bg = doc.createNode("BACKGROUND (working only)", "paintlayer")
    root.addChildNode(bg, None)
    with open(os.path.join(DIR, man["bg"]["file"]), "rb") as f:
        bg.setPixelData(QByteArray(f.read()), 0, 0, man["bg"]["w"], man["bg"]["h"])

    # MARBLES parent group on top of the background
    marbles = doc.createNode("MARBLES (49 - paint one at a time)", "grouplayer")
    root.addChildNode(marbles, None)

    for m in man["marbles"]:
        grp = doc.createNode(m["name"], "grouplayer")          # e.g. "01 water"
        marbles.addChildNode(grp, None)

        base = doc.createNode("marble", "paintlayer")          # the lit orb = alpha shape
        grp.addChildNode(base, None)
        with open(os.path.join(DIR, m["file"]), "rb") as f:
            base.setPixelData(QByteArray(f.read()), m["x"], m["y"], m["w"], m["h"])

        paint = doc.createNode("PAINT-HERE (inherit alpha)", "paintlayer")
        grp.addChildNode(paint, base)                          # placed ABOVE the orb
        paint.setInheritAlpha(True)                            # clip paint to THIS circle

    doc.refreshProjection()
    ok = doc.saveAs(OUT)
    with open(os.path.join(DIR, "_build_done.txt"), "w") as f:
        f.write(("SAVED " if ok else "FAILED ") + OUT + "\n")
    doc.close()


if __name__ == "__main__":
    __main__()
