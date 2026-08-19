# WireTapper — Senior Engineering & Multi‑Disciplinary Review

**Reviewed:** 2026‑08‑19 · **Commit:** `7e43d6a` · **Reviewer scope:** full repository

> **Status update:** this review captured the *original* baseline. The prioritized
> findings (P0–P3) have since been remediated across v0.2.0–v0.5.0 — see
> [`CHANGELOG.md`](../CHANGELOG.md) and [`TODO.md`](../TODO.md). Remaining items
> are the carry‑overs in TODO (key rotation, SRI, frontend auth) and
> [`ROADMAP.md`](ROADMAP.md). The sections below are kept as the original
> rationale; don't read them as the current state.

WireTapper is a single‑file **Flask** web app that fronts several OSINT APIs
(Wigle, OpenCellID/UnwiredLabs, Shodan, wpa‑sec) behind a Leaflet map UI and
plots "nearby" wireless devices. This document is the narrative review; the
prioritized, actionable checklist lives in [`/TODO.md`](../TODO.md) and the
attacker's view in [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md). A machine‑oriented
map for AI agents is in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 1. Executive summary

The project is an **early‑stage prototype presented as a platform.** It works as
a demo, but is not production‑ready and — more importantly for a tool in this
category — it has meaningful **security, privacy, and legal exposure** that must
be resolved before it is deployed anywhere reachable by others.

| Dimension | Verdict | One‑line |
|---|---|---|
| Software engineering | ⚠️ Weak | Two near‑duplicate entrypoints, heavy copy‑paste, no tests, no deps pinning. |
| Security (operator) | 🔴 Critical | `debug=True` on `0.0.0.0`, secrets‑in‑source workflow, tracked `.env`, no `.gitignore`. |
| Security (app) | 🔴 High | DOM XSS via unescaped SSID/vendor; unauthenticated 3rd‑party API spend. |
| UX | ⚠️ Mixed | Strong visual identity; ~12 dead nav/endpoints; silent "dummy data" masks failures. |
| Privacy / legal | 🔴 High | Plots people's devices + "leaked" credentials; CC‑BY‑NC license link is broken; no privacy notice. |
| Marketing / positioning | ⚠️ Overclaims | README lists capabilities (BLE, CCTV, vehicles, cell) the code only partially delivers. |

**Top 5 things to fix first** (see TODO for the full list):
1. Turn off `debug=True` and stop binding `0.0.0.0` by default.
2. Add `.gitignore`, untrack `.env`, rotate any key ever pasted into `app.py`.
3. Escape all API/user strings before injecting into the DOM.
4. Make secret loading actually work (`python-dotenv` is never imported).
5. Add timeouts to every outbound `requests` call.

---

## 2. Architecture & correctness (software engineer's lens)

### 2.1 Two divergent entrypoints
`app.py` and `app-env.py` are ~95% identical. `app.py` hardcodes API
placeholders in source; `app-env.py` reads `os.getenv` **and** adds the
`wpasec_kquery` leaked‑credential feature that `app.py` lacks. This is classic
feature drift — a bug fixed in one will not reach the other. **Collapse to one
module** with configuration injected, not duplicated.

### 2.2 The documented `.env` method does not work
`README.md` (Method 2) says you can "define these keys in a `.env` file" and run
`app-env.py`. But **nothing imports `python-dotenv` or calls `load_dotenv()`**
(`grep` confirms zero references). `os.getenv` only sees real shell exports, so
the `.env`‑file path silently yields `None` keys and every result falls through
to dummy data. Either add `python-dotenv` + `load_dotenv()` or correct the docs.

### 2.3 Falsy‑coordinate bug
```python
if not lat or not lon:   # /nearby, /searchzz, /api/geo/*
    return jsonify({"error": "Missing coordinates"}), 400
```
`0.0` is a **valid** coordinate (Gulf of Guinea, the equator, the prime
meridian). `not 0.0` is `True`, so any request on lat=0 or lon=0 is wrongly
rejected (or silently re‑centered to London in `get_towers`). Use
`if lat is None or lon is None`.

