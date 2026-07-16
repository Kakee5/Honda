#!/usr/bin/env python3
import os, json, time, urllib.parse, pathlib, subprocess

TOKEN = None
env = pathlib.Path(__file__).parent / ".env"
for line in env.read_text().splitlines():
    if line.startswith("AIRTABLE_TOKEN="):
        TOKEN = line.split("=", 1)[1].strip()

SOURCES = [
    ("GB3/GP3 DIY 工具", "appKQD0JB0oRvzsfG", "tblODDv9VmF89Cnbb", "gb3_gp3"),
    ("常用推薦地點",     "appli7Gu16H0SEicv", "tblUkhYUJuw0PB6rc", "locations"),
    ("GB5/GB7 DIY 工具", "appmYWVQfbt76HWs2", "tblODDv9VmF89Cnbb", "gb5_gb7"),
]

outdir = pathlib.Path(__file__).parent / "raw"
outdir.mkdir(exist_ok=True)

def fetch(base, table):
    records, offset = [], None
    while True:
        q = {"pageSize": "100"}
        if offset:
            q["offset"] = offset
        url = f"https://api.airtable.com/v0/{base}/{table}?" + urllib.parse.urlencode(q)
        out = subprocess.check_output(
            ["curl", "-s", "-H", f"Authorization: Bearer {TOKEN}", url]
        )
        data = json.loads(out)
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        time.sleep(0.25)
    return records

for name, base, table, slug in SOURCES:
    recs = fetch(base, table)
    (outdir / f"{slug}.json").write_text(json.dumps(recs, ensure_ascii=False, indent=2))
    print(f"{name}: {len(recs)} records -> raw/{slug}.json")
