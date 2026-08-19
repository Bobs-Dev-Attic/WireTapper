# AGENTS.md

Context for AI coding agents (Codex, etc.). This file mirrors
[`CLAUDE.md`](CLAUDE.md) — read that for the full briefing; the essentials are
repeated here so either tool works standalone.

## TL;DR
Flask OSINT map app (Wigle / OpenCellID / Shodan / wpa‑sec) → Leaflet UI.
Prototype, **not production‑ready**, with active security/privacy issues. Work
queue in [`TODO.md`](TODO.md); system map in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); risk detail in
[`docs/PROJECT_REVIEW.md`](docs/PROJECT_REVIEW.md) and
[`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md).

## Files (as of v0.3.0)
- `app.py` — **the single canonical backend** (env keys, `wpasec_kquery`, shared
  `HTTP` session, rate limiting, access gate). Edit here.
- `app-env.py` — thin shim: `from app import app`. No logic here.
- `templates/wifi-search.html` — entire frontend (inline CSS/JS).
- `WireTapper.txt` — deps (Flask, requests, python-dotenv, Flask-Limiter; still
  unpinned). `.env` — gitignored; auto-loaded; see `.env.example`.

## Gotchas (save yourself a wrong turn)
1. `app.py` is canonical; `app-env.py` only imports it (consolidated v0.3.0).
2. `.env` **is** loaded now (python-dotenv); dotenv + Flask-Limiter are optional
   imports (app degrades gracefully if absent).
3. ~12 frontend routes are **unimplemented** (404): `/crmx`, `/api/username`,
   `/log-activity`, `/chatgpt`, `/logout`, … Only `/map-w`, `/nearby`,
   `/searchzz`, `/api/geo/towers`, `/api/geo/celltower` exist.
4. Dummy data is **opt-in via `?demo=1`**; real empty results return `[]`.
5. The device JSON keys are a **contract** the template relies on.
6. Route outbound HTTP through the shared `HTTP` session (timeouts/retries).

## Must‑not‑break invariants (all currently satisfied — keep them)
- Keep `debug=False` default; never bind `0.0.0.0` publicly (Werkzeug RCE).
- Keep escaping `ssid/vendor/bssid/ip` before DOM insertion (`escapeHtml`).
- Keep `timeout=`/shared `HTTP` session on every outbound call.
- Keep `lat is None`/`lon is None` checks (0.0 is a valid coordinate).
- No secrets in code/commits/PRs/comments. `/chatgpt` reply must be sanitized
  before that endpoint ships (SEC‑10).

## Conventions
- Minimal, style‑matching diffs. Update `docs/ARCHITECTURE.md` + `TODO.md` when
  routes or the device contract change. No tests/CI yet — validate manually and
  state what you did. Lawful‑use‑only tool: don't add interception/harvesting/
  evasion features.
