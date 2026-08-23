#!/usr/bin/env python3
"""Download all Airtable attachments locally so the prototype does not rely on
expiring signed URLs. Uses curl (macOS python has SSL cert issues)."""
import json, pathlib, subprocess
from imgopt import optimize_image, human

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
    subprocess.run(
        ["curl", "-s", "-L", "-o", str(dest), url],
        check=True,
    )

def existing_variant(sub, stem):
    """Return an already-downloaded file for this attachment, whatever its
    extension. optimize_image() may have turned a .png into a .jpg, so matching
    on the exact extension would re-download the full-size original every sync.
    """
    for p in sorted(sub.glob(stem + ".*")):
        if p.is_file() and p.stat().st_size > 0 and not p.name.endswith(".opt.tmp"):
            return p
    return None

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
                stem = f"{rid}_{i}"
                found = existing_variant(sub, stem)
                if found:
                    dest, status = found, "cached"
                else:
                    dest = sub / f"{stem}{ext}"
                    try:
                        curl_download(url, dest)
                        status = "downloaded"
                    except subprocess.CalledProcessError:
                        status = "FAILED"
                    if status == "downloaded" and atype.startswith("image/"):
                        result = optimize_image(dest)
                        if result:
                            dest, before, after = result
                            if after < before:
                                print(f"  optimised {dest.name}:"
                                      f" {human(before)} -> {human(after)}")
                saved.append({"file": f"assets/{slug}/{dest.name}",
                              "type": atype, "status": status})
        manifest[rid] = saved

json.dump(manifest, open(BASE / "assets_manifest.json", "w"), ensure_ascii=False, indent=2)
total = sum(len(v) for v in manifest.values())
ok = sum(1 for v in manifest.values() for x in v if x["status"] != "FAILED")
print(f"Attachments processed: {total}, ok: {ok}")