### 2.4 No timeouts, no shared session, no pooling
Every upstream call is a bare `requests.get/post(...)` with **no `timeout=`**.
A slow or hung upstream ties up a worker indefinitely; under the dev server this
can wedge the whole app. There is also no `requests.Session`, so every call pays
full TCP+TLS handshake cost and cannot reuse connections. Introduce a module
‑level `Session` with sane `timeout` and a small retry/back‑off adapter.

### 2.5 Fragile parsing & broad excepts
- `wpasec_kquery` indexes `d['type']`, `d['bssid']`, `d['ssid']` directly —
  a `KeyError` on any malformed device aborts the whole enrichment loop.
- Multiple bare `except:` (e.g. location split, JSON parse) swallow real errors
  and make debugging opaque.
- `classify_device` uses naive substring matching: `"CAR"` matches `OSCAR`,
  `SCART`; `"LG"` matches `FLAGSHIP`; `"TV"` matches `PARTVILLE`. High false
  ‑positive rate. Prefer word‑boundary/token matching and an ordered rule set.

### 2.6 "Dummy data" fallback hides failures
When any provider returns nothing (or, in practice, when keys are missing), the
endpoints inject fabricated devices (`CYBER_SURVEILLANCE_ROUTER`, `Tesla Model
3`, …). This conflates "no results" with "misconfigured/broken" and, in a tool
whose entire value is data fidelity, is actively misleading. Make it an explicit
opt‑in (`?demo=1`) and otherwise return an honest empty set + status.

### 2.7 Dependency hygiene
`WireTapper.txt` (an unusual name for `requirements.txt`) pins nothing:
```
Flask
requests
```
No versions, no `python-dotenv`, no WSGI server, no hashes. Rename to
`requirements.txt`, pin versions, and add a production server (gunicorn/uvicorn).

### 2.8 No tests, no CI, no linting
There is no test suite, no `pytest`, no GitHub Actions workflow, no formatter/
linter config. For an app that parses several third‑party JSON shapes, contract
tests around the response‑mapping code would catch most real bugs cheaply.

---

## 3. Security — operator/deployment (defensive lens)

- 🔴 **`app.run(host="0.0.0.0", port=8080, debug=True)`.** The Werkzeug
  interactive debugger allows **arbitrary code execution** on any unhandled
  exception, and `0.0.0.0` exposes it to the whole network. This is the single
  most dangerous line in the repo.
- 🔴 **Secrets‑in‑source workflow.** README Method 1 instructs users to paste
  live keys into `app.py`. Combined with **no `.gitignore`** and a **tracked
  `.env`**, this is a recipe for committed credentials. Any key ever placed in
  `app.py` or a real `.env` should be considered burned and rotated.
- 🟠 **Cleartext key transmission.** `get_towers` calls
  `http://opencellid.org/cell/getInArea` over plain HTTP with the API key in the
  query string — interceptable on the wire and in proxy logs.
- 🟠 **Keys in query strings.** Shodan and OpenCellID keys travel as URL params,
  which land in access logs, browser history (if ever proxied), and error text
  that the app sometimes echoes back to clients (`details: response.text[:100]`).
- 🟠 **No authn/authz, no rate limiting.** The UI implies login/logout/admin, but
  every endpoint is open. Anyone who can reach the app can spend the operator's
  paid Shodan/Wigle quota at will (see §4).

## 4. Security — application/attacker (penetration‑tester lens)

Full detail with repro steps in [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md). Headlines:

- 🔴 **DOM‑based XSS via SSID/vendor/BSSID.** `updateMap()` and `renderSidebar()`
  build markup with template literals and assign via `innerHTML`/`bindPopup`
  using **unescaped** `ssid`, `vendor`, `bssid`, `ip`, `info`. Wi‑Fi SSIDs are
  attacker‑controlled free text; an SSID like `<img src=x onerror=alert(1)>`
  (already present in Wigle data, or supplied via the `ssid` search) executes in
  the operator's browser. The chat `addMessage` override also does
  `div.innerHTML = text` on server replies.
- 🟠 **Third‑party API abuse / cost amplification.** `/searchzz?type=network`
  passes the raw `query` straight into a Shodan search using the operator's
  **premium** key — an unauthenticated visitor can run arbitrary Shodan queries
  on the operator's dime and exfiltrate results.
