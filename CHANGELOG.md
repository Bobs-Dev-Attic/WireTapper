# Changelog

All notable changes to WireTapper are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project uses [Semantic Versioning](https://semver.org/).

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
