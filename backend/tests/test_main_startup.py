import os
from fastapi.testclient import TestClient


def test_startup_creates_db_and_tables(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg; reload(cfg)
    import service.db as dbmod; reload(dbmod)
    import service.models as modelsmod; reload(modelsmod)
    import service.main as mainmod; reload(mainmod)

    with TestClient(mainmod.app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        # tables created
        from sqlalchemy import inspect
        names = set(inspect(dbmod.engine).get_table_names())
        assert {"api_config", "wordlist", "prompt_template",
                "category", "task", "task_event"} <= names
