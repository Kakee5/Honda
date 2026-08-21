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
- Locations table: `Name`, `電話`, `地址`, `Google Map`, `高德地圖`, `WAZE`, `Remark` (images/video).

### Categories (assigned in build_data.py CATEGORY_MAP)
lighting 燈光系統 / engine 引擎‧油水‧保養 / electronics 電子‧音響 /
body 車身‧外觀 / interior 內飾‧門板 / tools 工具‧其他.
Unmapped parts fall back to `tools`.

## File structure (in repo root = Honda/)
- `index.html` — the whole site (embedded CSS + JS). Loads `data.js`.
- `data.js` — `window.SITE_DATA = {...}` generated from `site_data.json`.
- `site_data.json` — clean categorized data (build output).
- `raw/*.json` — raw Airtable dumps (backup).
- `assets/{gb3_gp3,gb5_gb7,locations}/` — downloaded images/videos (so the site
  never depends on Airtable's expiring signed URLs).
- `fetch_airtable.py` — pulls records from the 3 bases into `raw/`.
- `download_assets.py` — downloads attachments locally into `assets/`.
- `build_data.py` — builds `site_data.json` with categories + local image paths.
  Contains `MANUAL_LOC_IMAGES` override (club logo used as 車會會址 photo).
- `make_favicon.js` — generates favicons from the club logo (uses `sharp`).
- `.env` — Airtable token (gitignored, must be recreated on each machine).

## Re-sync pipeline (run after any Airtable change)
```bash
python3 fetch_airtable.py      # 1. pull latest from Airtable
python3 download_assets.py     # 2. download new images/videos
python3 build_data.py          # 3. rebuild categorized site_data.json
# 4. regenerate data.js:
python3 -c "import pathlib; d=open('site_data.json').read(); pathlib.Path('data.js').write_text('window.SITE_DATA = '+d+';\n', encoding='utf-8')"
# 5. commit & push
git add -A && git commit -m "sync Airtable" && git push origin main
```

## Running the pipeline on Windows / PowerShell
The commands above assume macOS. On the Windows machine three things differ. All three have
bitten us before — read this before running a sync there.

### 1. Force UTF-8 or the scripts crash
Windows Python defaults to the `cp950` codec, which cannot encode some of the Chinese
characters in the Airtable data. `fetch_airtable.py` dies with
`UnicodeEncodeError: 'cp950' codec can't encode character ...`.
Set this once per shell session before running anything:
```powershell
$env:PYTHONUTF8 = "1"
```
Also pass `encoding='utf-8'` explicitly when reading `site_data.json` in the data.js step.
Full pipeline in PowerShell:
```powershell
$env:PYTHONUTF8 = "1"
python fetch_airtable.py
python download_assets.py
python build_data.py
python -c "import pathlib; d=open('site_data.json',encoding='utf-8').read(); pathlib.Path('data.js').write_text('window.SITE_DATA = '+d+';\n', encoding='utf-8')"
```
(`python`, not `python3`, on Windows. `curl` is built in at `C:\Windows\System32\curl.exe`,
so the subprocess calls work unchanged.)

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

### 3. Git Credential Manager hangs the agent terminal
Running `git push` from Kiro's shell on Windows triggers the GCM browser/GUI login, and that
process **never returns** — the push may actually complete, but the terminal stays blocked and
every following command silently returns nothing for several minutes. This has already caused
one false "push failed" diagnosis.

Two ways to avoid it:
- **Preferred:** run the push yourself in a normal terminal, where the GCM prompt is interactive.
- **Non-interactive:** feed a short-lived PAT through `GIT_ASKPASS` and disable GCM for that
  one invocation, so it fails fast instead of hanging:
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
  Delete the askpass file and revoke the token afterwards. Keeps the token out of git config,
  the remote URL, and the repo.

### Verifying a push when the terminal is unreliable
Don't trust terminal silence. Check the remote ref directly — this needs no auth and no shell:
`https://api.github.com/repos/Kakee5/Honda/git/refs/heads/main`
Compare the returned sha against local `git rev-parse HEAD`.

### Reading command output on this machine
Kiro's PowerShell integration echoes commands back garbled and often shows empty output even
for commands that ran fine. Write output to a file and read that file instead of trusting the
terminal, and clean the scratch files up before committing (they are not gitignored).

## Environment setup on a new machine
1. `git clone https://github.com/Kakee5/Honda.git`
2. Create `.env` with: `AIRTABLE_TOKEN=pat...` (get from https://airtable.com/create/tokens,
   scopes `data.records:read` + `schema.bases:read`, with the 3 bases added to Access).
3. Python 3 (uses only stdlib + curl). Node + `sharp` only needed for favicon regen.
4. Preview locally: `python3 -m http.server 8000` then open `http://localhost:8000/`.
   (Opening index.html via file:// works too since data is in data.js, not fetched.)
5. On Windows, also read "Running the pipeline on Windows / PowerShell" above — UTF-8,
   git-not-on-PATH and the credential-manager hang all need handling there.

## Deployment (GitHub Pages)
- Settings → Pages → Deploy from branch → `main` / root.
- Pages takes 1–3 min to rebuild after each push; hard-refresh (Cmd+Shift+R) to bust favicon cache.

## Gotchas learned the hard way
- macOS system Python has an SSL cert issue → all HTTP calls use `curl` (via subprocess), not urllib.
- Windows Python defaults to `cp950` and cannot write the Chinese data → always `PYTHONUTF8=1`.
- On Windows, `git push` from the agent terminal hangs on Git Credential Manager; verify the
  push against the GitHub refs API rather than believing the terminal. See the Windows section.
- GitHub Pages is case-sensitive (Linux). The club logo file is `.JPG` (uppercase) — keep references exact.
- Pushing needs a GitHub PAT (Contents: Read & write on `Kakee5/Honda`). Never store it in
  git config/remote URL — push with an inline credential helper and a short-lived token, then revoke.
- If edits were made on GitHub web, `git pull --rebase origin main` before pushing.
- Do NOT commit `node_modules`, `.env`, or unrelated large media. See `.gitignore`.

## Current state (as of last sync)
- GB3/GP3: 32 DIY items · GB5/GB7: 25 DIY items · 推薦地點: 11 locations.
- Features: model switch, category filters, search, image lightbox, YouTube教學 buttons,
  per-location map buttons (Google/高德/Waze), route-demo video button (林叔), club-logo favicon.

## Possible next steps / ideas (not yet done)
- Bundle the re-sync pipeline into a single `sync.sh`.
- Swap the header "F" placeholder box for the real club logo image.
- Generate a QR code linking to the live site.
- Optional: reduce image sizes (assets ~50MB) if repo size becomes a concern.
