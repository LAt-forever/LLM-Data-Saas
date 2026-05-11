import os
from fastapi.testclient import TestClient


def test_startup_creates_db_and_tables(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import sys
    for mod in [m for m in list(sys.modules) if m == "service" or m.startswith("service.")]:
        sys.modules.pop(mod, None)
    import service.config as cfg  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401  register tables
    import service.main as mainmod

    with TestClient(mainmod.app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        # tables created
        from sqlalchemy import inspect
        names = set(inspect(dbmod.engine).get_table_names())
        assert {"api_config", "wordlist", "prompt_template",
                "category", "task", "task_event"} <= names
