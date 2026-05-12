# backend/tests/test_llm_client.py
import pytest

from service.llm_client import LlmClient, AuthError, RetryExhausted


class _FakeOpenAI:
    """Stand-in for openai.OpenAI client."""
    def __init__(self, responses):
        # responses: list of (kind, value) — kind in ("ok", "rate", "auth", "server")
        self.responses = list(responses)
        self.chat = self
        self.completions = self

    def create(self, **kw):
        import httpx
        _req = httpx.Request("POST", "http://fake.local")
        kind, value = self.responses.pop(0)
        if kind == "ok":
            class M: content = value
            class C: message = M()
            class R: choices = [C()]
            return R()
        if kind == "rate":
            from openai import RateLimitError
            raise RateLimitError(message="429",
                                 response=httpx.Response(429, request=_req),
                                 body=None)
        if kind == "auth":
            from openai import AuthenticationError
            raise AuthenticationError(message="401",
                                      response=httpx.Response(401, request=_req),
                                      body=None)
        if kind == "server":
            from openai import APIStatusError
            raise APIStatusError(message="500",
                                 response=httpx.Response(500, request=_req),
                                 body=None)
        raise RuntimeError(kind)


def test_openai_call_success(monkeypatch):
    fake = _FakeOpenAI([("ok", "hello world")])
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=3, sleep=lambda s: None)
    out = c.call("ping")
    assert out == "hello world"


def test_openai_call_retries_then_succeeds(monkeypatch):
    fake = _FakeOpenAI([("rate", None), ("server", None), ("ok", "got it")])
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=5, sleep=lambda s: None)
    assert c.call("ping") == "got it"


def test_openai_call_raises_auth_error_immediately(monkeypatch):
    fake = _FakeOpenAI([("auth", None)])
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=5, sleep=lambda s: None)
    with pytest.raises(AuthError):
        c.call("ping")


def test_openai_call_exhausts_retries(monkeypatch):
    fake = _FakeOpenAI([("rate", None)] * 10)
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=3, sleep=lambda s: None)
    with pytest.raises(RetryExhausted):
        c.call("ping")


def test_raw_call_success(monkeypatch):
    class FakeResp:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "raw-ok"}}]}
        def raise_for_status(self):
            pass

    def fake_post(url, headers, json, timeout):
        return FakeResp()

    monkeypatch.setattr("service.llm_client.requests.post", fake_post)
    c = LlmClient(base_url="http://x", api_key="k", model_name="m", api_type="raw",
                  max_retries=3, sleep=lambda s: None)
    assert c.call("ping") == "raw-ok"


def test_raw_call_429_then_ok(monkeypatch):
    calls = {"n": 0}
    class Resp429:
        status_code = 429
        text = "rate limit"
        def raise_for_status(self):
            import requests
            raise requests.HTTPError("429", response=self)

    class RespOk:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}
        def raise_for_status(self):
            pass

    def fake_post(url, headers, json, timeout):
        calls["n"] += 1
        return Resp429() if calls["n"] == 1 else RespOk()

    monkeypatch.setattr("service.llm_client.requests.post", fake_post)
    c = LlmClient(base_url="http://x", api_key="k", model_name="m", api_type="raw",
                  max_retries=3, sleep=lambda s: None)
    assert c.call("ping") == "ok"
    assert calls["n"] == 2
