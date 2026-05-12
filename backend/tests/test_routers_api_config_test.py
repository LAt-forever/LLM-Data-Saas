# backend/tests/test_routers_api_config_test.py
import json

import httpx
import pytest


def test_api_config_test_endpoint_success(client, monkeypatch):
    """Mock the LLM call to return a successful response."""
    cid = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "http://example.com",
        "api_key": "sk-test", "model_name": "m", "type": "raw"}).json()["id"]

    # Patch the underlying helper in routers.api_configs that does the HTTP call
    from service.routers import api_configs as mod

    def fake_ping(base_url, api_key, model_name, api_type):
        return {"ok": True, "latency_ms": 42, "sample_text": "hello"}

    monkeypatch.setattr(mod, "_ping_llm", fake_ping)

    r = client.post(f"/api/api-configs/{cid}/test")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "latency_ms" in body


def test_api_config_test_endpoint_failure(client, monkeypatch):
    cid = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "http://example.com",
        "api_key": "sk-test", "model_name": "m", "type": "raw"}).json()["id"]

    from service.routers import api_configs as mod

    def fake_ping(*a, **kw):
        return {"ok": False, "error": "connect timeout"}

    monkeypatch.setattr(mod, "_ping_llm", fake_ping)

    r = client.post(f"/api/api-configs/{cid}/test")
    assert r.status_code == 200      # endpoint itself returns 200 with body
    body = r.json()
    assert body["ok"] is False
    assert "error" in body
