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

## Files
- `app-env.py` — preferred backend (env keys; has `wpasec_kquery`).
- `app.py` — legacy duplicate (hardcoded placeholder keys; no wpa‑sec).
- `templates/wifi-search.html` — entire frontend (inline CSS/JS).
- `WireTapper.txt` — deps (unpinned: Flask, requests). `.env` — tracked placeholders.

## Gotchas (save yourself a wrong turn)
1. `.env` is **not** loaded — no `load_dotenv()` exists; only shell exports work.
2. `app.py` and `app-env.py` have **drifted**; prefer editing/consolidating into
   `app-env.py`.
3. ~12 frontend routes are **unimplemented** (404): `/crmx`, `/api/username`,
   `/log-activity`, `/chatgpt`, `/logout`, … Only `/map-w`, `/nearby`,
   `/searchzz`, `/api/geo/towers`, `/api/geo/celltower` exist.
4. Empty upstream results silently fall back to **fabricated dummy data**.
5. The device JSON keys are a **contract** the template relies on.

## Must‑not‑break (fix if you touch nearby code)
- Keep `debug=False`; never bind `0.0.0.0` publicly (Werkzeug RCE).
- Escape `ssid/vendor/bssid/ip/info` before DOM insertion (current XSS).
- Add `timeout=` to every `requests` call.
- Use `lat is None` checks, not `not lat` (0.0 is valid).
- No secrets in code/commits/PRs/comments.

## Conventions
- Minimal, style‑matching diffs. Update `docs/ARCHITECTURE.md` + `TODO.md` when
  routes or the device contract change. No tests/CI yet — validate manually and
  state what you did. Lawful‑use‑only tool: don't add interception/harvesting/
  evasion features.
