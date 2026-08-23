# Freed Spike 交流區 — Project Context (Handoff)

This is the website for the **Freed Spike 交流區** Honda Freed car club (Hong Kong).
It was revamped out of Airtable into a static, user-friendly site. This file gives
you (Kiro) the full context to keep working on the project.

## What this project is
- A static website: DIY maintenance guides + recommended shops/locations for club members.
- Source of truth for content is **Airtable** (3 bases). The site is a generated,
  read-only, member-friendly view of that data.
- Hosted free on **GitHub Pages**.

## Live site & repo
- Repo: `https://github.com/Kakee5/Honda` (GitHub user: `Kakee5`)
- Live site: `https://kakee5.github.io/Honda/`
- Default branch: `main`

## Data source (Airtable)
Personal Access Token lives in `Honda/.env` as `AIRTABLE_TOKEN` (NOT committed — see setup).
Three bases:
| Base name | Base ID | Table ID | Notes |
|---|---|---|---|
| Freed GB3/GP3 DIY 工具 | `appKQD0JB0oRvzsfG` | `tblODDv9VmF89Cnbb` | DIY parts, 1st-gen chassis |
| 常用推薦地點 | `appli7Gu16H0SEicv` | `tblUkhYUJuw0PB6rc` | recommended shops/locations |
| Freed GB5/GB7 DIY 工具 | `appmYWVQfbt76HWs2` | `tblODDv9VmF89Cnbb` | DIY parts, 2nd-gen chassis |

Note: both DIY bases use the same table id — key data by base, not table id.

### Fields
- DIY tables: `零件位置` (part), `型號` (spec), `車會提供型號` (club-recommended brand),
  `參考更換周期` (interval), `影片教學` (YouTube link), `Attachments` (images).
- Locations table: `Name`, `電話`, `地址`, `Google Map`, `高德地圖`, `WAZE`, `Remark` (images/video),
  `類型` (service category — drives the 推薦地點 filter pills, see below).

### DIY categories (assigned in build_data.py CATEGORY_MAP)
lighting 燈光系統 / engine 引擎‧油水‧保養 / electronics 電子‧音響 /
body 車身‧外觀 / interior 內飾‧門板 / tools 工具‧其他.
Unmapped parts fall back to `tools`.

### Location categories (Airtable 類型 field → filter pills)
The 推薦地點 tab has filter pills mirroring the DIY ones. Unlike DIY (where the category is
*derived* from `零件位置` via `CATEGORY_MAP`), a location's category **is the Airtable string
itself** — there is no mapping table. `LOCATION_CATEGORIES` in `build_data.py` only fixes the
display order and picks an icon:

| 類型 (Airtable single select) | icon | count at last sync |
|---|---|---|
| 車房／綜合維修 | 🔧 | 4 |
| 呔鈴／膠輪 | 🛞 | 4 |
| 四輪定位／底盤避震 | 📐 | 3 |
| 電池 | 🔋 | 2 |
| 噴油／車身 | 🎨 | 1 |
| 車會 | 🏠 | 1 |

Why it is built this way:
- **The user maintains 類型 in Airtable, so adding a location needs no code change.** This was a
  deliberate choice over keyword-inference from the shop name (店名 like 明哥 / 噴油平哥 have no
  usable keyword) and over a hard-coded record-id map (every new shop would need an edit + push).
- **A value not in `LOCATION_CATEGORIES` is grouped into 其他 (📍) and printed as a warning, not
  hidden.** So a typo in Airtable can never make a location silently vanish from the site. If a
  new option appears, add it to `LOCATION_CATEGORIES` to give it an icon and a sort position.
