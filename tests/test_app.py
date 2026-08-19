"""Regression tests for the WireTapper backend.

Run: pip install -r requirements.txt -r requirements-dev.txt && pytest

Outbound HTTP is stubbed so no real network / API keys are needed.
"""

import importlib.util
import os
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load_app_module():
    spec = importlib.util.spec_from_file_location("wiretapper_app", ROOT / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeResp:
    status_code = 200

    def json(self):
        return {"results": [], "cells": [], "matches": [], "features": []}


class _FakeHTTP:
    def get(self, *a, **k):
        return _FakeResp()

    def post(self, *a, **k):
        return _FakeResp()


class _RoutedResp:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload

    def json(self):
        return self._payload


class _RoutedHTTP:
    """Returns realistic per-provider payloads keyed by URL substring."""

    def get(self, url, *a, **k):
        if "wigle.net" in url:
            return _RoutedResp({"results": [{
                "trilat": 51.5, "trilong": -0.09, "ssid": "MyNet",
                "netid": "AA:BB:CC:DD:EE:FF", "vendor": "Cisco",
                "level": -60, "lastupdt": "2025-01-01T00:00:00Z",
            }]})
        if "unwiredlabs.com" in url:
            return _RoutedResp({"status": "ok", "cells": [{
                "lat": 51.51, "lon": -0.08, "cellid": 12345,
                "signal": -70, "accuracy": 100, "updated": "2025-01-01",
            }]})
        return _RoutedResp({"matches": [], "features": []})

    def post(self, *a, **k):
        return _RoutedResp({})  # wpa-sec: no leaked suffixes


@pytest.fixture()
def app_module():
    os.environ.pop("WIRETAPPER_ACCESS_TOKEN", None)
    m = _load_app_module()
    m.HTTP = _FakeHTTP()
    if getattr(m, "_LIMITER_ENABLED", False):
        m.limiter.reset()
    return m


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


# ---- classify_device: word-boundary matching (no more substring false positives)

@pytest.mark.parametrize("name,expected", [
    ("Tesla Model 3", "car"),
    ("Ford SYNC", "car"),
    ("Samsung QLED 75", "tv"),
    ("Sony WH-1000XM4", "headphone"),
    ("DASH CAM Pro", "dashcam"),      # dashcam wins over camera ("CAM")
    ("Ring Doorbell", "camera"),
    ("Fitbit Charge", "iot"),
    ("OSCAR-Home", "router"),          # 'CAR' inside OSCAR must NOT match car
    ("FLAGSHIP-5G", "router"),         # 'LG' inside FLAGSHIP must NOT match tv
    ("PARTVILLE_WIFI", "router"),      # 'TV' inside PARTVILLE must NOT match tv
    ("", "router"),                     # empty name -> original type
    ("PlainHomeNetwork", "router"),
])
def test_classify_device(app_module, name, expected):
    assert app_module.classify_device(name, "router") == expected


# ---- coordinate handling (0.0 is valid, not "missing")

def test_zero_coords_accepted(client):
    r = client.get("/nearby?lat=0&lon=0")
    assert r.status_code == 200
    assert r.get_json() == {"devices": []}


def test_missing_coords_rejected(client):
    assert client.get("/nearby").status_code == 400


def test_bad_location_search_rejected(client):
    assert client.get("/searchzz?type=location&query=notcoords").status_code == 400


# ---- demo data is opt-in

def test_no_demo_returns_empty(client):
    assert client.get("/nearby?lat=51&lon=-0.1").get_json() == {"devices": []}


def test_demo_flag_returns_devices(client):
    devices = client.get("/nearby?lat=51&lon=-0.1&demo=1").get_json()["devices"]
    assert len(devices) == 3


# ---- access-token gate

def test_access_gate(app_module):
    app_module.API_ACCESS_TOKEN = "secret"
    c = app_module.app.test_client()
    assert c.get("/nearby?lat=1&lon=1").status_code == 401
    assert c.get("/nearby?lat=1&lon=1", headers={"X-API-Key": "secret"}).status_code == 200
    assert c.get("/nearby?lat=1&lon=1&access_token=secret").status_code == 200
    assert c.get("/nearby?lat=1&lon=1&access_token=wrong").status_code == 401


# ---- security headers (SEC-08)

def test_security_headers_present(client):
    r = client.get("/map-w")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in r.headers


# ---- provider -> device mapping contract

def test_nearby_maps_provider_payloads(app_module):
    app_module.HTTP = _RoutedHTTP()
    c = app_module.app.test_client()
    devices = c.get("/nearby?lat=51.5&lon=-0.09").get_json()["devices"]

    routers = [d for d in devices if d["type"] == "router"]
    towers = [d for d in devices if d["type"] == "cell_tower"]
    assert len(routers) == 1
    assert len(towers) == 1

    r = routers[0]
    # Wigle fields mapped onto the device contract
    assert r["lat"] == 51.5 and r["lon"] == -0.09
    assert r["ssid"] == "MyNet"
    assert r["bssid"] == "AA:BB:CC:DD:EE:FF"
    assert r["vendor"] == "Cisco"
    assert r["signal"] == -60

    t = towers[0]
    assert t["cell_id"] == "12345"  # coerced to str
    assert t["accuracy"] == 100


def test_wpasec_kquery_skips_malformed_without_raising(app_module):
    # bad bssid + missing ssid must not raise, and produce no hash
    devices = [
        {"type": "router", "bssid": "not-a-mac", "ssid": "X"},
        {"type": "router", "bssid": "AABBCCDDEEFF", "ssid": None},
        {"type": "cell_tower"},
    ]
    app_module.HTTP = _RoutedHTTP()
    out = app_module.wpasec_kquery(devices)
    assert out is devices
    assert all("hash" not in d for d in out)


# ---- upstream calls run in parallel (not serial)

class _SlowHTTP:
    """Every call sleeps `delay`, so serial vs. parallel is measurable."""

    def __init__(self, delay):
        self.delay = delay

    def get(self, url, *a, **k):
        time.sleep(self.delay)
        if "wigle.net" in url:
            return _RoutedResp({"results": [{
                "trilat": 1, "trilong": 2, "ssid": "N",
                "netid": "AA:BB:CC:DD:EE:FF", "vendor": "V", "level": -1, "lastupdt": "t",
            }]})
        if "unwiredlabs.com" in url:
            return _RoutedResp({"status": "ok", "cells": [{"lat": 1, "lon": 2, "cellid": 9}]})
        if "shodan.io" in url:
            return _RoutedResp({"matches": [{
                "ip_str": "1.2.3.4", "data": "", "location": {"latitude": 1, "longitude": 2},
            }]})
        return _RoutedResp({})

    def post(self, *a, **k):
        time.sleep(self.delay)
        return _RoutedResp({})


def test_nearby_runs_providers_concurrently(app_module):
    app_module.SHODAN_API_KEY = "x"  # enable the shodan branch
    app_module.HTTP = _SlowHTTP(0.2)
    c = app_module.app.test_client()

    t0 = time.perf_counter()
    devices = c.get("/nearby?lat=1&lon=2").get_json()["devices"]
    elapsed = time.perf_counter() - t0

    types = [d["type"] for d in devices]
    # Output still complete and in fixed order (Wigle → cells → Shodan).
    assert "router" in types and "cell_tower" in types
    assert types.index("router") < types.index("cell_tower")
    # Parallel wall-clock ≈ the slowest branch (Wigle get+post ≈ 0.4s), well
    # under the ~0.8s a serial run of all four calls would take.
    assert elapsed < 0.6, f"providers appear to run serially: {elapsed:.2f}s"


# ---- rate limiting (SEC-03)

def test_rate_limit_enforced(app_module):
    if not getattr(app_module, "_LIMITER_ENABLED", False):
        pytest.skip("Flask-Limiter not installed")
    app_module.limiter.reset()
    c = app_module.app.test_client()
    codes = [c.get("/nearby?lat=1&lon=1&demo=1").status_code for _ in range(125)]
    assert codes.count(200) == 120
    assert codes.count(429) == 5
