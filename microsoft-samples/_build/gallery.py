# Microsoft design gallery (Benedict, 2026-10-20). Rebuild: python3 gallery.py -> gallery.html + index.html (served at localhost:8791).
# Oct 21 (Benedict): only Conrad's FINAL designs (Slack #b2b-clients, Microsoft thread, Oct 21 10:33), in 2D, sorted
# brand > model > Minimal / Creative rows; every design gets an "Open in 3D customizer" link so Benedict edits it himself;
# no previous / next design buttons. Pictures: scripts/make_final_gallery_pictures.py -> live/final/<slot>/; links: live/final/links.json.
# No print file or file names on the page: it is also for showing customers.
import os, html, json, re
HERE = os.environ.get("GALLERY_ROOT") or os.path.dirname(os.path.abspath(__file__))   # GALLERY_ROOT: run from the public repo's _build/ (GitHub Action)
TEMPLATE = next(p for p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "gallery-template.html"), f"{HERE}/gallery-template.html") if os.path.exists(p))
BLANK = {"Classic": "https://shoezero.com/products/classic-zero", "Core": "https://shoezero.com/products/core-zero-low-tops"}   # an empty white shoe
# Each slot: ("label", "slot key"). The slot's 3D link and name live in live/final/links.json, which Benedict edits from the
# local page (serve.py). Its pictures are in live/final/<slot key>/ (scripts/make_final_gallery_pictures.py). No pictures = an empty slot.
CURRENT = [
    ("SQL", [
        ("Classic", [("Minimal", [("a", "sql-classic-minimal-1"), ("b", "sql-classic-minimal-2")]),
                     ("Creative", [("Wave", "sql-classic-creative-1"), ("Square", "sql-classic-creative-2"), ("Little Square", "sql-classic-creative-3")])]),
        ("Core", [("Minimal", [("Blue Heel, SQL Pill", "sql-core-minimal-1"), ("Blue Panels, SQL Pill", "sql-core-minimal-2")]),
                  ("Creative", [("a", "sql-core-creative-1"), ("b", "sql-core-creative-2")])]),
    ]),
    ("Fabric", [
        ("Classic", [("Minimal", [("a", "fabric-classic-minimal-1"), ("b", "fabric-classic-minimal-2")]),
                     ("Creative", [("Wave", "fabric-classic-creative-1"), ("See Stripe", "fabric-classic-creative-2"), ("Stripe V2", "fabric-classic-creative-3")])]),
        ("Core", [("Minimal", [("Teal Heel, F Logo", "fabric-core-minimal-1"), ("Teal Panels, F Logo", "fabric-core-minimal-2")]),
                  ("Creative", [("a", "fabric-core-creative-1"), ("b", "fabric-core-creative-2")])]),
    ]),
]
CONCEPTS = []  # list end marker: design-review-gate.sh reads the designs between CURRENT and CONCEPTS
LINKS = json.load(open(f"{HERE}/live/final/links.json"))
from PIL import Image
import numpy as np
os.makedirs(f"{HERE}/live/thumbs", exist_ok=True)   # no leading underscore: GitHub Pages skips "_" folders (Oct 20 publish, 4 broken covers)
def flat(path):
    im = Image.open(f"{HERE}/{path}")
    if im.mode in ("RGBA", "LA", "P"):   # customizer snapshots are see-through: put them on white
        im = im.convert("RGBA"); bg = Image.new("RGBA", im.size, (235, 235, 235, 255)); bg.alpha_composite(im); im = bg   # same light grey as the concept photos' floor
    return im.convert("RGB")
