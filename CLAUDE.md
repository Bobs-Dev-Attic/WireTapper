# CLAUDE.md — context for AI coding agents

Read this first. It exists so you don't have to re‑read the whole repo. For the
full system map see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); for the work
queue see [`TODO.md`](TODO.md); for risk detail see
[`docs/PROJECT_REVIEW.md`](docs/PROJECT_REVIEW.md) and
[`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md).

## What this is
A Flask OSINT web app: a Leaflet map UI that queries Wigle, OpenCellID/
UnwiredLabs, Shodan, and wpa‑sec, then plots "nearby" wireless devices.
Prototype quality, **not production‑ready** — has live security/privacy issues.

## Repo shape (small — ~4 code files)
- `app-env.py` — **preferred backend**; keys via `os.getenv`; has `wpasec_kquery`.
- `app.py` — legacy duplicate with **hardcoded key placeholders**; no wpa‑sec.
- `templates/wifi-search.html` — the entire frontend (inline CSS + JS).
- `.env` — tracked, placeholders only. Requirements are in `WireTapper.txt`.

## Non‑obvious facts that will save you a wrong turn
1. **`.env` is never loaded** — no `load_dotenv()` / `python-dotenv` anywhere.
   Only real shell exports reach `os.getenv`. Don't assume the file works.
2. **`app.py` and `app-env.py` are ~95% duplicated and have drifted.** Fix bugs
   in `app-env.py`; ideally consolidate rather than edit both.
3. **~12 frontend routes don't exist** (`/crmx`, `/api/username`, `/log-activity`,
   `/chatgpt`, `/logout`, …). They 404. Only `/map-w`, `/nearby`, `/searchzz`,
   `/api/geo/towers`, `/api/geo/celltower` are implemented.
4. **Dummy data fallback** fires whenever a provider returns nothing (e.g. missing
   keys) — so "it works" in the demo can mean "all upstreams failed."
5. **The device JSON shape is a contract** the template depends on (keys: `lat,
   lon, ssid, bssid, cell_id, ip, vendor, signal, accuracy, timestamp, type,
   leaked`). Don't rename keys without updating the template.

## Landmines — do not reintroduce, fix if you touch nearby code
- 🔴 `app.run(..., debug=True)` on `0.0.0.0` → RCE. Keep `debug=False`.
- 🔴 Template injects `ssid/vendor/bssid/ip/info` via `innerHTML`/`bindPopup`
  **unescaped** → XSS. Use `textContent`/`createElement`/escape.
- 🟠 No `timeout=` on any `requests` call. Always add one.
- 🟠 `if not lat or not lon` wrongly rejects `0.0`. Use `is None`.
- 🟠 Never hardcode real keys; never commit `.env`.

## House rules
- No secrets in code, commits, PRs, comments, or docs.
- Keep changes minimal and match existing style (this is a hobby‑scale repo).
- When you change routes or the device contract, update `docs/ARCHITECTURE.md`
  and `TODO.md` in the same change.
- There are **no tests and no CI yet** — validate manually and say so; if you add
  behavior, add a matching test where practical.
- Ethics: this is an OSINT tool. Don't add capabilities for unauthorized
  interception, credential harvesting, or evasion. Keep it lawful‑use‑only.

## Fast validation
```bash
python -m pyflakes app-env.py app.py         # if available
python -c "import ast,sys; [ast.parse(open(f).read()) for f in ('app.py','app-env.py')]"  # syntax
WIGLE_API_NAME=x WIGLE_API_TOKEN=y python app-env.py   # boots on :8080; visit /map-w
```
