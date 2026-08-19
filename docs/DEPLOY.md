# Deploying WireTapper to Vercel

WireTapper runs on Vercel as a **Python serverless function** (WSGI). The repo
ships the config to do this:

- `api/index.py` — re-exports the Flask `app` from `app.py` as the WSGI handler.
- `vercel.json` — routes all paths to that function and bundles `templates/`.
- `.vercelignore` — keeps tests/docs/images out of the function bundle.

Because Vercel imports the `app` object directly, `app.py`'s `app.run(...)` dev
server never runs — so there's no debugger/`0.0.0.0` exposure to worry about.

## 1. Deploy

Either connect the GitHub repo in the Vercel dashboard (Import Project), or:

```bash
npm i -g vercel
vercel          # preview deploy
vercel --prod   # production
```

Vercel installs `requirements.txt` and uses Python 3.12 (satisfies our `>=3.10`
floor).

> **Note:** `.vercelignore` excludes `pyproject.toml` on purpose. It holds only
> ruff/pytest config (no `[project]` table); if Vercel's uv-based builder sees
> it, `uv lock` fails with *"No `project` table found"*. Excluding it makes the
> builder use `requirements.txt`.

## 2. Environment variables (Project → Settings → Environment Variables)

Set these instead of a `.env` file (which is git-ignored and not deployed):

| Variable | Purpose | Notes |
|---|---|---|
| `WIGLE_API_NAME`, `WIGLE_API_TOKEN` | Wigle auth | required for Wi-Fi/BT data |
| `OPENCELLID_API_KEY` | OpenCellID/UnwiredLabs | required for cell data |
| `SHODAN_API_KEY` | Shodan | optional; **premium** for search |
| `WIRETAPPER_ACCESS_TOKEN` | gate the data endpoints | **strongly recommended** in prod (see §4) |
| `RATE_LIMIT_STORAGE` | rate-limit backend | **set to a Redis URL** on serverless (see §3) |
| `HTTP_READ_TIMEOUT` | per-call read timeout (s) | **lower it** on serverless (see §5) |
| `RATE_LIMIT_DEFAULT` | e.g. `240 per hour` | optional |
| `MAX_QUERY_LEN` | Shodan/Wigle query cap | optional (default 256) |

Do **not** set `FLASK_DEBUG` in production.

## 3. Rate limiting on serverless ⚠️

Flask-Limiter's default `memory://` store is **per-instance**. Serverless
instances are ephemeral and not shared, so in-memory limits reset constantly and
provide **no real protection**. Use a shared store:

1. Create a Redis (e.g. Vercel's Upstash integration — free tier is fine).
2. Set `RATE_LIMIT_STORAGE` to its URL, e.g. `rediss://default:<pw>@<host>:<port>`.
3. Add the Redis client to `requirements.txt` (Flask-Limiter needs it for Redis):
   ```
   limits[redis]
   ```
   (Kept out of the default deps so local/dev installs stay lean.)

Without this, keep expectations low: the limiter will run but won't meaningfully
throttle a distributed caller.

## 4. Access control

The data endpoints (`/nearby`, `/searchzz`, `/api/geo/*`) are **open** unless
`WIRETAPPER_ACCESS_TOKEN` is set. A public Vercel URL with real API keys and no
token lets anyone spend your Wigle/Shodan quota. Set the token and send it as the
`X-API-Key` header (or `?access_token=`). Note the built-in UI does **not** send
this header yet (tracked in `TODO.md`/`docs/ROADMAP.md`), so today the token gate
is best paired with an external auth layer (e.g. Vercel Authentication /
password protection) if you expose the map UI itself.

## 5. Function timeout vs. upstream calls

`/nearby` and `/searchzz` now call the independent providers **concurrently**
(v0.7.0), so wall-clock ≈ the *slowest* provider (Wigle + its wpa-sec follow-up)
rather than the sum of all of them. That keeps most requests comfortably under
**Vercel's function limit** (10s Hobby, ~60s Pro). Still, a single slow provider
plus retries can add up, so:

- Set `HTTP_READ_TIMEOUT` to something like `4` for extra headroom.
- On Pro, you can also raise the function `maxDuration`.

## 6. Content-Security-Policy

The app sends a CSP allowing the CDNs it uses (unpkg, cdnjs, Google Fonts) and
the map tile hosts. It works as-is on Vercel. If you put the app on a custom
domain behind additional tooling, re-check the CSP.

## Alternative: any WSGI host

The same `app:app` WSGI target runs under gunicorn on a normal server/container:

```bash
gunicorn -w 2 -b 0.0.0.0:8080 app:app   # behind nginx/TLS
```

That path avoids the serverless caveats (§3, §5) at the cost of managing a host.
