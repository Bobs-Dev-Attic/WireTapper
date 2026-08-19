"""WireTapper — Wireless OSINT dashboard backend.

This is the single canonical module (P1 consolidation). `app-env.py` is kept as
a thin backwards-compatible shim that imports from here. All configuration comes
from the environment; never hardcode secrets (see docs/SECURITY_AUDIT.md).
"""

import functools
import json
import logging
import os
import random
import re
from hashlib import sha1

import requests
from requests.adapters import HTTPAdapter
from flask import Flask, request, jsonify, render_template

# P1: optional urllib3 retry (degrade gracefully if unavailable)
try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None

# P1: optional .env auto-loading. The documented `.env` method previously did
# nothing because load_dotenv() was never called. Now the file is loaded when
# python-dotenv is installed; otherwise we fall back to real shell exports.
try:
    from dotenv import load_dotenv
    load_dotenv()
    _DOTENV_LOADED = True
except Exception:  # pragma: no cover
    _DOTENV_LOADED = False

__version__ = "0.3.0"

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("wiretapper")

app = Flask(__name__)

# --- Configuration (all from environment) ---
WIGLE_API_NAME = os.getenv("WIGLE_API_NAME", "")
WIGLE_API_TOKEN = os.getenv("WIGLE_API_TOKEN", "")
OPENCELLID_API_KEY = os.getenv("OPENCELLID_API_KEY", "")
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "")

# SEC-03: optional shared-secret gate for data endpoints. When unset the
# endpoints stay open (dev default) but a warning is logged at import time.
API_ACCESS_TOKEN = os.getenv("WIRETAPPER_ACCESS_TOKEN", "")

# SEC-07: connect/read timeouts (seconds) applied to every outbound call.
HTTP_TIMEOUT = (
    float(os.getenv("HTTP_CONNECT_TIMEOUT", "3.05")),
    float(os.getenv("HTTP_READ_TIMEOUT", "10")),
)

# SEC-03: bound user-supplied query length before it reaches upstream APIs.
MAX_QUERY_LEN = int(os.getenv("MAX_QUERY_LEN", "256"))


def _build_session():
    """Shared requests.Session with pooling + bounded retry/back-off (SEC-07)."""
    session = requests.Session()
    if Retry is not None:
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    else:  # pragma: no cover
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": f"WireTapper/{__version__}"})
    return session


HTTP = _build_session()

# SEC-03: per-IP rate limiting via Flask-Limiter when installed; no-op otherwise.
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[os.getenv("RATE_LIMIT_DEFAULT", "240 per hour")],
        storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),
    )
    _LIMITER_ENABLED = True
except Exception:  # pragma: no cover
    limiter = None
    _LIMITER_ENABLED = False
    log.warning("Flask-Limiter not available; rate limiting disabled.")


def rate_limit(spec):
    """Apply a per-view rate limit if Flask-Limiter is available."""
    if _LIMITER_ENABLED:
        return limiter.limit(spec)

    def _identity(func):
        return func

    return _identity


