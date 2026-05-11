from fastapi.testclient import TestClient


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import sys
    for mod in [m for m in list(sys.modules) if m == "service" or m.startswith("service.")]:
        sys.modules.pop(mod, None)
    import service.config as cfg  # noqa: F401
    import service.db as dbmod  # noqa: F401
    import service.models  # noqa: F401  register tables
    import service.main as mainmod
    return TestClient(mainmod.app)


def test_wordlist_crud_and_filter(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as c:
        a = c.post("/api/wordlists", json={
            "name": "scn", "kind": "scenario", "items": ["a", "b"]}).json()
        c.post("/api/wordlists", json={
            "name": "tne", "kind": "tone", "items": ["t1"]})
        r = c.get("/api/wordlists?kind=scenario").json()
        assert len(r) == 1 and r[0]["items"] == ["a", "b"]
        u = c.put(f"/api/wordlists/{a['id']}", json={"items": ["x"]}).json()
        assert u["items"] == ["x"]
        assert c.delete(f"/api/wordlists/{a['id']}").status_code == 204
