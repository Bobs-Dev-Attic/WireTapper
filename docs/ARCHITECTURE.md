# WireTapper — Architecture & Data Flow (agent‑oriented map)

Purpose: give an AI agent or new contributor the whole system in one screen so
they don't re‑read every file. Keep this in sync when routes/flows change.

> Updated for **v0.3.0** (P1 consolidation). Backends are now unified.

## Stack
- **Backend:** Python 3 + Flask, **single canonical module `app.py`**.
  `app-env.py` is a thin shim (`from app import app`) kept for backward compat;
  `app.py` includes env config + `wpasec_kquery`. WSGI targets: `app:app` (or
  `app-env:app`).
- **Frontend:** one server‑rendered Jinja template `templates/wifi-search.html`
  (Leaflet + MarkerCluster + Font Awesome + highlight.js via CDN). All app logic
  is inline `<script>`.
- **Config:** env vars, auto‑loaded from `.env` via `python-dotenv` (`.env` is
  gitignored; see `.env.example`). Keys: `WIGLE_API_NAME/TOKEN`,
  `OPENCELLID_API_KEY`, `SHODAN_API_KEY`. Server/security knobs: `FLASK_HOST/
  PORT/DEBUG`, `WIRETAPPER_ACCESS_TOKEN`, `RATE_LIMIT_DEFAULT`,
  `HTTP_CONNECT_TIMEOUT`, `HTTP_READ_TIMEOUT`, `MAX_QUERY_LEN`.
- **Deps:** `requirements.txt` (pinned) = Flask, Werkzeug, requests,
  python-dotenv, Flask-Limiter, gunicorn. `requirements-dev.txt` = pytest.
  dotenv/limiter imported defensively.
- **Cross‑cutting:** all outbound calls use one shared `requests.Session`
  (`HTTP`) with timeouts + retry/pooling. Every response carries security
  headers + a CSP (`after_request`). Data endpoints are rate‑limited and behind
  an optional `X-API-Key` gate. Demo data is opt‑in via `?demo=1`.
- **Tests:** `tests/test_app.py` (pytest) — `pytest` from repo root; HTTP stubbed.
- **Prod:** `gunicorn -w 2 -b 127.0.0.1:8080 app:app` (never the dev server).

## External services
| Service | Used for | Endpoint(s) | Auth |
|---|---|---|---|
| Wigle | Wi‑Fi + BT networks by bbox/ssid/bssid | `api.wigle.net/api/v2/{network,bluetooth}/search` | HTTP Basic (`WIGLE_API_NAME`/`TOKEN`) |
| UnwiredLabs | cell geolocation | `us1.unwiredlabs.com/v2/process.php` | token in JSON (`OPENCELLID_API_KEY`) |
| OpenCellID | towers in area | `opencellid.org/cell/getInArea` (**https** since v0.3.0), `www.opencellid.org/ajax/getCells.php` | key in query / none |
| Shodan | internet‑exposed hosts by geo/query | `api.shodan.io/shodan/host/search` | key in query (**premium** required) |
| wpa‑sec | leaked WPA creds (k‑anonymity) | `wpa-sec.stanev.org/bmacssid` | none (prefix query) |

## Routes (backend) — the ONLY implemented endpoints
| Route | Method | Purpose | Notes |
|---|---|---|---|
| `/map-w` | GET | serve the dashboard | renders `wifi-search.html` |
| `/nearby?lat&lon&mode` | GET | devices near a point (`wifi`/`bluetooth`) | Wigle(+wpa‑sec)+Unwired+Shodan; dummy fallback |
| `/searchzz?type&query` | GET | search by `location`/`bssid`/`ssid`/`network` | dummy fallback |
| `/api/geo/towers?lat&lon` | GET | towers in ~5km bbox | OpenCellID getInArea |
| `/api/geo/celltower?lat&lon` | GET | towers in ~1km bbox | OpenCellID ajax GeoJSON |

## Routes referenced by the frontend but **NOT implemented**
Sidebar links (`/crmx`, `/surveillance`, `/profiles`, `/geo`, `/cctv`,
`/mobile`, `/social`, `/alerts`, `/fit`, `/settings`, `/`, `/logout`) — as of
v0.4.0 these are labeled "SOON" and intercepted with a toast, not live links.
The previously auto‑firing calls to `/api/username`, `/log-activity` (telemetry
beacon), and `/chatgpt` were **removed** in v0.4.0. Don't add calls back to any
unimplemented endpoint.

## Request → response flow (`/nearby`, wifi mode)
```
Browser click on map
  → GET /nearby?lat&lon&mode=wifi
    → Wigle network/search (bbox ±0.01°)         → map results → devices[]
      → wpasec_kquery(devices): sha1(bssid+hex(ssid)), send 4‑char prefixes
        to wpa-sec/bmacssid, match returned suffixes → device.leaked=True
    → UnwiredLabs process.php (cells)             → devices[]
    → Shodan host/search geo:lat,lon,1 (if key)   → devices[]
  → if devices empty AND ?demo=1: inject DUMMY_DATA (opt-in since v0.3.0)
  → JSON {devices:[...]}
Browser updateMap(): filter by checkboxes → Leaflet markers + sidebar cards
  (ssid/vendor/bssid escaped via escapeHtml() since v0.2.0)
```

## Device object shape (backend → frontend contract)
```jsonc
{
  "lat": 51.5, "lon": -0.09,
  "ssid": "…", "bssid": "aa:bb:…", "cell_id": "…", "ip": "…",
  "vendor": "…", "signal": -65, "accuracy": 50,
  "timestamp": "ISO8601 or epoch", "type": "router|cell_tower|camera|car|tv|headphone|dashcam|iot|iot_device|bluetooth",
  "hash": "sha1…", "leaked": true   // added by wpasec_kquery
}
```
`type` is derived by `classify_device(name, original_type)` via **substring**
matching on the SSID/banner (naive; false‑positive prone).

## Resolved hot spots (history — do not reintroduce)
- Falsy‑coordinate bug (`not lat`) → fixed with `is None` (v0.3.0).
- `wpasec_kquery` KeyErrors + no timeout → `.get()` + shared session (v0.3.0).
- Unbounded Shodan `query` → `MAX_QUERY_LEN` + result cap (v0.3.0).
- OpenCellID over http → HTTPS (v0.3.0).
- Template `innerHTML` XSS sinks → `escapeHtml()` (v0.2.0); the `/chatgpt` sink
  is still flagged for sanitization before that endpoint ships (SEC‑10).

## If you change things
- Edit the single backend `app.py`; `app-env.py` is just a shim — don't fork logic.
- Keep the device object shape stable — the template depends on these exact keys.
- Route outbound calls through the shared `HTTP` session (keeps timeouts/retries).
- Update this file + `/TODO.md` + `CHANGELOG.md` when routes/contract/version change.
