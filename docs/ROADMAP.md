# WireTapper — Roadmap & Architecture Options

Honest positioning plus the "better options a senior engineer would consider,"
captured so the review isn't lost. Nothing here is committed work; it's a menu.

## What WireTapper is today (v0.5.0)

A Flask app that **queries public OSINT databases** (Wigle, OpenCellID, Shodan,
wpa-sec) and plots results on a Leaflet map. It is a **historical-database
aggregator**, not a live signal receiver. Device "type" is inferred from SSID/
banner text. It is prototype-grade but now hardened (see `CHANGELOG.md`).

## What it is *not* (right-sizing the marketing)

- ❌ Not real-time RF/SDR capture. ❌ Not packet interception. ❌ Not credential
  cracking. The "leaked" flag surfaces data already public in wpa-sec.
- Several README-advertised categories (BLE, CCTV, vehicles, wearables) are
  **classification labels over third-party data**, not dedicated sensors.

## Near-term (small, high-leverage)

1. **Frontend auth** so `WIRETAPPER_ACCESS_TOKEN` is actually usable end-to-end
   (send `X-API-Key`, or add a login/session). Today the gate works but the
   static UI doesn't send the header.
2. **Finish SRI** — run `scripts/gen_sri.sh` and paste `integrity=` attributes;
   or self-host the CDN assets and drop the `'unsafe-inline'` CSP relaxation.
3. **Response caching** (per-bbox TTL, e.g. `cachetools` or Redis) to cut
   provider quota/cost and latency on repeated queries.
4. **Implement or remove** the "SOON" sidebar modules rather than leaving stubs.

## Medium-term (architecture options)

- **Parallelize upstream calls.** `/nearby` currently calls Wigle → wpa-sec →
  UnwiredLabs → Shodan sequentially. Fanning them out concurrently
  (`concurrent.futures` with the current `requests.Session`, or migrating the
  hot path to `httpx.AsyncClient`) would roughly halve latency.
- **FastAPI + async** if the app grows: native async I/O suits a service whose
  work is mostly fanning out to slow third-party APIs; Pydantic would formalize
  the device contract (currently an implicit dict shape).
- **Typed device contract.** Replace the ad-hoc dict with a dataclass/Pydantic
  model + one serializer, so the template contract is enforced in code and
  tested (a start exists in `tests/test_app.py`).
- **Split frontend from backend.** The single 2k-line template mixes CSS, JS and
  markup; extracting static assets (and self-hosting the libs) improves caching,
  CSP tightening, and maintainability.

## Production hardening (beyond the dev server)

- Serve via **gunicorn/uvicorn behind nginx** (TLS termination, real timeouts,
  worker management). Never the Flask dev server. See `README.md`.
- **Structured logging + metrics** (request IDs, upstream latencies, quota
  counters) instead of `print`/`log.warning`.
- **Secrets manager** (not `.env`) for deployed instances; per-provider key
  rotation.
- **Distributed rate-limit store** (Redis) so limits hold across workers/hosts —
  the current in-memory limiter is per-process.

## Data quality

- `classify_device` is keyword heuristics. A small labeled dataset + a proper
  classifier (or vendor-OUI lookup for BSSIDs) would beat substring rules.
- Surface provider confidence/accuracy in the UI instead of a single signal bar.
