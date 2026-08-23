#!/usr/bin/env python3
"""Build a clean, categorized data file for the prototype website from the raw
Airtable dumps. Images are mapped to the locally-downloaded copies."""
import json, pathlib, glob

BASE = pathlib.Path(__file__).parent
RAW = BASE / "raw"

# ---- Proposed categories for DIY parts -------------------------------------
# key = normalized 零件位置, value = category id
CATEGORY_MAP = {
    # 燈光系統
    "頭燈膽": "lighting", "頭燈": "lighting", "尾燈": "lighting",
    "尾車牌燈": "lighting", "車尾頂brake燈": "lighting", "房燈": "lighting",
    "冷氣燈": "lighting",
    # 引擎‧油水‧保養
    "偈油": "engine", "波箱油": "engine", "換COIL 火咀": "engine",
    "冷氣隔": "engine", "風隔": "engine", "電池": "engine",
    # 電子‧音響
    "車頭喇叭": "electronics", "車尾喇叭": "electronics", "車響安": "electronics",
    "車機": "electronics", "Fuse 盒": "electronics", "車匙換電": "electronics",
    "點煙器插座面板": "electronics",
    # 車身‧外觀
    "頭bumper": "body", "尾bumper": "body", "側鏡": "body", "水潑": "body",
    "死氣喉": "body", "洗天風/蝴蝶掩": "body", "車頭太陽擋": "body",
    # 內飾‧門板
    "司機門板": "interior", "尾門板": "interior", "中門門板": "interior",
    "拆A柱": "interior", "踏板": "interior",
    # 工具‧其他
    "升車": "tools", "GB3 裝cam片": "tools",
}

CATEGORIES = [
    {"id": "lighting",    "name": "燈光系統",    "icon": "\U0001F4A1"},
    {"id": "engine",      "name": "引擎‧油水‧保養", "icon": "\U0001F6E2\uFE0F"},
    {"id": "electronics", "name": "電子‧音響",    "icon": "\U0001F50C"},
    {"id": "body",        "name": "車身‧外觀",    "icon": "\U0001F697"},
    {"id": "interior",    "name": "內飾‧門板",    "icon": "\U0001FA91"},
    {"id": "tools",       "name": "工具‧其他",    "icon": "\U0001F527"},
]

def local_images(slug, rid):
    files = sorted(glob.glob(str(BASE / "assets" / slug / f"{rid}_*")))
    out = []
    for f in files:
        rel = "assets/" + slug + "/" + pathlib.Path(f).name
        ext = pathlib.Path(f).suffix.lower()
        out.append({"path": rel, "video": ext == ".mp4"})
    return out

def build_diy(slug):
    records = json.load(open(RAW / f"{slug}.json"))
    items = []
    for r in records:
        f = r["fields"]
        part = (f.get("零件位置") or "").strip()
        cat = CATEGORY_MAP.get(part, "tools")
        imgs = local_images(slug, r["id"])
        items.append({
            "id": r["id"],
            "part": part,
            "category": cat,
            "spec": (f.get("型號") or "").strip(),
            "club_spec": (f.get("車會提供型號") or "").strip(),
            "interval": (f.get("參考更換周期") or "").strip(),
            "video": (f.get("影片教學") or "").strip(),
            "images": [i["path"] for i in imgs if not i["video"]],
        })
    # sort by category order then part name
    order = {c["id"]: n for n, c in enumerate(CATEGORIES)}
    items.sort(key=lambda x: (order.get(x["category"], 99), x["part"]))
    return items

# Manual image overrides for locations that don't have an Airtable attachment.
# key = record id, value = list of local image paths (relative to Honda/).
# Used e.g. for 車會會址 where the club logo was supplied directly, not via Airtable.
MANUAL_LOC_IMAGES = {
    "recQepS3t6IzlBgQ4": ["assets/locations/39761872-4700-4c3f-aeaf-d4fed29685b4.JPG"],  # 車會會址
}

# The club's own address is pinned to the top of 推薦地點; everything else keeps the
# order Airtable returns. Matched by record id, with a name fallback in case the
# record is ever recreated with a new id.
CLUB_LOCATION_ID = "recQepS3t6IzlBgQ4"
CLUB_LOCATION_NAME = "車會會址"

