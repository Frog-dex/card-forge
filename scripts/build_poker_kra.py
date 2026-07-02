"""kritarunner assembler: build 49 labeled poker .kra files from plan.json.
Run: kritarunner -s build_poker_kra   (script copied into pykrita dir first).
Each card: GUIDES group (hidden) / BORDER group (border + shade inherit-alpha) /
ART group (window-base + art-reference + PAINT-HERE inherit-alpha) / BACKGROUND.
Layer + doc names are ASCII only (unicode breaks kritarunner stdout)."""
import os, json
from krita import Krita
from PyQt5.QtCore import QByteArray

ROOT = os.environ.get("SS_ROOT", "/Users/blu/card-borders/poker-deck")
BORD = os.path.join(ROOT, "borders")
ART  = os.path.join(ROOT, "art")
BADGES = os.path.join(ROOT, "badges")
OUT  = os.path.join(ROOT, "cards")
os.makedirs(OUT, exist_ok=True)

def rd(p):
    with open(p, "rb") as f: return f.read()

def __main__(*args):
    app = Krita.instance()
    P = json.load(open(os.path.join(ROOT, "plan.json")))
    W, H = P["canvas"]
    cells = P["cells"]
    bm = json.load(open(os.path.join(BORD, "borders_manifest.json")))

    border_bytes = {k: rd(os.path.join(BORD, bm["elements"][k]["file"])) for k in bm["elements"]}
    win_bytes = rd(os.path.join(BORD, "window_base.bgra"))
    guide_bytes = rd(os.path.join(BORD, "guides.bgra"))

    done = 0
    for cell in cells:
        name = "SS %s %s %s" % (cell["label"][:2], cell["category"], cell["element"])
        doc = app.createDocument(W, H, name, "RGBA", "U8", "", 600.0)
        root = doc.rootNode()

        def full(layer, data):
            layer.setPixelData(QByteArray(data), 0, 0, W, H)

        # --- BACKGROUND (working only) : dark fill so transparent areas read while painting
        bg = doc.createNode("BACKGROUND (working only)", "paintlayer")
        bgdata = bytes(bytearray([28, 27, 33, 255]) * (W * H))  # BGRA dark
        full(bg, bgdata)
        root.addChildNode(bg, None)

        # --- ART group : window-base (clip shape) / art-reference / PAINT-HERE inherit alpha
        gart = doc.createNode("ART", "grouplayer")
        root.addChildNode(gart, None)
        wbase = doc.createNode("card-bg (swap me)", "paintlayer")
        full(wbase, win_bytes)
        gart.addChildNode(wbase, None)
        if cell["art"]:
            a = cell["art"]
            aref = doc.createNode("art-reference", "paintlayer")
            aref.setPixelData(QByteArray(rd(os.path.join(ART, a["file"]))), a["x"], a["y"], a["w"], a["h"])
            gart.addChildNode(aref, None)
        paint = doc.createNode("PAINT-HERE (inherit alpha)", "paintlayer")
        paint.setInheritAlpha(True)
        gart.addChildNode(paint, None)

        # --- BORDER group : border / border-shade inherit alpha
        gbor = doc.createNode("BORDER", "grouplayer")
        root.addChildNode(gbor, None)
        border = doc.createNode("border", "paintlayer")
        full(border, border_bytes[cell["element"]])
        gbor.addChildNode(border, None)
        shade = doc.createNode("border-shade (inherit alpha)", "paintlayer")
        shade.setInheritAlpha(True)
        gbor.addChildNode(shade, None)

        # --- corner-number marbles (top-right + bottom-left, number inset) ---
        cn = doc.createNode("corner-number", "paintlayer")
        cn.setPixelData(QByteArray(rd(os.path.join(BADGES, cell["badge"]))), 0, 0, W, H)
        root.addChildNode(cn, None)

        # --- GUIDES group (hidden) : trim/safe/window lines
        gg = doc.createNode("GUIDES (hide before print)", "grouplayer")
        root.addChildNode(gg, None)
        gl = doc.createNode("trim-safe-window", "paintlayer")
        full(gl, guide_bytes)
        gg.addChildNode(gl, None)
        gg.setVisible(False)

        doc.setName(name)
        path = os.path.join(OUT, cell["filename"])
        doc.saveAs(path)
        doc.close()
        done += 1

    # leave a sentinel so we can verify completion (stdout is not surfaced)
    open(os.path.join(ROOT, "_kra_build_done.txt"), "w").write("built %d kra files\n" % done)