- 🟠 **Verbose upstream error reflection.** Several endpoints return
  `response.text[:100]` from upstreams to the client, leaking provider internals
  and aiding enumeration. `debug=True` compounds this with full tracebacks.
- 🟡 **SSRF surface is currently low** (upstream hosts are hardcoded) but the
  pattern of forwarding user input into outbound requests is the seed of one;
  keep host allow‑listing explicit if endpoints are ever parameterized.

## 5. UX / product design (designer's lens)

**Strengths.** Coherent "cyber‑surveillance" visual language, responsive grid,
map/list split, live filtering, satellite/hybrid layers, relative‑time labels.

**Problems.**
- **~12 dead links.** The sidebar and header wire up `/crmx`, `/surveillance`,
  `/profiles`, `/geo`, `/cctv`, `/mobile`, `/social`, `/alerts`, `settings`,
  `/logout`, and JS calls `/api/username`, `/log-activity`, `/chatgpt` — **none
  of these routes exist** in either backend. Every one is a 404 or a silent
  fetch failure. Either build them, hide them, or mark them "coming soon."
- **Silent failure.** When a fetch fails the user sees fabricated data or a 3s
  toast; there is no persistent error/empty state explaining *why* (missing key,
  quota, upstream down).
- **Mixed branding.** The app is "WireTapper" but the UI says "HayOS / H9 EYE /
  Hayden." Pick one identity; the inconsistency reads as unfinished.
- **Accessibility.** `<center>` tags, icon‑only controls without labels, color
  ‑only signal encoding, and neon‑on‑near‑black text with low contrast fail WCAG
  AA in places. Add labels, focus states, and a contrast pass.
- **Client‑side telemetry.** The page beacons a `username` cookie + click text +
  dwell time to `/log-activity` (which doesn't exist) on every interaction —
  surveillance‑of‑the‑user inside a surveillance tool. Remove or disclose it.

## 6. Privacy, legal & ethics (legal/compliance lens)

- 🔴 **This tool processes personal data.** Mapping devices to locations, and
  especially surfacing **"WPA‑SEC LEAKED"** credentials against real BSSIDs, is
  processing of personal/identifying data under **GDPR/CCPA**. There is no
  privacy notice, lawful‑basis statement, data‑retention policy, or DPA. Even
  though wpa‑sec's k‑anonymity query is privacy‑preserving *for the query*, the
  **result** ("this specific network's password is public") is sensitive.
- 🔴 **Broken license reference.** README links `[LICENSE](LICENSE)` but the file
  is named `LICENSE-NONCOMMERCIAL.md`; the standard `LICENSE` GitHub recognizes
  is absent. Fix the filename/link so the CC‑BY‑NC‑4.0 terms actually bind.
- 🟠 **"Unauthorized use is strictly prohibited" is not a control.** The README
  and SECURITY.md assert ethical/lawful use but nothing enforces or even warns
  in‑product. Add an interstitial acknowledgement and a clear "authorized
  networks only" statement, and document lawful use per jurisdiction.
- 🟠 **Third‑party ToS.** Shodan, Wigle, and OpenCellID each restrict
  redistribution and automated querying. Re‑serving their data through a public
  endpoint likely violates their terms; document compliant usage.

## 7. Marketing / positioning (founder/exec lens)

The README sells a "Wireless OSINT & Signal Intelligence **Platform**" that
"detects and correlates signals" across Wi‑Fi, BLE, CCTV, vehicles, wearables,
smart TVs, IoT and cell towers "in real time." In reality the app **queries
historical third‑party databases** (not live RF), device "types" are guessed
from SSID substrings, and several categories exist only as icons. The gap between
claim and capability is a credibility and (for a security product) trust risk.
Right‑size the copy to what ships, and keep a public roadmap for the rest.

## 8. What's genuinely good

- The **wpa‑sec k‑anonymity** integration (prefix‑only query, local suffix match)
  is a thoughtful, privacy‑aware design choice and the best‑engineered part.
- The map UX, theming, and filter interactions are polished for a prototype.
- Docs scaffolding (CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, issue/PR templates)
  shows good open‑source hygiene intent.

---

*See [`/TODO.md`](../TODO.md) for the prioritized remediation plan.*
