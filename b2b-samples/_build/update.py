# update_link.py: one link change for the B2B samples gallery, run by the public repo's gallery-link workflow (Benedict, Oct 22: "make it
# easier to replace links and ill do it myself", no server). Lives here; publish_gallery.sh copies it to the repo as _build/update.py.
# Sets the slot's share link and name in live/final/links.json, pulls that design's four customizer pictures into live/final/<slot>/,
# rebuilds index.html + gallery.html + thumbs. An empty url takes the slot back to empty.
#   GALLERY_ROOT=b2b-samples python3 b2b-samples/_build/update.py --key derse-classic-1 --url <share link> --name "Tile Pattern"
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.environ["GALLERY_ROOT"]; sys.path.insert(0, HERE)
import make_final_gallery_pictures as pics
a = argparse.ArgumentParser(); a.add_argument("--key", required=True); a.add_argument("--url", default=""); a.add_argument("--name", default=""); a = a.parse_args()
if not re.fullmatch(r"(abbvie|derse|fourloko|placer|caretrust)-(classic|core|street)-\d+", a.key): sys.exit("unknown slot " + a.key)
links = json.load(open(pics.LINKS)); url = a.url.strip(); name = a.name.strip()[:60]
if url:
    cid = pics.config_id(url); model = pics.fetch(cid).get("model", "")
    want = "classic-zero" if "-classic-" in a.key else "court-zero-lowtop"   # Street slots (Placer) have no 3D yet
    if model != want: sys.exit(f"that design is a {model}, this slot is {want}")
    links[a.key] = {"url": f"https://shoezero.com/pages/share-design/?model={model}&configId={cid}", "name": name or (links.get(a.key) or {}).get("name", ""), "model": model}
else:
    links.pop(a.key, None)
print(a.key, pics.build(a.key, links))
tmp = pics.LINKS + ".tmp"; json.dump(links, open(tmp, "w"), indent=1); os.replace(tmp, pics.LINKS)
subprocess.run([sys.executable, os.path.join(HERE, "gallery.py")], check=True, env={**os.environ, "GALLERY_ROOT": ROOT})
