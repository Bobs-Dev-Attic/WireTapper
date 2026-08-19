# Configuration Reference

WireTapper is configured entirely through **environment variables** (loaded from
`.env` via python-dotenv, or exported in the shell). Nothing is hardcoded. This
is the complete list; `.env.example` is a ready-to-copy template.

**Precedence:** a variable exported in the shell overrides the same key in
`.env`. Unset variables fall back to the defaults below.

---

## Provider API keys

| Variable | Default | Required? | Notes |
|---|---|---|---|
| `WIGLE_API_NAME` | `""` | for Wi-Fi/BT data | Wigle "API Name". |
| `WIGLE_API_TOKEN` | `""` | for Wi-Fi/BT data | Wigle "API Token". |
| `OPENCELLID_API_KEY` | `""` | for cell data | OpenCellID/UnwiredLabs token. |
| `SHODAN_API_KEY` | `""` | for IoT/host data | **Premium** plan required for search. If empty, Shodan is skipped. |

Missing keys don't crash the app — those providers just return nothing. See
[`INSTALL.md`](INSTALL.md) §4 for how to obtain each.

## Server (SEC-01)

| Variable | Default | Notes |
|---|---|---|
| `FLASK_HOST` | `127.0.0.1` | Bind address for the **dev server only** (`python app.py`). Keep localhost; never `0.0.0.0` on a public box. Ignored under gunicorn/Vercel. |
| `FLASK_PORT` | `8080` | Dev-server port. |
| `FLASK_DEBUG` | `0` | `1`/`true` enables the Werkzeug debugger — **RCE risk, dev only**. Never enable on anything reachable by others. |

> These apply only to the built-in dev server. In production the WSGI server
> (gunicorn) or Vercel controls host/port, and the debugger is never active.

## Access control & rate limiting (SEC-03)

| Variable | Default | Notes |
|---|---|---|
| `WIRETAPPER_ACCESS_TOKEN` | `""` (open) | When set, `/nearby`, `/searchzz`, `/api/geo/*` require this token via the `X-API-Key` header or `?access_token=`. **Set it before exposing the app** so anonymous users can't spend your paid API quota. |
| `RATE_LIMIT_DEFAULT` | `240 per hour` | Per-IP limit applied to data endpoints (Flask-Limiter syntax, e.g. `100 per minute`). |
| `RATE_LIMIT_STORAGE` | `memory://` | Limiter backend. `memory://` is per-process — **ineffective on serverless / multi-worker**. Use a shared store there, e.g. `redis://…` (install `limits[redis]`). See [`DEPLOY.md`](DEPLOY.md) §3. |

## HTTP client (SEC-07)

All outbound provider calls share one pooled `requests.Session` with these
timeouts and bounded retries; the independent calls run in parallel (v0.7.0).

| Variable | Default | Notes |
|---|---|---|
| `HTTP_CONNECT_TIMEOUT` | `3.05` | Seconds to establish a connection. |
| `HTTP_READ_TIMEOUT` | `10` | Seconds to wait for a response. Lower it (e.g. `4`) on serverless to fit the function time limit. |
| `MAX_QUERY_LEN` | `256` | Max length of a user-supplied `/searchzz` query before it's forwarded upstream (abuse/cost guard). |

## Response hardening (SEC-08)

| Variable | Default | Notes |
|---|---|---|
| `SECURITY_HEADERS` | `1` | `0`/`false`/`no` disables all security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`). Leave on. |
| `CSP_ENABLED` | `1` | `0`/`false`/`no` drops the `Content-Security-Policy` header only (headers above still send). Disable only if a proxy/CDN sets its own CSP, or while debugging a blocked asset. |

The CSP allows exactly the CDNs (unpkg, cdnjs, Google Fonts) and map-tile hosts
(OpenStreetMap, Esri, Google) the template uses. If you add assets from another
host, extend `_CSP` in `app.py` or self-host them.

## Logging

| Variable | Default | Notes |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Python level: `DEBUG` / `INFO` / `WARNING` / `ERROR`. `DEBUG` surfaces per-provider request detail — useful when results are unexpectedly empty. Avoid `DEBUG` in production (verbose). |

---

## Recommended profiles

**Local development** — just the keys; defaults are fine:
```dotenv
WIGLE_API_NAME=...
WIGLE_API_TOKEN=...
OPENCELLID_API_KEY=...
SHODAN_API_KEY=...
```

**Public / production** — gate access, use a shared rate-limit store, tighten timeouts:
```dotenv
WIGLE_API_NAME=...
WIGLE_API_TOKEN=...
OPENCELLID_API_KEY=...
SHODAN_API_KEY=...
WIRETAPPER_ACCESS_TOKEN=<a long random secret>
RATE_LIMIT_STORAGE=redis://default:<pw>@<host>:<port>
RATE_LIMIT_DEFAULT=60 per hour
HTTP_READ_TIMEOUT=4
LOG_LEVEL=WARNING
# FLASK_* are ignored under gunicorn/Vercel — set host/port/workers there.
```

See [`DEPLOY.md`](DEPLOY.md) for the Vercel/gunicorn specifics that go with the
production profile.
