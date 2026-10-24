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
CONCEPTS = {}   # no concept-picture slots in the B2B gallery
FLIP = {}
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
