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

## P2 — Robustness, UX honesty, best practices

- [x] 🟡 **Make dummy data opt‑in (`?demo=1`).** Done in v0.3.0.
- [x] 🟡 **SEC‑06 Stop reflecting upstream error text / tracebacks.** Done in v0.3.0.
- [x] 🟡 **Harden `wpasec_kquery`** — `.get()` + skip malformed. Done in v0.3.0.
- [ ] 🟡 **SEC‑08 Add security headers + CSP** (Flask‑Talisman). ⏱M
- [ ] 🟡 **SEC‑09 Pin Python deps (hashes) + add SRI to CDN assets** (or self‑host). ⏱M
- [ ] 🟡 **Rename `WireTapper.txt` → `requirements.txt`; pin versions; add WSGI server.** ⏱S
  (Deps now include `python-dotenv` + `Flask-Limiter`; still unpinned/unrenamed.)
- [ ] 🟡 **Improve `classify_device`** — token/word‑boundary match, ordered rules,
  reduce false positives (`OSCAR`→car, `FLAGSHIP`→LG). ⏱M
- [ ] 🟡 **Resolve dead frontend routes** — implement, hide, or label the ~12
  nav/JS endpoints (`/crmx`, `/api/username`, `/log-activity`, `/chatgpt`, …). ⏱M
- [ ] 🟡 **Remove or disclose client telemetry beacon** (`/log-activity` sends the
  username cookie + click text + dwell time). ⏱S

## P3 — Quality, product, compliance

- [ ] ⚪ **Add tests + CI** — contract tests for provider→device mapping; a
  `SessionStart` hook / GitHub Action running lint + tests. ⏱M
- [ ] ⚪ **Add linter/formatter** (ruff + black) config. ⏱S
- [ ] ⚪ **Privacy notice + lawful‑use interstitial** — state lawful basis, data
  retention, and an "authorized networks only" acknowledgement. ⏱M
- [ ] ⚪ **Third‑party ToS compliance** — document Shodan/Wigle/OpenCellID terms
  for re‑serving data. ⏱S
- [ ] ⚪ **Right‑size marketing copy** — align README claims (BLE/CCTV/vehicle/cell
  "real‑time correlation") with what actually ships; add a roadmap. ⏱S
- [ ] ⚪ **Unify branding** — WireTapper vs. HayOS/H9/Hayden. ⏱S
- [ ] ⚪ **Accessibility pass** — remove `<center>`, add labels/focus states, fix
  contrast, don't encode signal by color alone. ⏱M
- [ ] ⚪ **Fix template cruft** — 3 duplicate `<title>`, duplicate Leaflet
  includes, stray `}` in the media query near L1259, duplicate `addMessage`. ⏱S
- [ ] ⚪ **Consider better options** — swap the Werkzeug dev server for
  gunicorn+nginx; consider FastAPI if async fan‑out to providers is wanted; use
  `httpx.AsyncClient` to parallelize the 3 upstream calls per request; cache
  provider responses (Redis/TTL) to cut quota + latency. ⏱L

---

### Suggested execution path
Land **P0** as one hardening PR (small, high‑impact), then **P1** as a
"correctness + secrets" PR, then iterate P2/P3. Keep `docs/ARCHITECTURE.md`
updated as routes/contract change.
