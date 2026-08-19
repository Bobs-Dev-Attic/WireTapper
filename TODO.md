# WireTapper — Prioritized TODO

Ordered by risk × leverage. Each item links to detail in
[`docs/PROJECT_REVIEW.md`](docs/PROJECT_REVIEW.md) and
[`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md). IDs (SEC‑nn) are stable.
Release notes for completed work live in [`CHANGELOG.md`](CHANGELOG.md).

Legend: 🔴 critical · 🟠 high · 🟡 medium · ⚪ low · effort ⏱ S/M/L

---

## P0 — Do before this is reachable by anyone else ✅ DONE in v0.2.0

- [x] 🔴 **SEC‑01 Disable the dev debugger / stop binding all interfaces.** ⏱S
  Done (v0.2.0): defaults to `debug=False`, host `127.0.0.1`, all env‑overridable
  (`FLASK_DEBUG`/`FLASK_HOST`/`FLASK_PORT`) in `app.py` + `app-env.py`.
  ↪ Follow‑up (P2): serve via gunicorn/uvicorn in production.
- [x] 🔴 **SEC‑04 Fix secrets hygiene.** ⏱S
  Done: `.gitignore` + `.env.example` added (v0.1.1); `.env` untracked and
  hardcoded keys removed from `app.py` (now env‑based) (v0.2.0).
  ⚠️ **Still required by maintainer:** **rotate any key** ever committed to source
  or a real `.env` — code cannot do this for you.
- [x] 🔴 **SEC‑02 Kill DOM XSS.** ⏱M
  Done (v0.2.0): added `escapeHtml()`; escaped `ssid`/`vendor`/`bssid`/`ip`/
  `type`/`signal`/`accuracy`/`timestamp` in popups + sidebar.
  ↪ Follow‑up (SEC‑10): sanitize the `/chatgpt` reply sink (DOMPurify) before that
  endpoint ships — flagged inline in the template.
- [x] 🔴 **Fix broken LICENSE reference.** ⏱S
  Done (v0.2.0): `LICENSE-NONCOMMERCIAL.md` → `LICENSE`; README link resolves.
  ↪ Follow‑up (P3): README says "CC‑BY‑NC‑4.0" but the file is a custom NCOSL —
  reconcile the license text vs. the stated license.

## P1 — Correctness & core hardening ✅ DONE in v0.3.0

- [x] 🟠 **Make secret loading actually work.** ⏱S
  Done (v0.3.0): `python-dotenv` added; `app.py` calls `load_dotenv()`.
- [x] 🟠 **SEC‑07 Add timeouts + shared session.** ⏱S
  Done (v0.3.0): one shared `requests.Session` with `timeout=(3.05, 10)`,
  pooling, and bounded retry/back‑off; used by every outbound call.
- [x] 🟠 **SEC‑03 Auth + rate limit search endpoints.** ⏱M
  Done (v0.3.0): Flask‑Limiter (120/hour on data endpoints), optional
  `WIRETAPPER_ACCESS_TOKEN` gate (`X-API-Key`), and `MAX_QUERY_LEN` bounding.
  ↪ Follow‑up: wire `X-API-Key` into the frontend / add real login‑based auth.
- [x] 🟠 **Fix falsy‑coordinate bug.** ⏱S
  Done (v0.3.0): all checks use `lat is None or lon is None`.
- [x] 🟠 **Consolidate `app.py` + `app-env.py` into one module.** ⏱M
  Done (v0.3.0): `app.py` is canonical; `app-env.py` is a shim importing it.
- [x] 🟠 **SEC‑05 HTTPS for OpenCellID; keys out of query strings.** ⏱S
  Done (v0.3.0): `getInArea` now HTTPS. (Provider APIs still require the key as a
  query param by design; HTTPS protects it in transit.)
- [x] 🟡 **(pulled forward) SEC‑06 Stop reflecting upstream error text.** ⏱S
  Done (v0.3.0): upstream bodies/tracebacks no longer returned to clients.
- [x] 🟡 **(pulled forward) Demo data opt‑in (`?demo=1`).** ⏱S Done (v0.3.0).
- [x] 🟡 **(pulled forward) Harden `wpasec_kquery`.** ⏱S Done (v0.3.0).

## P2 — Robustness, UX honesty, best practices ✅ DONE in v0.4.0

- [x] 🟡 **Make dummy data opt‑in (`?demo=1`).** Done in v0.3.0.
- [x] 🟡 **SEC‑06 Stop reflecting upstream error text / tracebacks.** Done in v0.3.0.
- [x] 🟡 **Harden `wpasec_kquery`** — `.get()` + skip malformed. Done in v0.3.0.
- [x] 🟡 **SEC‑08 Add security headers + CSP.** Done (v0.4.0): manual
  `after_request` headers + scoped CSP (no Talisman dep). Toggle via
  `SECURITY_HEADERS`/`CSP_ENABLED`.
- [~] 🟡 **SEC‑09 Pin Python deps + add SRI to CDN assets.** Python deps pinned
  (v0.4.0); `scripts/gen_sri.sh` added. ↪ **Remaining:** run the script (needs
  network) and paste the `integrity=`/`crossorigin` attrs into the template.
- [x] 🟡 **Rename `WireTapper.txt` → `requirements.txt`; pin; add WSGI server.**
  Done (v0.4.0): pinned + `gunicorn` added; README shows the gunicorn command.
- [x] 🟡 **Improve `classify_device`** — token/word‑boundary match, ordered
  rules. Done (v0.4.0); covered by tests.
- [x] 🟡 **Resolve dead frontend routes** — Done (v0.4.0): sidebar modules marked
  "SOON" + toast; failing `/api/username`, `/log-activity`, `/chatgpt` calls
  removed. ↪ Implementing the actual modules stays future work.
- [x] 🟡 **Remove client telemetry beacon.** Done (v0.4.0): removed entirely.

## P3 — Quality, product, compliance ✅ DONE in v0.5.0

- [x] ⚪ **Add tests + CI** — pytest suite (now 22 tests, incl. provider→device
  mapping + `wpasec_kquery` contract) + GitHub Actions CI (ruff + pytest on
  3.9/3.12). Done (v0.4.0 tests, v0.5.0 CI + contract tests).
- [x] ⚪ **Add linter** — ruff config in `pyproject.toml`; codebase ruff-clean.
  Done (v0.5.0). (`ruff format` available but not gated yet.)
- [x] ⚪ **Privacy notice + lawful‑use interstitial** — `PRIVACY.md` + one‑time
  in‑app acknowledgement. Done (v0.5.0).
- [x] ⚪ **Third‑party ToS compliance** — `docs/LEGAL.md`. Done (v0.5.0).
- [x] ⚪ **Right‑size marketing copy** — README reframed as OSINT aggregator +
  roadmap link. Done (v0.5.0).
- [x] ⚪ **Unify branding** — `<title>`/H1 unified to "WireTapper" (author credit
  kept in subtitle). Done (v0.5.0).
- [x] ⚪ **Accessibility pass** — `<center>` removed, focus states, ARIA labels,
  keyboard‑operable cards, non‑color signal value. Done (v0.5.0).
- [x] ⚪ **Fix template cruft** — duplicate titles/Leaflet/Font‑Awesome/addMessage
  removed; dead highlight.js dropped; the **orphan `}`** (an unbalanced CSS brace
  that silently dropped following rules) removed. Done (v0.5.0).
- [~] ⚪ **Consider better options** — documented in `docs/ROADMAP.md` (async
  fan‑out, caching, FastAPI/typed contract, gunicorn+nginx). ↪ Implementation is
  future work by design.

## Deploy
- [x] **Vercel serverless** wired: `api/index.py` + `vercel.json` +
  `docs/DEPLOY.md`. ↪ Before public: set Redis `RATE_LIMIT_STORAGE` and lower
  `HTTP_READ_TIMEOUT` (DEPLOY.md §3/§5).

## Carry-over follow-ups (not blocking; owner action)
- ⚠️ **Rotate any API key** ever committed to source or a real `.env` (from P0).
- **Run `scripts/gen_sri.sh`** (needs network) and paste `integrity=` attrs into
  the template — finishes SEC‑09.
- **Frontend auth** so the `WIRETAPPER_ACCESS_TOKEN` gate is usable end‑to‑end
  (the static UI doesn't send `X-API-Key` yet). Matters most for a public deploy.
- **On Vercel:** set `RATE_LIMIT_STORAGE` to a Redis URL (memory:// is per-
  instance and ineffective on serverless) and tune `HTTP_READ_TIMEOUT`.
- **Implement or remove** the "SOON" sidebar modules.

---

### Status
P0–P3 complete (v0.2.0 → v0.5.0). Remaining work is the carry-over list above
plus anything in [`docs/ROADMAP.md`](docs/ROADMAP.md). Keep
`docs/ARCHITECTURE.md`, `CHANGELOG.md`, and this file updated as things change.