def require_access(func):
    """SEC-03: gate a view behind WIRETAPPER_ACCESS_TOKEN when it is set.

    Token may be supplied via the `X-API-Key` header or an `access_token` query
    param. When the env var is unset the view stays open (dev convenience).
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if API_ACCESS_TOKEN:
            provided = request.headers.get("X-API-Key") or request.args.get(
                "access_token", ""
            )
            if provided != API_ACCESS_TOKEN:
                return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


if not API_ACCESS_TOKEN:
    log.warning(
        "WIRETAPPER_ACCESS_TOKEN is unset: data endpoints are OPEN. Set it "
        "(and send X-API-Key) before exposing this app beyond localhost."
    )

# SEC-08: security headers + Content-Security-Policy. The CSP enumerates the
# CDNs / tile + font hosts the template actually uses. It still needs
# 'unsafe-inline' because all app CSS/JS is inline in the template; that relaxes
# once assets are self-hosted or moved to nonces (SEC-09 follow-up). Toggle the
# whole thing with SECURITY_HEADERS=0 and the CSP alone with CSP_ENABLED=0.
_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdnjs.cloudflare.com",
    "style-src 'self' 'unsafe-inline' https://unpkg.com https://cdnjs.cloudflare.com https://fonts.googleapis.com",
    "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com",
    "img-src 'self' data: blob: https://unpkg.com https://haybnz.web.app "
    "https://*.tile.openstreetmap.org https://server.arcgisonline.com https://*.google.com",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
])


@app.after_request
def set_security_headers(response):
    if os.getenv("SECURITY_HEADERS", "1").lower() in ("0", "false", "no"):
        return response
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    if os.getenv("CSP_ENABLED", "1").lower() not in ("0", "false", "no"):
        response.headers.setdefault("Content-Security-Policy", _CSP)
    return response

# Dummy data for testing (opt-in via ?demo=1; see _maybe_dummy)
DUMMY_DATA = [
    {
        "lat": 51.505,
        "lon": -0.09,
        "ssid": "TestWiFi",
        "bssid": "00:14:22:01:23:45",
        "vendor": "Generic",
        "signal": -65,
        "accuracy": 50,
        "timestamp": "2025-04-11T10:00:00Z",
        "type": "router",
    },
    {
        "lat": 51.507,
        "lon": -0.09,
        "ssid": "TestWiFi2",
        "bssid": "00:14:22:01:23:46",
        "vendor": "Generic",
        "signal": -65,
        "accuracy": 60,
        "timestamp": "2025-04-11T10:00:00Z",
        "type": "router",
        "leaked": True,
    },
    {
        "lat": 51.506,
        "lon": -0.088,
        "cell_id": "123456789",
        "vendor": "N/A",
        "signal": -70,
        "accuracy": 100,
        "timestamp": "2025-04-11T10:01:00Z",
        "type": "cell_tower",
    },
    {
        "lat": 51.504,
        "lon": -0.091,
        "ip": "192.168.1.100",
        "vendor": "CameraCorp",
        "type": "camera",
    },
]


@app.route("/map-w")
def wifi_map():
    return render_template("wifi-search.html")


# Ordered classification rules. Order matters (first match wins) — dashcam
# before camera so "DASH CAM" isn't caught by "CAM"; car before tv so "SYNC"
# etc. resolve first. Keywords are matched on token boundaries (digits+letters
# count as one token), so "CAR" no longer matches OSCAR/SCART and "LG" no longer
# matches FLAGSHIP — the main false-positive source in the old substring logic.
_CLASSIFY_RULES = [
    ("car", ["CAR", "FORD", "TOYOTA", "BMW", "TESLA", "SYNC", "MAZDA", "HONDA", "UCONNECT", "HYUNDAI", "LEXUS", "NISSAN"]),
    ("dashcam", ["DASHCAM", "DASH CAM", "DVR", "70MAI", "VIOFO", "GARMIN DASH"]),
    ("tv", ["TV", "BRAVIA", "VIZIO", "SAMSUNG", "LG", "ROKU", "FIRE", "SMARTVIEW", "KDL"]),
    ("headphone", ["HEADPHONE", "EARBUD", "BOSE", "SONY", "BEATS", "AUDIO", "AIRPOD", "JBL", "SENNHEISER"]),
    ("camera", ["CAM", "SURVEILLANCE", "SECURITY", "NEST", "RING", "ARLO", "HIKVISION", "DAHUA", "REOLINK"]),
    ("iot", ["WATCH", "FITBIT", "GARMIN", "WHOOP"]),
]


def _compile_rules(rules):
    compiled = []
    for label, keywords in rules:
        # A token boundary here means "not flanked by another letter/digit".
        pattern = re.compile(
            r"(?<![A-Z0-9])(?:" + "|".join(re.escape(k) for k in keywords) + r")(?![A-Z0-9])"
        )
        compiled.append((label, pattern))
    return compiled


_CLASSIFY_COMPILED = _compile_rules(_CLASSIFY_RULES)


def classify_device(name, original_type):
    if not name:
        return original_type
    name_upper = name.upper()
    for label, pattern in _CLASSIFY_COMPILED:
        if pattern.search(name_upper):
            return label
    return original_type


def wpasec_kquery(devices):
    if not isinstance(devices, list):
        return devices
    clids = set()
    try:
        for d in devices:
            if d.get("type") == "router" and d.get("bssid") is not None and d.get("ssid") is not None:
                # Normalize BSSID
                bssid = d["bssid"].replace(":", "").replace("-", "").lower()
                if len(bssid) != 12 or not all(c in "0123456789abcdef" for c in bssid):
                    continue
                # Hexlify SSID. Presume utf-8 encoding, which is not always the case
                ssid = d["ssid"].encode("utf-8").hex()
                # Build hash and clid
                d["hash"] = sha1(f"{bssid}{ssid}".encode("ascii")).hexdigest()
                clids.add(d["hash"][:4])

        if not clids:
            return devices

        # Query wpa-sec k-Anonymity interface (SEC-07: timeout + shared session)
        wpasec_response = HTTP.post(
            "https://wpa-sec.stanev.org/bmacssid",
            data=json.dumps(list(clids)),
            timeout=HTTP_TIMEOUT,
        )
        if wpasec_response.status_code == 200:
            wpasec_json = wpasec_response.json()
            for d in devices:
                if "hash" not in d:
                    continue
                suffixes = wpasec_json.get(d["hash"][:4])
                if not suffixes:
                    continue
                for s in suffixes:
                    if d["hash"].endswith(s):
                        d["leaked"] = True
                        break
    except Exception as e:
        log.warning("wpa-sec kquery exception: %s", e)

    return devices


def _maybe_dummy(devices, mode, lat=None, lon=None):
    """Return demo devices only when explicitly requested via ?demo=1.

    Previously fabricated data was injected on ANY empty result, silently
    masking missing keys / upstream failures. It is now opt-in.
    """
    if devices or request.args.get("demo") not in ("1", "true", "yes"):
        return devices
    log.info("Serving demo data for mode=%s (?demo=1)", mode)
    base_lat = lat if lat is not None else 51.505
    base_lon = lon if lon is not None else -0.09
    if mode == "bluetooth":
        return [
            {"lat": base_lat + random.uniform(-0.002, 0.002), "lon": base_lon + random.uniform(-0.002, 0.002), "ssid": "Tesla Model 3", "type": "car", "vendor": "Tesla Motors"},
            {"lat": base_lat + random.uniform(-0.002, 0.002), "lon": base_lon + random.uniform(-0.002, 0.002), "ssid": "Sony WH-1000XM4", "type": "headphone", "vendor": "Sony Corp."},
            {"lat": base_lat + random.uniform(-0.002, 0.002), "lon": base_lon + random.uniform(-0.002, 0.002), "ssid": "Samsung QLED 75", "type": "tv", "vendor": "Samsung Electronics"},
            {"lat": base_lat + random.uniform(-0.002, 0.002), "lon": base_lon + random.uniform(-0.002, 0.002), "ssid": "Hidden_BT_Tracker", "type": "bluetooth", "vendor": "Unknown"},
        ]
    return [
        {"lat": base_lat + random.uniform(-0.001, 0.001), "lon": base_lon + random.uniform(-0.001, 0.001), "ssid": "CYBER_SURVEILLANCE_ROUTER", "type": "router", "vendor": "Cisco Systems"},
        {"lat": base_lat + random.uniform(-0.001, 0.001), "lon": base_lon + random.uniform(-0.001, 0.001), "ssid": "DASHCAM_V3", "type": "camera", "vendor": "Nextbase"},
        {"lat": base_lat + random.uniform(-0.001, 0.001), "lon": base_lon + random.uniform(-0.001, 0.001), "ssid": "5G_TOWER_B4", "type": "cell_tower", "vendor": "Ericsson"},
    ]


@app.route("/nearby")
@rate_limit("120 per hour")
@require_access
def nearby():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    mode = request.args.get("mode", "wifi")  # 'wifi' or 'bluetooth'

    if lat is None or lon is None:
        return jsonify({"error": "Missing coordinates"}), 400

    devices = []

    if mode == "bluetooth":
        # Wigle Bluetooth API call
        try:
            wigle_response = HTTP.get(
                "https://api.wigle.net/api/v2/bluetooth/search",
                params={"latrange1": lat - 0.01, "latrange2": lat + 0.01, "longrange1": lon - 0.01, "longrange2": lon + 0.01},
                auth=(WIGLE_API_NAME, WIGLE_API_TOKEN),
                timeout=HTTP_TIMEOUT,
            )
            if wigle_response.status_code == 200:
                for device in wigle_response.json().get("results", []):
                    name = device.get("name") or device.get("netid")
                    classified_type = classify_device(name, "bluetooth")
                    devices.append({
                        "lat": device.get("trilat"),
                        "lon": device.get("trilong"),
                        "ssid": name,
                        "bssid": device.get("netid"),
                        "vendor": device.get("type") or ("Bluetooth Node" if classified_type == "bluetooth" else classified_type.replace("_", " ").title()),
                        "signal": device.get("level"),
                        "timestamp": device.get("lastupdt"),
                        "type": classified_type,
                    })
            else:
                log.warning("Wigle BT error: %s", wigle_response.status_code)
        except Exception as e:
            log.warning("Wigle BT exception: %s", e)
    else:
        # Wigle WiFi
        try:
            wigle_response = HTTP.get(
                "https://api.wigle.net/api/v2/network/search",
                params={"latrange1": lat - 0.01, "latrange2": lat + 0.01, "longrange1": lon - 0.01, "longrange2": lon + 0.01},
                auth=(WIGLE_API_NAME, WIGLE_API_TOKEN),
                timeout=HTTP_TIMEOUT,
            )
            if wigle_response.status_code == 200:
                for network in wigle_response.json().get("results", []):
                    name = network.get("ssid")
                    classified_type = classify_device(name, "router")
                    devices.append({
                        "lat": network.get("trilat"),
                        "lon": network.get("trilong"),
                        "ssid": name,
                        "bssid": network.get("netid"),
                        "vendor": network.get("vendor"),
                        "signal": network.get("level"),
                        "timestamp": network.get("lastupdt"),
                        "type": classified_type,
                    })
                # Augment devices with wpa-sec leaked data
                devices = wpasec_kquery(devices)
            else:
                log.warning("Wigle error: %s", wigle_response.status_code)
        except Exception as e:
            log.warning("Wigle exception: %s", e)

        # UnwiredLabs / OpenCellID geolocation (HTTPS, token in JSON body)
        try:
            opencell_response = HTTP.get(
                "https://us1.unwiredlabs.com/v2/process.php",
                json={"token": OPENCELLID_API_KEY, "lat": lat, "lon": lon, "address": 0},
                timeout=HTTP_TIMEOUT,
            )
            if opencell_response.status_code == 200:
                data = opencell_response.json()
                if data.get("status") == "ok":
                    for cell in data.get("cells", []):
                        devices.append({
                            "lat": cell.get("lat"),
                            "lon": cell.get("lon"),
                            "cell_id": str(cell.get("cellid")),
                            "signal": cell.get("signal"),
                            "accuracy": cell.get("accuracy"),
                            "timestamp": cell.get("updated"),
                            "type": "cell_tower",
                        })
                else:
                    log.warning("OpenCellID API error: %s", data.get("message", "Unknown error"))
            else:
                log.warning("OpenCellID HTTP error: %s", opencell_response.status_code)
        except Exception as e:
            log.warning("OpenCellID exception: %s", e)

        # Shodan
        if SHODAN_API_KEY:
            try:
                shodan_response = HTTP.get(
                    "https://api.shodan.io/shodan/host/search",
                    params={"key": SHODAN_API_KEY, "query": f"geo:{lat},{lon},1", "limit": 5},
                    timeout=HTTP_TIMEOUT,
                )
                if shodan_response.status_code == 200:
                    for banner in shodan_response.json().get("matches", []):
                        ip = banner["ip_str"]
                        info = banner.get("data", "")
                        classified_type = classify_device(info, "iot_device")
                        devices.append({
                            "lat": banner["location"]["latitude"],
                            "lon": banner["location"]["longitude"],
                            "ip": ip,
                            "info": info[:50],
                            "type": classified_type,
                        })
            except Exception as e:
                log.warning("Shodan exception: %s", e)

    devices = _maybe_dummy(devices, mode, lat, lon)
    return jsonify({"devices": devices})


@app.route("/api/geo/towers")
@rate_limit("120 per hour")
@require_access
def get_towers():
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)

        if lat is None or lon is None:
            lat = 51.505
            lon = -0.09

        # Bounding box (approx 5-10km). 1 deg lat ~= 111km; 0.05 ~= 5.5km
        min_lat, max_lat = lat - 0.05, lat + 0.05
        min_lon, max_lon = lon - 0.05, lon + 0.05
        bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"

        # SEC-05: HTTPS (was http://) so the key is not sent in cleartext.
        response = HTTP.get(
            "https://opencellid.org/cell/getInArea",
            params={"key": OPENCELLID_API_KEY, "BBOX": bbox, "format": "json"},
            timeout=HTTP_TIMEOUT,
        )

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                # SEC-06: don't reflect upstream body to the client.
                log.warning("OpenCellID getInArea returned non-JSON")
                return jsonify({"error": "Upstream returned non-JSON"}), 502

            towers = []
            cells = data.get("cells", []) if isinstance(data, dict) else data
            if isinstance(cells, list):
                for cell in cells:
                    towers.append({
                        "id": str(cell.get("cellid", "Unknown")),
                        "lat": float(cell.get("lat")),
                        "lon": float(cell.get("lon")),
                        "lac": cell.get("lac", 0),
                        "mcc": cell.get("mcc", 0),
                        "mnc": cell.get("mnc", 0),
                        "signal": cell.get("signal", 0),
                        "radio": cell.get("radio", "gsm"),
                    })
            return jsonify(towers)

        log.warning("OpenCellID getInArea upstream error: %s", response.status_code)
        return jsonify({"error": "Upstream API error"}), 502

    except Exception as e:
        log.warning("get_towers exception: %s", e)
        return jsonify({"error": "Internal error"}), 500


@app.route("/api/geo/celltower")
@rate_limit("120 per hour")
@require_access
def get_celltower_click():
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)

        if lat is None or lon is None:
            return jsonify({"error": "Missing coordinates"}), 400

        # Small BBOX (approx 2km). Format: min_lon,min_lat,max_lon,max_lat
        min_lat, max_lat = lat - 0.01, lat + 0.01
        min_lon, max_lon = lon - 0.01, lon + 0.01
        bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"

        response = HTTP.get(
            "https://www.opencellid.org/ajax/getCells.php",
            params={"bbox": bbox},
            timeout=HTTP_TIMEOUT,
        )

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                log.warning("OpenCellID getCells returned non-JSON")
                return jsonify({"error": "Upstream returned non-JSON"}), 502

            towers = []
            features = data.get("features", []) if isinstance(data, dict) else []
            for feature in features:
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [0, 0])  # [lon, lat]
                towers.append({
                    "id": str(props.get("cellid", props.get("unit", "Unknown"))),
                    "lat": float(coords[1]),
                    "lon": float(coords[0]),
                    "lac": props.get("area", 0),
                    "mcc": props.get("mcc", 0),
                    "mnc": props.get("net", 0),
                    "signal": props.get("samples", 0),
                    "radio": props.get("radio", "gsm"),
                })
            return jsonify(towers)

        log.warning("OpenCellID getCells upstream error: %s", response.status_code)
        return jsonify({"error": "Upstream API error"}), 502

    except Exception as e:
        log.warning("get_celltower exception: %s", e)
        return jsonify({"error": "Internal error"}), 500


@app.route("/searchzz")
@rate_limit("120 per hour")
@require_access
def search():
    search_type = request.args.get("type")
    query = request.args.get("query")
    if not search_type or not query:
        return jsonify({"error": "Missing search parameters"}), 400

    # SEC-03: bound user-supplied query before forwarding to any upstream.
    query = query[:MAX_QUERY_LEN]

    devices = []
    lat = lon = None

    if search_type == "location":
        try:
            lat, lon = map(float, query.split(","))
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid location format"}), 400

        try:
            wigle_response = HTTP.get(
                "https://api.wigle.net/api/v2/network/search",
                params={"latrange1": lat - 0.01, "latrange2": lat + 0.01, "longrange1": lon - 0.01, "longrange2": lon + 0.01},
                auth=(WIGLE_API_NAME, WIGLE_API_TOKEN),
                timeout=HTTP_TIMEOUT,
            )
            if wigle_response.status_code == 200:
                for network in wigle_response.json().get("results", []):
                    devices.append(_wigle_network_to_device(network))
                devices = wpasec_kquery(devices)
            else:
                log.warning("Wigle location error: %s", wigle_response.status_code)
        except Exception as e:
            log.warning("Wigle location exception: %s", e)

        try:
            opencell_response = HTTP.get(
                "https://us1.unwiredlabs.com/v2/process.php",
                json={"token": OPENCELLID_API_KEY, "lat": lat, "lon": lon, "address": 0},
                timeout=HTTP_TIMEOUT,
            )
            if opencell_response.status_code == 200:
                data = opencell_response.json()
                if data.get("status") == "ok":
                    for cell in data.get("cells", []):
                        devices.append({
                            "lat": cell.get("lat"),
                            "lon": cell.get("lon"),
                            "cell_id": str(cell.get("cellid")),
                            "signal": cell.get("signal"),
                            "accuracy": cell.get("accuracy"),
                            "timestamp": cell.get("updated"),
                            "type": "cell_tower",
                        })
                else:
                    log.warning("OpenCellID location error: %s", data.get("message", "Unknown error"))
            else:
                log.warning("OpenCellID location HTTP error: %s", opencell_response.status_code)
        except Exception as e:
            log.warning("OpenCellID location exception: %s", e)

    elif search_type == "bssid":
        try:
            wigle_response = HTTP.get(
                "https://api.wigle.net/api/v2/network/search",
                params={"netid": query},
                auth=(WIGLE_API_NAME, WIGLE_API_TOKEN),
                timeout=HTTP_TIMEOUT,
            )
            if wigle_response.status_code == 200:
                for network in wigle_response.json().get("results", []):
                    devices.append(_wigle_network_to_device(network))
                devices = wpasec_kquery(devices)
            else:
                log.warning("Wigle BSSID error: %s", wigle_response.status_code)
        except Exception as e:
            log.warning("Wigle BSSID exception: %s", e)

    elif search_type == "ssid":
        try:
            wigle_response = HTTP.get(
                "https://api.wigle.net/api/v2/network/search",
                params={"ssid": query},
                auth=(WIGLE_API_NAME, WIGLE_API_TOKEN),
                timeout=HTTP_TIMEOUT,
            )
            if wigle_response.status_code == 200:
                for network in wigle_response.json().get("results", []):
                    devices.append(_wigle_network_to_device(network))
                devices = wpasec_kquery(devices)
            else:
                log.warning("Wigle SSID error: %s", wigle_response.status_code)
        except Exception as e:
            log.warning("Wigle SSID exception: %s", e)

    elif search_type == "network":
        if SHODAN_API_KEY:
            try:
                shodan_response = HTTP.get(
                    "https://api.shodan.io/shodan/host/search",
                    params={"key": SHODAN_API_KEY, "query": query, "limit": 10},
                    timeout=HTTP_TIMEOUT,
                )
                if shodan_response.status_code == 200:
                    for host in shodan_response.json().get("matches", []):
                        devices.append({
                            "lat": host.get("location", {}).get("latitude"),
                            "lon": host.get("location", {}).get("longitude"),
                            "ip": host.get("ip_str"),
                            "vendor": host.get("org"),
                            "type": host.get("product", "iot"),
                        })
                else:
                    log.warning("Shodan search error: %s", shodan_response.status_code)
            except Exception as e:
                log.warning("Shodan search exception: %s", e)
        else:
            log.info("Shodan search skipped: No API key provided")

    # Demo fallback is opt-in via ?demo=1
    if not devices and request.args.get("demo") in ("1", "true", "yes") and search_type in ["location", "ssid", "bssid", "network"]:
        devices = [d for d in DUMMY_DATA if (
            (search_type == "location" and lat is not None and abs(d["lat"] - lat) < 0.1 and abs(d["lon"] - lon) < 0.1)
            or (search_type == "ssid" and d.get("ssid", "").lower() == query.lower())
            or (search_type == "bssid" and d.get("bssid", "").lower() == query.lower())
            or (search_type == "network" and d.get("ip", "") == query)
        )]

    return jsonify({"devices": devices})


def _wigle_network_to_device(network):
    return {
        "lat": network.get("trilat"),
        "lon": network.get("trilong"),
        "ssid": network.get("ssid"),
        "bssid": network.get("netid"),
        "vendor": network.get("vendor"),
        "signal": network.get("level"),
        "timestamp": network.get("lastupdt"),
        "type": "router",
    }


if __name__ == "__main__":
    # SEC-01: never default to the Werkzeug debugger (RCE) or bind all
    # interfaces. Opt in explicitly via env for local/dev use only, e.g.
    #   FLASK_DEBUG=1 FLASK_HOST=127.0.0.1 python app.py
    # In production serve behind a real WSGI server (gunicorn/uvicorn).
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "8080"))
    app.run(host=host, port=port, debug=debug)
