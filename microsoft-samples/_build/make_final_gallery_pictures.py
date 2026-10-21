# Pictures for the final-designs gallery (Benedict, Oct 21: "improve the Microsoft sample designs gallery so it only includes these
# final designs ... shown in 2D"). Conrad's final list: Slack #b2b-clients, Microsoft thread, Oct 21 10:33.
# Writes live/final/<slot>/NN-<side>.png: a slot with a 3D link in live/final/links.json gets the customizer's own saved snapshots;
# a slot without one gets its concept picture (+ back view when one exists), or nothing (an empty slot).
# Benedict adds / changes links himself on the local gallery page (serve.py POST /api/link), which runs this with --only <slot>.
# Run: python3 scripts/make_final_gallery_pictures.py [--only <slot>]   (system python, no numpy)
import json, os, re, shutil, subprocess, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.environ.get("GALLERY_ROOT") or os.path.dirname(HERE); OUT = f"{ROOT}/live/final"; LINKS = f"{OUT}/links.json"
API = "https://customizer-backend-prod.fly.dev/api/threedium/configurations/"   # curl User-Agent: Python's default gets 403
SNAP_SIDES = {"image1": "01-Outside", "image2": "02-Inside", "image3": "03-Top", "image4": "04-Back"}
CONCEPTS = {     # slot: concept picture (side), used while the slot has no 3D link
    "sql-classic-creative-2": "concepts/concepts-r20/sql-classic-minimal-N1.png",       # "square" (Conrad's screenshot 1 = N1, not P2)
    "sql-classic-creative-3": "concepts/concepts-r15/sql-classic-bold.png",             # "little square"
    "fabric-classic-creative-2": "concepts/concepts-r15/fabric-classic-bold.png",       # "see stripe"
    "fabric-classic-creative-3": "concepts/concepts-r18/fabric-classic-bold-J1.png"}    # "stripe v2"

# Benedict, Oct 22: "the shoes are in different direction ... Make them all look at the right". The customizer snapshots show the shoe
# toe-right; the concept photos show it toe-left, so those are mirrored. Mirroring flips the logos and words too, so each glyph
# (tongue logo, heel logo, any word) is found inside a region hint and pasted back un-mirrored: a logo on a flat patch of tongue or
# heel tab survives the swap with no seam. Region hints are (x0, y0, x1, y1) on the 1254 px concept picture.
FLIP = {
    "sql-classic-creative-2":    {"tongue": (680, 360, 830, 480), "heel": (1040, 450, 1210, 640)},
    "sql-classic-creative-3":    {"tongue": (680, 380, 830, 490), "heel": (1040, 450, 1210, 640), "word": (1000, 735, 1170, 800)},
    "fabric-classic-creative-2": {"tongue": (680, 360, 820, 450), "heel": (1040, 450, 1210, 640)},
    "fabric-classic-creative-3": {"tongue": (680, 380, 820, 470), "heel": (1040, 450, 1210, 640)},
}
def glyph_box(a, region, kind):
    """tight box of the glyph inside the region: a coloured mark on the white tongue, a white mark inside the coloured heel tab, or a
    coloured word on the white side"""
    import numpy as np
    from scipy import ndimage as ndi
    x0, y0, x1, y1 = region; r = a[y0:y1, x0:x1].astype(int); sat = r.max(-1) - r.min(-1)
    if kind == "heel":
        tab = ndi.binary_erosion(ndi.binary_fill_holes(sat > 50), iterations=5)       # inside the coloured tab
        m = tab & (r.min(-1) > 170)                                                     # the white glyph on it
    else:
        m = sat > 60
    m = ndi.binary_opening(m, iterations=1)
    ys, xs = np.nonzero(m)
    if not len(xs): return None
    pad = 5; return (x0 + max(xs.min() - pad, 0), y0 + max(ys.min() - pad, 0), x0 + min(xs.max() + pad + 1, x1 - x0), y0 + min(ys.max() + pad + 1, y1 - y0))

