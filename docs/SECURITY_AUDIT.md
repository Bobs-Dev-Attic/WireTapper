# WireTapper — Security Audit (White‑Hat / Pentester View)

**Scope:** static review of `app.py`, `app-env.py`, `templates/wifi-search.html`,
repo hygiene. **No live testing performed.** Severities use CVSS‑style intuition,
not formal scoring. Cross‑reference IDs are used in [`/TODO.md`](../TODO.md).

> Ethical note: findings below are for hardening WireTapper itself. Nothing here
> is an exploit against third parties.

---

## Severity legend
🔴 Critical · 🟠 High · 🟡 Medium · ⚪ Low/Info

## Status (see [`CHANGELOG.md`](../CHANGELOG.md))
- ✅ **Fixed in v0.2.0:** SEC‑01, SEC‑02, SEC‑04 (code portion; **key rotation
  still owed by the maintainer**).
- ⬜ **Open:** SEC‑03, SEC‑05, SEC‑06, SEC‑07, SEC‑08, SEC‑09, SEC‑10.

---

### SEC‑01 🔴 Werkzeug debugger + `0.0.0.0` (RCE)
**Where:** `app.py:497`, `app-env.py:559` — `app.run(host="0.0.0.0", port=8080, debug=True)`
**Impact:** With `debug=True`, any unhandled exception exposes the Werkzeug
interactive console; if the PIN is bypassed/known it is **remote code execution**.
`0.0.0.0` publishes it to every interface on the network.
**Fix:** Default `debug=False`, bind `127.0.0.1`, gate both behind env vars, and
serve via gunicorn/uvicorn in production. Never ship the dev server publicly.

### SEC‑02 🔴 DOM‑based XSS via device fields
**Where:** `templates/wifi-search.html` — `updateMap()` (`bindPopup` template
literal, ~L1693), `renderSidebar()` (`item.innerHTML`, ~L1762), and the chat
`addMessage` override (`div.innerHTML = text`, ~L2149).
**Impact:** `ssid`, `vendor`, `bssid`, `ip`, `info` are inserted into the DOM
**unescaped**. SSIDs are attacker‑authored free text (32 bytes, arbitrary
content). A network named `"><img src=x onerror=alert(document.cookie)>` — or an
`ssid` search crafted to return one — runs script in the operator's session.
Because the operator is the privileged user, this can pivot to any same‑origin
action the app later adds (admin panel, logout CSRF, key display).
**Fix:** Never build markup from data with `innerHTML`. Use `textContent`,
`document.createElement`, and a small `escapeHtml()` for any interpolation. For
the chat, render markdown/code through a sanitizer (DOMPurify) — do not trust the
server reply as HTML.

### SEC‑03 🟠 Unauthenticated third‑party API spend (Shodan/Wigle)
**Where:** `/searchzz?type=network` (`app.py:460`, `app-env.py:522`), `/nearby`
Shodan block, all Wigle blocks.
**Impact:** No auth, no rate limit. A visitor supplies an arbitrary Shodan
`query` executed with the operator's **premium** key, or hammers Wigle until the
daily quota is drained. This is cost amplification + data exfiltration through
the operator's paid identity.
**Fix:** Require authentication for search endpoints; add per‑IP rate limiting
(Flask‑Limiter); constrain/validate `query`; consider server‑side allow‑lists for
Shodan filters. Never expose raw provider queries to anonymous users.

### SEC‑04 🟠 Secrets management (tracked `.env`, no `.gitignore`, keys in source)
**Where:** repo root — `.env` is git‑tracked; no `.gitignore`; `README` Method 1
+ `app.py:10‑13` bake keys into source.
**Impact:** High likelihood of committing real credentials. Even the placeholder
`.env` normalizes committing the file.
**Fix:** Add `.gitignore` (`.env`, `__pycache__/`, `*.pyc`, venvs); `git rm
--cached .env`; ship `.env.example` only; remove hardcoded keys from `app.py`;
**rotate** any key ever placed in source or a real `.env`; consider a secrets
manager for deployment. Add a pre‑commit secret scanner (gitleaks/trufflehog).

### SEC‑05 🟠 Cleartext API key over HTTP
**Where:** `get_towers` — `http://opencellid.org/cell/getInArea` with `key=` in
query (`app.py:232`, `app-env.py:288`).
**Impact:** Key and request are interceptable on‑path; also lands in any proxy
logs.
**Fix:** Use HTTPS; move the key out of the query string where the API allows;
treat the key as compromised and rotate.

### SEC‑06 🟠 Upstream error/detail reflection + debug tracebacks
**Where:** `get_towers`/`get_celltower` return `details: response.text[:100]`;
`debug=True` returns full tracebacks on any 500.
**Impact:** Information disclosure (provider internals, stack frames, file paths)
useful for enumeration.
**Fix:** Log details server‑side; return generic client messages; disable debug.

### SEC‑07 🟡 Missing request timeouts → DoS / resource exhaustion
**Where:** every `requests.get/post` in both backends.
**Impact:** A slow upstream holds a worker open; enough concurrent slow requests
exhaust the (already limited) dev‑server capacity — a cheap DoS.
**Fix:** `timeout=(3.05, 10)` on all calls via a shared `requests.Session`; add
circuit‑breaking/back‑off.

### SEC‑08 🟡 No security headers / CSP
**Where:** all responses.
**Impact:** No `Content-Security-Policy`, `X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`. A CSP would have blunted SEC‑02.
**Fix:** Add Flask‑Talisman or a manual `after_request` header set; ship a strict
CSP (self + pinned CDN hashes, or self‑host assets).

### SEC‑09 🟡 Supply‑chain: unpinned deps + unversioned CDNs
**Where:** `WireTapper.txt` (no versions); template loads Leaflet, MarkerCluster,
Font Awesome, highlight.js from CDNs **without SRI**.
**Impact:** A compromised/updated CDN asset executes in the operator's browser;
unpinned Python deps yield non‑reproducible, potentially vulnerable builds.
**Fix:** Pin Python deps with hashes; add Subresource Integrity (`integrity=` +
`crossorigin`) to every CDN tag, or self‑host and version the assets.

### SEC‑10 ⚪ CSRF on state/telemetry endpoints (latent)
**Where:** `/log-activity`, `/chatgpt` (POST) — currently unimplemented but wired
in the client.
**Impact:** When implemented as unauthenticated JSON POSTs they are CSRF‑able and
(for `/chatgpt`) a cost/abuse vector.
**Fix:** Add CSRF protection / same‑site checks and auth before shipping them.

---

## Quick‑win order (attacker‑risk vs. effort)
1. SEC‑01 (one line) → 2. SEC‑04 (gitignore + rotate) → 3. SEC‑02 (escape output)
→ 4. SEC‑07 (timeouts) → 5. SEC‑03 (auth + rate limit) → 6. SEC‑05/06/08/09.
