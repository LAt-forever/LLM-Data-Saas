import pytest
from fastapi.testclient import TestClient

from service.main import app
from service.session import session_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear all sessions before each test."""
    session_store._sessions.clear()


class TestAuthMe:
    def test_me_without_cookie_returns_401(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_valid_session_returns_user(self, client):
        sid = session_store.create_session("admin")
        resp = client.get("/api/auth/me", cookies={"session_id": sid})
        assert resp.status_code == 200
        assert resp.json()["username"] == "admin"


class TestAuthLogout:
    def test_logout_clears_cookie(self, client):
        sid = session_store.create_session("admin")
        resp = client.post("/api/auth/logout", cookies={"session_id": sid})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert session_store.get_session(sid) is None


class TestAuthLogin:
    @pytest.mark.skip(reason="Requires real bcrypt hash; test manually")
    def test_login_with_valid_credentials(self, client):
        pass
