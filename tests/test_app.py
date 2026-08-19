"""Regression tests for the WireTapper backend.

Run: pip install -r requirements.txt -r requirements-dev.txt && pytest

Outbound HTTP is stubbed so no real network / API keys are needed.
"""

import importlib.util
import os
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


# ---- rate limiting (SEC-03)

def test_rate_limit_enforced(app_module):
    if not getattr(app_module, "_LIMITER_ENABLED", False):
        pytest.skip("Flask-Limiter not installed")
    app_module.limiter.reset()
    c = app_module.app.test_client()
    codes = [c.get("/nearby?lat=1&lon=1&demo=1").status_code for _ in range(125)]
    assert codes.count(200) == 120
    assert codes.count(429) == 5
