#!/usr/bin/env python3
"""Download all Airtable attachments locally so the prototype does not rely on
expiring signed URLs. Uses curl (macOS python has SSL cert issues)."""
import json, pathlib, subprocess

BASE = pathlib.Path(__file__).parent
RAW = BASE / "raw"
ASSETS = BASE / "assets"
ASSETS.mkdir(exist_ok=True)

SOURCES = {
    "gb3_gp3": ("Attachments",),
    "gb5_gb7": ("Attachments",),
    "locations": ("Remark",),
}

def curl_download(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return "cached"
    subprocess.run(
        ["curl", "-s", "-L", "-o", str(dest), url],
        check=True,
    )
    return "downloaded"

manifest = {}
for slug, attach_fields in SOURCES.items():
    records = json.load(open(RAW / f"{slug}.json"))
    sub = ASSETS / slug
    sub.mkdir(exist_ok=True)
    for rec in records:
        rid = rec["id"]
        f = rec["fields"]
        saved = []
        for field in attach_fields:
            for i, att in enumerate(f.get(field, [])):
                atype = att.get("type", "")
                if atype.startswith("image/"):
                    # prefer full-size thumbnail (stable enough), fall back to url
                    url = att.get("thumbnails", {}).get("full", {}).get("url") or att["url"]
                    ext = ".jpg" if "jpeg" in atype else ".png"
                elif atype.startswith("video/"):
                    url = att["url"]
                    ext = ".mp4"
                else:
                    url = att["url"]
                    ext = pathlib.Path(att.get("filename", "file")).suffix or ".bin"
                fname = f"{rid}_{i}{ext}"
                dest = sub / fname
                try:
                    status = curl_download(url, dest)
                except subprocess.CalledProcessError:
                    status = "FAILED"
                saved.append({"file": f"assets/{slug}/{fname}", "type": atype, "status": status})
        manifest[rid] = saved

json.dump(manifest, open(BASE / "assets_manifest.json", "w"), ensure_ascii=False, indent=2)
total = sum(len(v) for v in manifest.values())
ok = sum(1 for v in manifest.values() for x in v if x["status"] != "FAILED")
print(f"Attachments processed: {total}, ok: {ok}")
