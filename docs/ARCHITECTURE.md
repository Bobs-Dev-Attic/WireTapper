# WireTapper — Architecture & Data Flow (agent‑oriented map)

Purpose: give an AI agent or new contributor the whole system in one screen so
they don't re‑read every file. Keep this in sync when routes/flows change.

## Stack
- **Backend:** Python 3 + Flask (single module). Two near‑duplicate entrypoints:
  - `app.py` — API keys **hardcoded** in source (placeholders). No wpa‑sec.
  - `app-env.py` — keys from `os.getenv`; **adds `wpasec_kquery`**. Preferred base.
- **Frontend:** one server‑rendered Jinja template `templates/wifi-search.html`
  (Leaflet + MarkerCluster + Font Awesome + highlight.js via CDN). All app logic
  is inline `<script>`.
- **Config:** `.env` (tracked, placeholders). ⚠️ **No `load_dotenv()` anywhere** —
  `.env` file is NOT actually read; only real shell exports reach `os.getenv`.
- **Deps:** `WireTapper.txt` = `Flask`, `requests` (unpinned).

## External services
| Service | Used for | Endpoint(s) | Auth |
|---|---|---|---|
| Wigle | Wi‑Fi + BT networks by bbox/ssid/bssid | `api.wigle.net/api/v2/{network,bluetooth}/search` | HTTP Basic (`WIGLE_API_NAME`/`TOKEN`) |
| UnwiredLabs | cell geolocation | `us1.unwiredlabs.com/v2/process.php` | token in JSON (`OPENCELLID_API_KEY`) |
| OpenCellID | towers in area | `opencellid.org/cell/getInArea` (**http**), `www.opencellid.org/ajax/getCells.php` | key in query / none |
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

## Routes referenced by the frontend but **NOT implemented** (all 404)
`/` · `/crmx` · `/surveillance` · `/profiles` · `/geo` · `/cctv` · `/mobile` ·
`/social` · `/alerts` · `/fit` · `/settings` · `/logout` · `/api/username` ·
`/log-activity` (POST beacon) · `/chatgpt` (POST). Treat these as TODO/stubs.

## Request → response flow (`/nearby`, wifi mode)
```
Browser click on map
  → GET /nearby?lat&lon&mode=wifi
    → Wigle network/search (bbox ±0.01°)         → map results → devices[]
      → wpasec_kquery(devices): sha1(bssid+hex(ssid)), send 4‑char prefixes
        to wpa-sec/bmacssid, match returned suffixes → device.leaked=True
    → UnwiredLabs process.php (cells)             → devices[]
    → Shodan host/search geo:lat,lon,1 (if key)   → devices[]
  → if devices empty: inject DUMMY_DATA           ⚠️ masks real failures
  → JSON {devices:[...]}
Browser updateMap(): filter by checkboxes → Leaflet markers + sidebar cards
  ⚠️ ssid/vendor/bssid injected via innerHTML/bindPopup UNESCAPED (XSS)
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

## Known‑bug hot spots (line refs, `app-env.py`)
- L129 `if not lat or not lon` — rejects valid 0.0 coordinates.
- L102‑105 `requests.post(... jsonify(list(clids)).get_data())` — works only in
  request context; no timeout.
- L226+ Shodan `query` from user is unbounded — cost/abuse.
- L288 OpenCellID over **http** with key in query.
- Template L1693/L1762/L2149 — `innerHTML` XSS sinks.

## If you change things
- Prefer editing **one** consolidated backend; delete or thin the duplicate.
- Keep the device object shape stable — the template depends on these exact keys.
- Update this file + `/TODO.md` when routes or the contract change.
