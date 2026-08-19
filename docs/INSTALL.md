# Installing & Running WireTapper

A step-by-step guide from a clean machine to a running instance. For the full
list of configuration knobs see [`CONFIGURATION.md`](CONFIGURATION.md); for
production/serverless deploys see [`DEPLOY.md`](DEPLOY.md).

---

## 1. Prerequisites

- **Python 3.10+** (`python3 --version`). Flask-Limiter 4.x dropped 3.9.
- **git** and **pip**.
- API keys for the providers you want (see §4). Everything except wpa-sec needs
  a key; the app runs without them but returns empty results (or demo data with
  `?demo=1`).

## 2. Get the code

```bash
git clone https://github.com/h9zdev/WireTapper.git
cd WireTapper
```

## 3. Create a virtual environment & install

Using a virtualenv keeps WireTapper's pinned deps isolated from your system.

```bash
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate

pip install -U pip
pip install -r requirements.txt              # runtime
pip install -r requirements-dev.txt          # optional: tests + linter
```

`requirements.txt` is pinned (Flask, Werkzeug, requests, python-dotenv,
Flask-Limiter, gunicorn). `python-dotenv` and `Flask-Limiter` are imported
defensively — if they're absent the app still boots (rate limiting becomes a
no-op).

## 4. Obtain API keys

| Provider | Key(s) | Where to get it |
|---|---|---|
| **Wigle** | `WIGLE_API_NAME`, `WIGLE_API_TOKEN` | Sign in at [wigle.net](https://wigle.net) → **Account** → *Show my token* → use the **API Name** and **API Token** (a.k.a. "Encoded for use"). Free tier has daily query limits. |
| **OpenCellID / UnwiredLabs** | `OPENCELLID_API_KEY` | Create a token at [unwiredlabs.com](https://unwiredlabs.com) (or OpenCellID) and paste the API token. |
| **Shodan** | `SHODAN_API_KEY` | From your [Shodan account](https://account.shodan.io). **Search requires a paid/premium plan.** |
| **wpa-sec** | — | No key. Uses a privacy-preserving k-anonymity query to [wpa-sec.stanev.org](https://wpa-sec.stanev.org). |

Handle keys as secrets — see [`../PRIVACY.md`](../PRIVACY.md) and
[`LEGAL.md`](LEGAL.md) for each provider's terms.

## 5. Configure

Copy the template and fill in your keys:

```bash
cp .env.example .env
# edit .env — at minimum set the provider keys you have
```

`app.py` auto-loads `.env`. Alternatively, `export` the variables in your shell
(useful in CI/containers where you don't want a file). The complete list of
settings and their defaults is in [`CONFIGURATION.md`](CONFIGURATION.md).

> **Security defaults:** the server binds `127.0.0.1` with the debugger **off**.
> Do not set `FLASK_DEBUG=1` or a non-local `FLASK_HOST` on anything reachable by
> others. Before exposing the app, set `WIRETAPPER_ACCESS_TOKEN` (see §7).

## 6. Run

**Local development** (Flask's built-in server — localhost only):

```bash
python app.py
# → serving on http://127.0.0.1:8080  (open /map-w)
```

`app-env.py` is a backward-compatible alias (`python app-env.py` works too).

**Production / anything public** — use a real WSGI server, never the dev server:

```bash
gunicorn -w 2 -b 127.0.0.1:8080 app:app     # put nginx/TLS in front
```

Open **http://localhost:8080/map-w**, acknowledge the lawful-use notice, and
click the map (or use the search bar). No keys yet? Append `?demo=1` to `/nearby`
or `/searchzz` to see sample data.

## 7. Verify

```bash
# health: the dashboard should return 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/map-w

# a data endpoint with demo data (no keys needed)
curl "http://127.0.0.1:8080/nearby?lat=51.5&lon=-0.09&demo=1"
```

Run the test suite (needs `requirements-dev.txt`; HTTP is stubbed, no keys):

```bash
ruff check .
pytest -q          # 23 tests
```

## 8. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ModuleNotFoundError: flask` | venv not activated, or deps not installed (`pip install -r requirements.txt`). |
| App runs but every result is empty | No/invalid API keys, or the provider quota is exhausted. Check logs (`LOG_LEVEL=DEBUG`). Use `?demo=1` to confirm the UI works. |
| `.env` values ignored | `python-dotenv` not installed, **or** you exported a different value in the shell (shell env wins). |
| `401 Unauthorized` on `/nearby` etc. | `WIRETAPPER_ACCESS_TOKEN` is set — send it as the `X-API-Key` header (or `?access_token=`). |
| `429 Too Many Requests` | Rate limit hit (`RATE_LIMIT_DEFAULT`, default 240/hour per IP). Raise it, or set a shared `RATE_LIMIT_STORAGE`. |
| Requests hang / time out | A provider is slow/unreachable. Lower `HTTP_READ_TIMEOUT`. Upstream calls run in parallel (v0.7.0), so latency ≈ the slowest one. |
| Map tiles blank | Tile host blocked by your network/CSP. See `CONFIGURATION.md` (CSP) and `DEPLOY.md`. |

Still stuck? See [`../SECURITY.md`](../SECURITY.md) for how to report issues.
