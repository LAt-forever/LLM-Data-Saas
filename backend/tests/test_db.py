from sqlalchemy import text
from service.db import create_engine_for_path, init_engine, SessionLocal


def test_create_engine_enables_wal(tmp_path):
    db = tmp_path / "x.db"
    engine = create_engine_for_path(db)
    with engine.connect() as conn:
        mode = conn.execute(text("PRAGMA journal_mode")).scalar()
    assert mode.lower() == "wal"


def test_init_engine_sets_module_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "y.db"))
    from importlib import reload
    import service.config as cfg; reload(cfg)
    import service.db as dbmod; reload(dbmod)
    dbmod.init_engine()
    with dbmod.SessionLocal() as s:
        assert s.execute(text("SELECT 1")).scalar() == 1
