from pathlib import Path
from service.config import settings

def test_settings_defaults_resolve_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg
    reload(cfg)
    assert cfg.settings.data_dir == Path(tmp_path / "data")
    assert cfg.settings.log_dir == Path(tmp_path / "logs")
    assert cfg.settings.db_path == Path(tmp_path / "app.db")

def test_settings_ensure_dirs_creates_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg
    reload(cfg)
    cfg.settings.ensure_dirs()
    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "logs").is_dir()
