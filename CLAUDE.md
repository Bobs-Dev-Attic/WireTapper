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

## Repo shape (small — ~3 code files) — current as of v0.5.0
- `app.py` — **the single canonical backend**; env config + `wpasec_kquery` +
  shared `HTTP` session + rate limiting + access gate + security headers/CSP.
- `app-env.py` — thin shim (`from app import app`); kept for backward compat.
  Don't put logic here.
- `templates/wifi-search.html` — the entire frontend (inline CSS + JS); includes
  a one‑time lawful‑use interstitial.
- `.env` — gitignored (see `.env.example`); auto‑loaded by `app.py`. Deps pinned
  in `requirements.txt`; tests in `tests/` (`pytest`, 22 tests), dev deps in
  `requirements-dev.txt`; `ruff` config + CI (`.github/workflows/ci.yml`).
- Setup/config: `docs/INSTALL.md`, `docs/CONFIGURATION.md` (full env-var
  reference), `.env.example`. Compliance/roadmap: `PRIVACY.md`, `docs/LEGAL.md`,
  `docs/ROADMAP.md`.
- Deploy: `api/index.py` (Vercel WSGI shim → `from app import app`) + `vercel.json`
  + `docs/DEPLOY.md`. Another thin shim — no logic here either.

## Non‑obvious facts that will save you a wrong turn
1. **`app.py` is canonical; `app-env.py` just imports it.** Consolidated in
   v0.3.0 — do not re‑fork logic into the shim.
2. **`.env` IS loaded now** (python-dotenv). dotenv + Flask-Limiter are imported
   defensively, so the app still runs if they're missing (limiter → no‑op).
3. **~12 frontend routes don't exist** (`/crmx`, `/logout`, `/chatgpt`, …). Only
   `/map-w`, `/nearby`, `/searchzz`, `/api/geo/towers`, `/api/geo/celltower` are
   implemented. As of v0.4.0 the dead sidebar links are labeled "SOON" and the
   failing on‑load calls (`/api/username`, `/log-activity`, `/chatgpt`) were
   removed — don't re‑add calls to unimplemented endpoints.
4. **Dummy data is opt‑in via `?demo=1`** (v0.3.0). Real empty results now return
   `{"devices": []}` — no more silent masking.
5. **The device JSON shape is a contract** the template depends on (keys: `lat,
   lon, ssid, bssid, cell_id, ip, vendor, signal, accuracy, timestamp, type,
   leaked`). Don't rename keys without updating the template.
6. **Data endpoints are rate‑limited + optionally token‑gated.** Route outbound
   calls through the shared `HTTP` session so they inherit timeouts/retries.

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
ruff check .                                 # lint (config in pyproject.toml)
pytest -q                                    # 22 tests, HTTP stubbed (no keys needed)
python app.py                                # boots on 127.0.0.1:8080; visit /map-w
```
