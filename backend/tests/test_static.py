# backend/tests/test_static.py
import sys

from fastapi.testclient import TestClient


def test_static_skipped_when_dir_missing(tmp_path, monkeypatch, client):
    # When dist doesn't exist, /healthz still works and /any unknown path is 404
    r = client.get("/healthz")
    assert r.status_code == 200
    r = client.get("/some-random-page")
    assert r.status_code == 404


def test_static_mounted_when_dir_present(tmp_path, monkeypatch):
    dist = tmp_path / "frontend_dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (dist / "assets").mkdir()
    (dist / "assets" / "main.js").write_text("/* js */", encoding="utf-8")

    monkeypatch.setenv("STATIC_DIR", str(dist))
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db  # noqa: F401
    import service.models  # noqa: F401
    import service.main as mainmod

    with TestClient(mainmod.app) as c:
        # / serves index.html
        r = c.get("/")
        assert r.status_code == 200
        assert "app" in r.text
        # Assets served
        r = c.get("/assets/main.js")
        assert r.status_code == 200
        assert "/* js */" in r.text
        # /some/path (SPA route) falls back to index.html
        r = c.get("/tasks/142")
        assert r.status_code == 200
        assert "app" in r.text
        # /api/... NOT redirected to index
        r = c.get("/api/sample-types")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
