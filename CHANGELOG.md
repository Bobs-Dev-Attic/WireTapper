# Changelog

All notable changes to WireTapper are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project uses [Semantic Versioning](https://semver.org/).

## [0.4.0] — 2026-08-19

Best-practices + UX-honesty pass (**P2** from [`TODO.md`](TODO.md)).

### Security
- **SEC-08** — Added security headers on every response (`X-Content-Type-Options`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy`,
  `Cross-Origin-Opener-Policy`) plus a **Content-Security-Policy** scoped to the
  CDN/tile/font hosts the template actually uses. Toggle via `SECURITY_HEADERS`
  / `CSP_ENABLED`. (CSP still allows `'unsafe-inline'` because all page CSS/JS is
  inline; that tightens once assets are self-hosted/nonce'd.)
- **SEC-09 (partial)** — Pinned all Python deps in `requirements.txt` (+ added
  `gunicorn`). Added `scripts/gen_sri.sh` to generate Subresource Integrity
  hashes for the CDN `<script>`/`<link>` tags — run it where network is
  available and paste the `integrity=`/`crossorigin` attributes in. (Hashes
  can't be computed in this sandbox; wrong values would break asset loading.)

### Changed / UX
- **Removed the client telemetry beacon** that POSTed the `username` cookie,
  click text, and dwell time to a non-existent `/log-activity` on every
  interaction (privacy + dead endpoint).
- **Stopped the failing on-load `/api/username` fetch** and the `/logout` link
  (neither endpoint exists); header now shows a static "Guest".
- **Chat no longer POSTs to the non-existent `/chatgpt`** — it shows an honest
  "not available in this build" notice, removing the last live `innerHTML`
  server-reply sink (SEC-10 pre-empted for this build).
- **Dead sidebar modules are marked "SOON"** (dimmed, `cursor:not-allowed`) and
  show a "Module coming soon" toast instead of silent dead clicks.
- **Improved `classify_device`** — token/word-boundary matching with an ordered
  rule set. `OSCAR`/`SCART` no longer classify as "car", `FLAGSHIP` no longer as
  "tv", `DASH CAM` resolves to dashcam (not camera).

### Added
- `requirements.txt` (renamed from `WireTapper.txt`, now pinned) and
  `requirements-dev.txt`.
- **First test suite** — `tests/test_app.py` (pytest, 20 tests) covering
  classification, coordinate handling, demo opt-in, the access gate, security
  headers, and rate limiting. Outbound HTTP is stubbed (no keys/network needed).
  (Partially addresses the P3 "tests/CI" gap; CI wiring still TODO.)

### Notes / not yet addressed (see TODO.md)
- SRI `integrity` attributes still need to be generated + pasted (SEC-09).
- CI, privacy notice, accessibility pass, and marketing/branding remain **P3**.

## [0.3.0] — 2026-08-19

Robustness + hardening pass (**P1** from [`TODO.md`](TODO.md)). Consolidates the
two backends and adds the network/auth safety that was missing.

### Changed
- **Consolidated backends.** `app.py` is now the single canonical module (env
  config + wpa-sec enrichment + all fixes). `app-env.py` is a thin shim that
  does `from app import app`, so `python app-env.py` and the WSGI target
  `app-env:app` still work. Ends the app.py/app-env.py feature drift.
- **Demo data is opt-in.** Fabricated "dummy" devices now require `?demo=1`;
  previously they were injected on any empty result, masking missing keys and
  upstream failures. Real empty results now return `{"devices": []}` honestly.

### Security / robustness
- **P1/SEC (dotenv)** — `.env` files are now actually loaded (`python-dotenv` +
  `load_dotenv()`); the documented Method-2 workflow previously did nothing.
- **SEC-07** — All outbound calls go through one shared `requests.Session` with
  connect/read **timeouts** `(3.05, 10)`, connection pooling, and bounded
  retry/back-off. Removes the hung-worker DoS surface.
- **SEC-03** — Added per-IP **rate limiting** (Flask-Limiter, 120/hour on data
  endpoints), an optional **access-token gate** (`WIRETAPPER_ACCESS_TOKEN` via
  `X-API-Key`/`access_token`, open by default for localhost), and **bounded the
  user query length** (`MAX_QUERY_LEN`, default 256) before it reaches Shodan/
  Wigle. Shodan `network` search is also capped to 10 results.
- **SEC-05** — OpenCellID `getInArea` now uses **HTTPS** (was cleartext `http://`
  with the key in the query string).
- **SEC-06** — Endpoints no longer reflect upstream response bodies/tracebacks to
  the client; details are logged server-side and generic errors returned.

### Fixed
- **Falsy-coordinate bug** — `lat`/`lon` of `0.0` (a valid location) are no longer
  rejected as "missing"; checks use `is None`.
- `wpasec_kquery` uses `.get()` and skips malformed devices instead of raising.

### Added
- `python-dotenv` and `Flask-Limiter` to the requirements (both imported
  defensively — the app degrades gracefully if either is absent).
- Expanded `.env.example` documenting every configuration knob.

### Notes / not yet addressed (see TODO.md)
- The static frontend does not yet send `X-API-Key`, so enabling the token gate
  currently requires a caller that adds the header (follow-up: real auth + login).
- Dead frontend routes, security headers/CSP (SEC-08), dependency pinning + SRI
  (SEC-09), and tests/CI remain open (**P2/P3**).

## [0.2.0] — 2026-08-19

Security hardening pass (**P0** from [`TODO.md`](TODO.md)). No feature changes;
focus is closing the highest-risk issues from the audit. Behavior of the running
app changes in two visible ways: it now binds `127.0.0.1` (not all interfaces)
with the debugger **off** by default, and provider/user text is escaped in the UI.

### Security
- **SEC-01** — Flask no longer defaults to `debug=True` on `0.0.0.0`
  (Werkzeug interactive-debugger RCE + network exposure). New defaults:
  `FLASK_HOST=127.0.0.1`, `FLASK_PORT=8080`, `FLASK_DEBUG=0`, all env-overridable
  for local dev only. Applied to `app.py` and `app-env.py`.
- **SEC-02** — Fixed DOM-based XSS. Added `escapeHtml()` and escaped all
  provider/user-controlled fields (`ssid`, `vendor`, `bssid`, `ip`, `type`,
  `signal`, `accuracy`, `timestamp`) before injecting into map popups and the
  results sidebar in `templates/wifi-search.html`. Flagged the unimplemented
  `/chatgpt` reply sink (`div.innerHTML = text`) inline as must-sanitize-before-ship
  (tracked as SEC-10).
- **SEC-04** — Removed hardcoded API-key placeholders from `app.py`; it now reads
  all keys from the environment (matching `app-env.py`). Untracked `.env` from
  git and added `.gitignore` + `.env.example` (added in 0.1.1). **Action still
  required:** rotate any key ever committed to source or `.env`.

### Fixed
- Broken license link: renamed `LICENSE-NONCOMMERCIAL.md` → `LICENSE` so the
  README reference (and GitHub's license detection) resolves.

### Docs
- Rewrote README configuration section: both entrypoints use env vars, documented
  the new host/port/debug env toggles and the "`.env` not auto-loaded yet" caveat.

### Notes / not yet addressed (see TODO.md)
- `.env`-file auto-loading still requires `python-dotenv` (**P1**).
- No timeouts on outbound `requests` (**P1 / SEC-07**), no auth/rate-limit
  (**P1 / SEC-03**), `app.py`/`app-env.py` still duplicated (**P1**).

## [0.1.1] — 2026-08-19

### Added
- Project documentation set: `docs/PROJECT_REVIEW.md`, `docs/SECURITY_AUDIT.md`,
  `docs/ARCHITECTURE.md`, prioritized `TODO.md`, and AI-agent context files
  `CLAUDE.md` / `AGENTS.md`.
- `.gitignore` and `.env.example` to prevent future secret leakage.

## [0.1.0] — baseline

- Pre-review state of the project (commit `7e43d6a`): Flask OSINT map app with
  Wigle / OpenCellID / Shodan / wpa-sec integrations and the Leaflet dashboard.

[0.2.0]: https://github.com/Bobs-Dev-Attic/WireTapper/tree/claude/project-review-audit-257vhu
[0.1.1]: https://github.com/Bobs-Dev-Attic/WireTapper/tree/claude/project-review-audit-257vhu
[0.1.0]: https://github.com/Bobs-Dev-Attic/WireTapper/tree/main
