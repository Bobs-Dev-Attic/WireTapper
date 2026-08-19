# WireTapper — Prioritized TODO

Ordered by risk × leverage. Each item links to detail in
[`docs/PROJECT_REVIEW.md`](docs/PROJECT_REVIEW.md) and
[`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md). IDs (SEC‑nn) are stable.

Legend: 🔴 critical · 🟠 high · 🟡 medium · ⚪ low · effort ⏱ S/M/L

---

## P0 — Do before this is reachable by anyone else

- [ ] 🔴 **SEC‑01 Disable the dev debugger / stop binding all interfaces.** ⏱S
  Set `debug=False`, bind `127.0.0.1`, gate via env; serve with gunicorn in prod.
- [ ] 🔴 **SEC‑04 Fix secrets hygiene.** ⏱S
  Add `.gitignore` (`.env`, `__pycache__/`, `*.pyc`, `.venv/`); `git rm --cached
  .env`; add `.env.example`; remove hardcoded keys from `app.py`; **rotate every
  key** ever pasted into source or a real `.env`.
- [ ] 🔴 **SEC‑02 Kill DOM XSS.** ⏱M
  Replace `innerHTML`/template‑literal `bindPopup` with `textContent` +
  `createElement` + `escapeHtml()`; sanitize chat replies (DOMPurify). Escape
  `ssid`, `vendor`, `bssid`, `ip`, `info`.
- [ ] 🔴 **Fix broken LICENSE reference.** ⏱S
  Rename `LICENSE-NONCOMMERCIAL.md` → `LICENSE` (or fix the README link) so the
  CC‑BY‑NC‑4.0 terms actually apply.

## P1 — Correctness & core hardening

- [ ] 🟠 **Make secret loading actually work.** ⏱S
  Add `python-dotenv` to requirements and `load_dotenv()` in `app-env.py`, OR fix
  the README (Method 2 currently silently fails — no `load_dotenv` exists).
- [ ] 🟠 **SEC‑07 Add timeouts + shared session.** ⏱S
  Module‑level `requests.Session`, `timeout=(3.05, 10)` on every call, back‑off.
- [ ] 🟠 **SEC‑03 Auth + rate limit search endpoints.** ⏱M
  Flask‑Limiter per‑IP; require auth for `/searchzz`/`/nearby`; validate/bound the
  Shodan `query` so anonymous users can't spend the premium key.
- [ ] 🟠 **Fix falsy‑coordinate bug.** ⏱S
  Replace `if not lat or not lon` with `if lat is None or lon is None` everywhere.
- [ ] 🟠 **Consolidate `app.py` + `app-env.py` into one module.** ⏱M
  Config via env; delete the duplicate to stop feature drift (wpa‑sec lives in
  only one today).
- [ ] 🟠 **SEC‑05 HTTPS for OpenCellID; keys out of query strings.** ⏱S

## P2 — Robustness, UX honesty, best practices

- [ ] 🟡 **Make dummy data opt‑in (`?demo=1`).** ⏱S Stop masking real failures.
- [ ] 🟡 **SEC‑06 Stop reflecting upstream error text / tracebacks.** ⏱S
- [ ] 🟡 **SEC‑08 Add security headers + CSP** (Flask‑Talisman). ⏱M
- [ ] 🟡 **SEC‑09 Pin Python deps (hashes) + add SRI to CDN assets** (or self‑host). ⏱M
- [ ] 🟡 **Rename `WireTapper.txt` → `requirements.txt`; pin versions; add WSGI server.** ⏱S
- [ ] 🟡 **Harden `wpasec_kquery`** — use `.get()` not `d['…']`; skip malformed
  devices without aborting the loop. ⏱S
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