# 推薦地點 filter pills. The category itself comes from the Airtable 類型 field; this
# list only fixes the display order and picks an icon. A value that is not listed here
# still works - it just lands in 其他 - so adding a new option in Airtable never breaks
# the site, it only means the pill has no icon until it is added below.
LOCATION_CATEGORIES = [
    ("車房／綜合維修",     "\U0001F527"),  # wrench
    ("呔鈴／膠輪",         "\U0001F6DE"),  # wheel
    ("四輪定位／底盤避震", "\U0001F4D0"),  # triangular ruler
    ("電池",               "\U0001F50B"),  # battery
    ("噴油／車身",         "\U0001F3A8"),  # palette
    ("車會",               "\U0001F3E0"),  # house
]
OTHER_LOCATION_CATEGORY = "其他"

def build_locations():
    records = json.load(open(RAW / "locations.json"))
    items = []
    skipped = []
    for r in records:
        f = r["fields"]
        # Blank rows in Airtable (a row added but not yet filled in) would otherwise
        # render as an empty card on the site. A location with no name is useless,
        # so drop it and report it instead.
        if not (f.get("Name") or "").strip():
            skipped.append(r["id"])
            continue
        imgs = local_images("locations", r["id"])
        images = [i["path"] for i in imgs if not i["video"]]
        # apply manual overrides (only include if the file actually exists)
        for p in MANUAL_LOC_IMAGES.get(r["id"], []):
            if (BASE / p).exists() and p not in images:
                images.insert(0, p)
        # Airtable values arrive with stray spaces (e.g. " 電池"), which would show up
        # as a second, separate pill. Strip before using it as a category key.
        category = (f.get("類型") or "").strip()
        items.append({
            "id": r["id"],
            "name": (f.get("Name") or "").strip(),
            "category": category or OTHER_LOCATION_CATEGORY,
            "phone": (f.get("電話") or "").strip(),
            "address": (f.get("地址") or "").strip(),
            "gmap": (f.get("Google Map") or "").strip(),
            "amap": (f.get("高德地圖") or "").strip(),
            "waze": (f.get("WAZE") or "").strip(),
            "images": images,
            "videos": [i["path"] for i in imgs if i["video"]],
        })
    # list.sort is stable, so this only lifts the club address and leaves the rest as-is
    items.sort(key=lambda x: 0 if (x["id"] == CLUB_LOCATION_ID
                                   or x["name"] == CLUB_LOCATION_NAME) else 1)
    if skipped:
        print("Skipped blank location rows (no Name):", ", ".join(skipped))
    return items


def location_categories(items):
    """Filter pills for 推薦地點, in LOCATION_CATEGORIES order, skipping unused ones.
    Any 類型 value not in LOCATION_CATEGORIES is grouped under 其他, appended last."""
    used = {it["category"] for it in items}
    known = [name for name, _ in LOCATION_CATEGORIES]
    cats = [{"id": name, "name": name, "icon": icon}
            for name, icon in LOCATION_CATEGORIES if name in used]
    unknown = sorted(u for u in used if u not in known)
    if unknown:
        # keep them visible rather than silently hiding the locations
        for it in items:
            if it["category"] in unknown:
                it["category"] = OTHER_LOCATION_CATEGORY
        cats.append({"id": OTHER_LOCATION_CATEGORY,
                     "name": OTHER_LOCATION_CATEGORY, "icon": "\U0001F4CD"})
        print("類型 values not in LOCATION_CATEGORIES (grouped into 其他):",
              ", ".join(repr(u) for u in unknown))
    return cats

locations = build_locations()
# must run before the dump: it rewrites unrecognised 類型 values to 其他
loc_cats = location_categories(locations)

data = {
    "categories": CATEGORIES,
    "models": [
        {"id": "gb3_gp3", "name": "Freed GB3 / GP3", "years": "1代 (2008-2016)", "items": build_diy("gb3_gp3")},
        {"id": "gb5_gb7", "name": "Freed GB5 / GB7", "years": "2代 (2016-)", "items": build_diy("gb5_gb7")},
    ],
    "locations": locations,
    "location_categories": loc_cats,
}

out = BASE / "site_data.json"
json.dump(data, open(out, "w"), ensure_ascii=False, indent=2)

# uncategorized check
uncat = set()
for m in data["models"]:
    for it in m["items"]:
        if it["part"] not in CATEGORY_MAP:
            uncat.add(it["part"])
print("Wrote", out.name)
print("GB3/GP3 items:", len(data["models"][0]["items"]))
print("GB5/GB7 items:", len(data["models"][1]["items"]))
print("Locations:", len(data["locations"]))
for c in loc_cats:
    n = sum(1 for l in locations if l["category"] == c["id"])
    print(f"  {c['icon']} {c['name']}: {n}")
if uncat:
    print("Parts falling back to 工具‧其他 (not explicitly mapped):", uncat)