def framed(path, out, w):
    """the shoe cropped out of its background and set in the same 16:9 frame, same margin, for every picture (Benedict, Oct 21:
    "crop the pictures ... why is this so high up"). The background is measured per row from the picture's left and right edges, so the
    concept photos' grey floor gradient is not taken for shoe."""
    if os.path.exists(f"{HERE}/{out}") and os.path.getmtime(f"{HERE}/{path}") <= os.path.getmtime(f"{HERE}/{out}"): return out
    im = flat(path); a = np.asarray(im).astype(int)
    row_bg = np.median(np.concatenate([a[:, :12], a[:, -12:]], 1), 1)          # one background colour per row
    diff = np.abs(a - row_bg[:, None]).sum(-1) > 36
    diff = diff & (np.convolve(diff.mean(1), np.ones(5) / 5, "same") > 0.01)[:, None]   # rows with real content only (drops stray noise)
    ys, xs = np.nonzero(diff)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); bw, bh = x1 - x0, y1 - y0
        fw = max(bw * 1.08, bh * 1.14 * 16 / 9); fh = fw * 9 / 16                 # 4 % margin at the sides, frame 16:9: a shoe is wide, 4:3 left a grey band under it (Benedict, Oct 22)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bgc = tuple(int(v) for v in np.median(row_bg, 0))
        canvas = Image.new("RGB", (int(fw), int(fh)), bgc)
        canvas.paste(im, (int(fw / 2 - cx), int(fh / 2 - cy)))
        # fill outside the original picture with that row's own background so the edges do not show
        im = canvas
    im.thumbnail((w, w)); im.save(f"{HERE}/{out}", quality=90); return out
import hashlib
def stamped(out):
    """the picture's path plus a fingerprint of its content, so a slot whose picture changed (a new link pasted) is never shown from the
    browser's cache (Oct 22: Benedict saw the test design still sitting in the SQL Pill slot after the link changed)"""
    return out + "?v=" + hashlib.md5(open(f"{HERE}/{out}", "rb").read()).hexdigest()[:8]
thumb = lambda path: stamped(framed(path, f"live/thumbs/{path.replace('/', '__').rsplit('.', 1)[0]}.jpg", 640))
big = lambda path: stamped(framed(path, f"live/thumbs/{path.replace('/', '__').rsplit('.', 1)[0]}-full.jpg", 1600))
TITLE = "Microsoft Final Designs"
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
data = {"brands": []}; n = 0
for brand, models in CURRENT:
    B = {"name": brand, "slug": slug(brand), "models": []}
    for model, rows in models:
        M = {"name": f"{brand} {model}", "slug": slug(f"{brand} {model}"), "rows": []}
        for style, items in rows:
            R = {"name": style, "designs": []}
            base = f"{brand.lower()}-{model.lower()}-{style.lower()}-"; listed = {k for _, k in items}
            items = list(items) + [(k[len(base):], k) for k in sorted(LINKS) if k.startswith(base) and k not in listed]   # extra slots added from the page (Oct 22: "add another one")
            for i, (label, key) in enumerate(items, 1):
                entry = LINKS.get(key) or {}; label = entry.get("name") or label; url = entry.get("url", "")
                folder = f"live/final/{key}"
                files = sorted(f for f in os.listdir(f"{HERE}/{folder}") if f.endswith(".png")) if os.path.isdir(f"{HERE}/{folder}") else []
                name = f"{brand} {model} {style} {i}" + (f": {label}" if files else "")
                if not files:   # Conrad's empty slot
                    R["designs"].append({"empty": True, "key": key, "short": f"{style} {label}", "name": name, "link": BLANK[model], "url": ""}); continue
                n += 1
                files = [f for f in files if not f.endswith("-hires.png")]
                pick = lambda f: f[:-4] + "-hires.png" if os.path.exists(f"{HERE}/{folder}/{f[:-4]}-hires.png") else f   # the 3600 px viewer render when we have one (scripts/hires_capture.js)
                views = [{"label": f[3:-4], "full": big(f"{folder}/{pick(f)}"), "thumb": thumb(f"{folder}/{pick(f)}"), "cover": f.startswith("01-")} for f in files]
                R["designs"].append({"n": n, "key": key, "slug": slug(name), "name": name, "short": label, "cover": views[0]["thumb"], "views": views,
                                     "url": url, "link": url,   # no 3D link = a 2D-only design: the page says so and shows no 3D button (Pam, Oct 22: a 3D link opened a blank product shoe)
                                     "linkLabel": "Open in 3D customizer" if url else ""})
            M["rows"].append(R)
        B["models"].append(M)
    data["brands"].append(B)
page = open(TEMPLATE).read()
page = page.replace("/*DATA*/null", json.dumps(data).replace("</", "<\\/")).replace("__COUNT__", str(n)).replace("__TITLE__", html.escape(TITLE))
for f in ("gallery.html", "index.html"): open(f"{HERE}/{f}", "w").write(page)
print(f"{n} designs -> gallery.html + index.html")