- **Always `.strip()` the value.** Airtable data contains leading spaces — at last sync both
  battery shops had `" 電池"`. Without the strip you get two separate pills for one category.
  (Same trap exists on `電話`: 福如's phone is stored as `" 2365 0596"`.)
- `類型` is a **single select**, so a shop that does several things sits in one bucket only
  (福如 does 電池 + 冷氣; Alignment Formula does 定位 + 避震 + 底盤). Multi-select was suggested
  and the user chose single — do not re-litigate this.
- Pills only filter. They do not reorder: 車會會址 stays pinned first, everything else keeps
  Airtable order.
- `location_categories(items)` runs **before** the JSON dump because it rewrites unknown
  categories in place.

## File structure (in repo root = Honda/)
- `index.html` — the whole site (embedded CSS + JS). Loads `data.js`.
- `data.js` — `window.SITE_DATA = {...}` generated from `site_data.json`.
- `site_data.json` — clean categorized data (build output).
- `raw/*.json` — raw Airtable dumps (backup).
- `assets/{gb3_gp3,gb5_gb7,locations}/` — downloaded images/videos (so the site
  never depends on Airtable's expiring signed URLs).
- `assets/brand/hero.jpg` — the header banner illustration. Hand-added, not from Airtable.
- `assets/maint/` — hand-added maintenance photos. `download_assets.py` never touches
  `brand/` or `maint/`, so a re-sync cannot wipe them.
- `fetch_airtable.py` — pulls records from the 3 bases into `raw/`.
- `download_assets.py` — downloads attachments locally into `assets/`.
- `build_data.py` — builds `site_data.json` with categories + local image paths.
  Contains `MANUAL_LOC_IMAGES` override (club logo used as 車會會址 photo),
  `LOCATION_CATEGORIES` (推薦地點 pill order + icons), and skips blank Airtable rows (no `Name`).
  Prints a per-category location count so a bad 類型 value is visible in the build output.
- `make_favicon.js` — generates favicons from the club logo (uses `sharp`).
- `.env` — Airtable token (gitignored, must be recreated on each machine).

## Re-sync pipeline (run after any Airtable change)
**This project is now maintained on the Windows machine only.** The Mac is no longer used, so
treat the PowerShell commands below as the canonical pipeline. Copy-paste this block:

```powershell
$env:PYTHONUTF8 = "1"                 # mandatory, see quirk 1 below
$git = "$env:ProgramFiles\Git\cmd\git.exe"   # git is not on PATH, see quirk 2

python fetch_airtable.py              # 1. pull latest from Airtable
python download_assets.py             # 2. download new images/videos (auto-compressed)
python build_data.py                  # 3. rebuild categorized site_data.json
# 4. regenerate data.js:
python -c "import pathlib; d=open('site_data.json',encoding='utf-8').read(); pathlib.Path('data.js').write_text('window.SITE_DATA = '+d+';\n', encoding='utf-8')"

# 5. commit & push (non-interactive, see quirk 3)
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE     = "never"
& $git add -A
& $git commit -F <utf-8 message file>   # see quirk 5 if the message contains Chinese
& $git push origin main
```

<details>
<summary>Historical: the original macOS commands (kept for reference only)</summary>

```bash
python3 fetch_airtable.py
python3 download_assets.py
python3 build_data.py
python3 -c "import pathlib; d=open('site_data.json').read(); pathlib.Path('data.js').write_text('window.SITE_DATA = '+d+';\n', encoding='utf-8')"
git add -A && git commit -m "sync Airtable" && git push origin main
```
</details>

## Windows / PowerShell quirks — read before running anything
Every one of these has broken a sync or a push before. They are not hypothetical.

### 1. Force UTF-8 or the scripts crash
Windows Python defaults to the `cp950` codec, which cannot encode some of the Chinese
characters in the Airtable data. `fetch_airtable.py` dies with
`UnicodeEncodeError: 'cp950' codec can't encode character ...`.
Fix: `$env:PYTHONUTF8 = "1"` once per shell session, and pass `encoding='utf-8'` explicitly when
reading `site_data.json` in the data.js step (both already in the pipeline block above).

Note `python`, not `python3`, on Windows. `curl` is built in at `C:\Windows\System32\curl.exe`,
so the scripts' subprocess calls work unchanged.

### 2. git is not on PATH
Git was installed with `winget install --id Git.Git -e` but its directory was never added to
PATH, so bare `git` fails with "無法辨識 'git' 詞彙". Call it by full path:
```powershell
$git = "$env:ProgramFiles\Git\cmd\git.exe"
& $git status
& $git add site_data.json data.js assets_manifest.json raw/*.json
& $git commit -m "sync Airtable"
```
Git identity is set locally in this repo (`Freed Spike <freedspike@users.noreply.github.com>`)
to match the existing history — do not rely on a global config being present.

### 3. Always push non-interactively — the GCM login hangs the agent terminal
GCM credentials for `Kakee5/Honda` are **already cached on this machine** (stored during the
first successful interactive login). So the only thing needed is to stop git from ever trying
to open the login UI. Set these two variables and push normally:
```powershell
$env:GIT_TERMINAL_PROMPT = "0"   # no terminal prompt
$env:GCM_INTERACTIVE     = "never"  # no GUI/browser prompt
& $git push origin main
```
Verified working: pushes complete immediately with `PUSH_EXIT=0`, no prompt, no hang.

**Why this matters:** if the login UI *is* triggered (i.e. you push without these variables and
the cache ever gets cleared), the git process **never returns**. The push may still complete
server-side, but the terminal stays blocked and every following command silently returns empty
output for several minutes. That already caused one false "push failed" diagnosis — the push had
actually succeeded. With the variables set, git fails fast with a clear error instead.

**Fallback if the credential cache is ever lost** (push errors with an auth failure): either run
the push in your own normal terminal, where the GCM prompt is interactive and works fine, or feed
a short-lived PAT through `GIT_ASKPASS`:
```powershell
# askpass.cmd (place OUTSIDE the repo, e.g. in $env:TEMP):
#   @echo off
#   echo %HONDA_TOKEN%
$env:HONDA_TOKEN         = "<short-lived PAT>"
$env:GIT_ASKPASS         = "$env:TEMP\askpass.cmd"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE     = "never"
& $git -c credential.helper= push https://x-access-token@github.com/Kakee5/Honda.git main
```
Delete the askpass file and revoke the token afterwards. Keeps the token out of git config, the
remote URL, and the repo. Note the PAT needs **Contents: Read and write** on `Kakee5/Honda`; a
token without it fails with `remote: Permission to Kakee5/Honda.git denied` / HTTP 403.

### 4. Never put Chinese text inside a helper .ps1
`powershell.exe` 5.1 reads `.ps1` files as ANSI unless they carry a UTF-8 BOM, so **any** Chinese
literal in a helper script gets mangled. Two ways this has already bitten:

- Hard-coded repo path → `文件` became `?辣`, and `Set-Location` failed with
  "找不到路徑，因為它不存在".
- Hard-coded commit message → the commit landed on GitHub as
  `sync Airtable: add YW??臬??游??摨? pin 頠???`, which then needed an amend + force push to fix.

Rules: keep helper scripts ASCII-only, and rely on the inherited working directory (the child
`powershell` starts in the cwd the tool call used, already the repo root — no `Set-Location`
needed at all).

### 5. Chinese commit messages must come from a UTF-8 file
Because of quirk 4, never pass a Chinese message with `git commit -m` from a script. Write the
message to a UTF-8 file (no BOM) and use `-F`:
```powershell
& $git commit -F "$env:TEMP\msg.txt"
```
Strip a possible BOM first — a BOM would end up as an invisible character at the start of the
subject line:
```powershell
python -c "import io,sys; p=sys.argv[1]; d=io.open(p,encoding='utf-8-sig').read(); io.open(p,'w',encoding='utf-8',newline='\n').write(d)" "$env:TEMP\msg.txt"
```
Verified working. To fix an already-pushed mangled message, `git commit --amend -F <file>` with
**nothing staged** (so the tree is untouched — compare `git rev-parse HEAD^{tree}` before and
after), then `git push --force-with-lease origin main`. Never plain `--force`.

### 6. Adding a nav tab can break the mobile layout
`.tabs-inner` is a flex row of `white-space:nowrap` tabs. Going from 2 to 3 tabs pushed the row
to 400px, which made the **whole page** horizontally scrollable at a 390px viewport. Fixed by
giving `.tabs-inner` `overflow-x:auto` (scrollbar hidden) plus tighter tab padding under 520px,
so the overflow is confined to the tab strip. If a 4th tab is ever added, re-check at 390px and
320px that `document.documentElement.scrollWidth <= window.innerWidth`.

### Verifying a push when the terminal is unreliable
Don't trust terminal silence. Check the remote ref directly — this needs no auth and no shell:
`https://api.github.com/repos/Kakee5/Honda/git/refs/heads/main`
Compare the returned sha against local `git rev-parse HEAD`.

### Reading command output on this machine
Kiro's PowerShell integration echoes commands back garbled and often shows empty output even
for commands that ran fine. Write output to a file and read that file instead of trusting the
terminal, and clean the scratch files up before committing (they are not gitignored).

## Current working machine
Windows only. Everything needed is already installed and configured:
- Python 3.12 at `python` · `curl` at `C:\Windows\System32\curl.exe`
- Git at `C:\Program Files\Git\cmd\git.exe` (installed via winget, **not** on PATH)
- git identity set locally in this repo: `Freed Spike <freedspike@users.noreply.github.com>`
- GCM credentials for `Kakee5/Honda` already cached → non-interactive push works
- `.env` with `AIRTABLE_TOKEN` present (gitignored)

<details>
<summary>Setting up from scratch on another machine (not currently needed)</summary>

1. `git clone https://github.com/Kakee5/Honda.git`
2. Create `.env` with `AIRTABLE_TOKEN=pat...` (from https://airtable.com/create/tokens,
   scopes `data.records:read` + `schema.bases:read`, the 3 bases added to Access).
3. Python 3 (stdlib + curl only). Node + `sharp` only needed for favicon regen.
4. Preview locally: `python -m http.server 8000` → `http://localhost:8000/`.
   (Opening index.html via file:// works too since data lives in data.js, not fetched.)
5. On Windows, expect one interactive GCM login to seed the credential cache before the
   non-interactive push works, then read the quirks section above.
</details>

## Deployment (GitHub Pages)
- Settings → Pages → Deploy from branch → `main` / root.
- Pages takes 1–3 min to rebuild after each push; hard-refresh (Ctrl+Shift+R) to bust favicon cache.
- Verify the live result by loading the page and reading `window.SITE_DATA`, not by eyeballing.

## Gotchas learned the hard way
- Windows Python defaults to `cp950` and cannot write the Chinese data → always `PYTHONUTF8=1`.
- Always push with `GIT_TERMINAL_PROMPT=0` + `GCM_INTERACTIVE=never`. Credentials are already
  cached; without these a GCM login prompt can hang the terminal indefinitely and make a
  successful push look like a failure. Verify against the GitHub refs API, not the terminal.
- Helper `.ps1` files must be ASCII-only (PowerShell 5.1 reads them as ANSI). Chinese paths and
  Chinese commit messages both get mangled — use inherited cwd and `git commit -F <utf-8 file>`.
- Adding a nav tab can make the whole page scroll horizontally on mobile. See quirk 6.
- GitHub Pages is case-sensitive (Linux). The club logo file is `.JPG` (uppercase) — keep references exact.
- All HTTP calls in the Python scripts go through `curl` via subprocess (originally a macOS SSL
  cert workaround). It works fine on Windows, so leave it as is.
- If edits were made on GitHub web, `git pull --rebase origin main` before pushing.
- Do NOT commit `node_modules`, `.env`, or unrelated large media. See `.gitignore`.

## Images are compressed automatically
Airtable serves full-resolution originals (a shopfront photo can be 3264x2448 / 10MB), which is
far more than a mobile-first site needs. `imgopt.py` shrinks the long edge to 1600px and
re-encodes; `download_assets.py` calls it on every newly downloaded image, so a normal sync needs
no extra step. `optimize_assets.py` is a one-off/idempotent pass over everything already in
`assets/` (re-running it reports ~0 saved). This took the 74 images under `assets/` from 56.4MB
to 5.7MB.

Only images are touched, so the two biggest files in `assets/` are now non-images:
the route-demo `.mp4` (8.44MB) and one Airtable `.pdf` attachment (1.96MB). Bear that in mind
before quoting a total: `assets/` is ~16MB, of which only ~5.7MB is images.

Two details that matter if you touch this:
- Photos become JPEG; only images that genuinely use transparency stay PNG. Files that are
  *already* JPEG keep their exact extension, because a few are referenced by hard-coded paths
  (the club logo `.JPG` in `MANUAL_LOC_IMAGES`, the `.jpeg` maintenance photo). Only
  PNG-without-transparency is renamed to `.jpg`, and those are all found by glob in
  `build_data.py`, so the rename is safe.
- `download_assets.py` matches its cache on `{rid}_{i}.*`, not the exact extension. Without
  that, every sync would see the `.png` missing and re-download the full-size original,
  silently undoing the compression.

## Current state (as of last sync)
- GB3/GP3: 32 DIY items · GB5/GB7: 25 DIY items · 推薦地點: 15 locations.
- Three tabs, in order: **保養參考資訊** (landing page) · DIY 教學 · 推薦地點.
- 保養參考資訊 is **static content** hard-coded in the `MAINT` const inside `index.html`
  (not from Airtable — editing it means editing code and pushing). Split by model:
  - GB3/GP3: 定期保養參考周期 (7 rows, sourced from Airtable 參考更換周期) · 水溫參考 (6 rows)
  - GB5/GB7: 定期保養參考周期 (7 rows) · 極力子油（GB7 Hybrid 專用）(5 rows + before/after photo)
  - Block format supports `type:'table'` and `type:'list'`, plus an optional
    `image:{src,alt,caption}` rendered as a clickable `.maint-fig` (opens the lightbox). The
    renderer removes the whole `<figure>` on `onerror`, so a missing file degrades silently
    instead of showing a broken image.
  - Hand-added maintenance photos live in `assets/maint/` — a directory `download_assets.py`
    never touches, so a re-sync can't wipe them. Use ASCII filenames with no spaces
    (GitHub Pages is case-sensitive and served over HTTP).
  - 車會會址 is pinned to the top of 推薦地點 by a stable sort in `build_data.py`
    (`CLUB_LOCATION_ID` / `CLUB_LOCATION_NAME`).
- Features: model switch, search, image lightbox, YouTube教學 buttons, per-location map buttons
  (Google/高德/Waze), route-demo video button (林叔), club-logo favicon, and **two independent
  sets of category filter pills**:
  - DIY 教學 — `#catChips` / `state.cat` / `renderCats()`, from `D.categories`.
  - 推薦地點 — `#locChips` / `state.locCat` / `renderLocCats()`, from `D.location_categories`.
  Both share the same `.chip` / `.chip.on` / `.n` CSS, and both combine with their search box
  (pill AND search, not OR). Copy `renderCats()` if a third one is ever needed.
- Header is the club **banner illustration** (`assets/brand/hero.jpg`), shown at its natural
  1.84 aspect with no crop, because the artwork already contains the「FREED SPIKE 交流區」
  wordmark. Consequences worth remembering:
  - The old `F` tile + text `<h1>` were removed to avoid duplicating that wordmark. The `<h1>`
    is still in the DOM as `.sr-only` for screen readers and SEO, and the `<img>` is decorative
    (`alt=""`) so the title is not announced twice.
  - Using the artwork as a CSS `background` behind the heading text was tried and abandoned:
    at a ~92px tall header, `cover` shows only ~17% of the image height, which destroys the
    composition and leaks the artwork's own「SPIKE」lettering behind the `<h1>`.
  - `min-width:560px` switches the banner from full-width to a fixed 240px height. Without that
    cap, a desktop banner is 521px tall and fills the entire first screen.

## Possible next steps / ideas (not yet done)
- Bundle the re-sync pipeline into a single `sync.ps1`.
- If 保養參考資訊 starts changing often, move it out of `index.html` into a 4th Airtable base so
  it can be synced instead of hand-edited.
- Generate a QR code linking to the live site.
- 類型 is a single select, so multi-service shops sit in one pill only. If that starts to annoy,
  switch the Airtable field to multiple select and change the filter to `l.category.includes(...)`
  (store an array instead of a string in `build_data.py`).
- Consider shrinking the route-demo mp4 (8.44MB): now that the images are compressed it is
  bigger than all 74 of them put together.