def mirror_keep_glyphs(src, dst, hints):
    import numpy as np
    from PIL import Image, ImageOps
    im = Image.open(src).convert("RGB"); a = np.asarray(im); W = im.width
    out = ImageOps.mirror(im); found = {}
    for kind, region in hints.items():
        box = glyph_box(a, region, kind)
        if box is None: continue
        bx0, by0, bx1, by1 = box; out.paste(im.crop(box), (W - bx1, by0)); found[kind] = box
    out.save(dst); return found

def config_id(url):
    """the configId out of a shoezero.com share link (or a bare id); raises on anything else"""
    url = url.strip()
    if re.fullmatch(r"\d{5,8}", url): return url
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    cid = (q.get("configId") or [""])[0]
    if not re.fullmatch(r"\d{5,8}", cid): raise ValueError("that link has no configId: copy the share link from the 3D customizer")
    return cid

def fetch(cid):
    r = subprocess.run(["curl", "-s", "-A", "curl/8", API + cid], capture_output=True, text=True)
    try: j = json.loads(r.stdout)["data"]["configuration_data"]
    except Exception: raise ValueError(f"the customizer has no design {cid}")
    return j

def build(slot, links):
    d = f"{OUT}/{slot}"; tmp = d + ".new"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    entry = links.get(slot) or {}
    if entry.get("og"):   # Benedict, Oct 22: "use the og image": the design's original 2D mockup renders (the 8-view mockups/ folder), toe-right views
        from PIL import Image
        for src, side in (("Right_Outside", "01-Outside"), ("Right_Inside", "02-Inside"), ("Top", "03-Top"), ("Back", "04-Back")):
            f = f"{ROOT}/{entry['og']}/{src}.jpg"
            if os.path.exists(f): Image.open(f).convert("RGB").save(f"{tmp}/{side}.png")
    elif entry.get("url"):
        j = fetch(config_id(entry["url"]))
        for k, side in SNAP_SIDES.items():
            u = j.get("snapshots", {}).get(k)
            if u: subprocess.run(["curl", "-s", "-A", "curl/8", "-o", f"{tmp}/{side}.png", u], check=True)
        if not os.listdir(tmp): raise ValueError("that design has no saved pictures yet: press Save in the 3D customizer first")
        entry["model"] = j.get("model", entry.get("model", ""))
    elif slot in CONCEPTS:
        src = CONCEPTS[slot]
        if slot in FLIP: print("   flipped", slot, mirror_keep_glyphs(f"{ROOT}/{src}", f"{tmp}/01-Outside.png", FLIP[slot]))
        elif os.path.exists(f"{ROOT}/{src}"): shutil.copy(f"{ROOT}/{src}", f"{tmp}/01-Outside.png")   # concept pictures are not in the public repo
        if os.path.exists(f"{ROOT}/{src[:-4]}-back.png"): shutil.copy(f"{ROOT}/{src[:-4]}-back.png", f"{tmp}/04-Back.png")
    # iCloud quirk (Oct 22): renaming a folder over a deleted one brought the old one back as "<slot> 2", so files are moved one by one
    if os.path.isdir(d):
        for f in os.listdir(d): os.remove(os.path.join(d, f))
    else: os.makedirs(d)
    for f in os.listdir(tmp): shutil.move(os.path.join(tmp, f), os.path.join(d, f))
    shutil.rmtree(tmp, ignore_errors=True)
    if not os.listdir(d): os.rmdir(d)
    return sorted(os.listdir(d)) if os.path.exists(d) else []

if __name__ == "__main__":
    links = json.load(open(LINKS))
    slots = [sys.argv[sys.argv.index("--only") + 1]] if "--only" in sys.argv else sorted(set(links) | set(CONCEPTS))
    for slot in slots: print(slot, build(slot, links))
    tmp = LINKS + ".tmp"; json.dump(links, open(tmp, "w"), indent=1); os.replace(tmp, LINKS)   # atomic: never a half-written links.json
