"""Shared pytest fixtures."""
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from service.db import Base, create_engine_for_path


@pytest.fixture
def db_session(tmp_path):
    eng = create_engine_for_path(tmp_path / "test.db")
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng, expire_on_commit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fresh-init TestClient: tmp DB + completely fresh service.* modules.

    Pops every `service` / `service.*` from sys.modules and re-imports in
    dependency order, so ORM classes rebind to a new Base.metadata each
    test. Without this, `Base.metadata.create_all` would no-op on the
    second test in a session because models are bound to a stale Base.
    """
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for mod in [m for m in list(sys.modules) if m == "service" or m.startswith("service.")]:
        sys.modules.pop(mod, None)
    import service.config  # noqa: F401
    import service.db  # noqa: F401
    import service.models  # noqa: F401
    import service.main as mainmod
    with TestClient(mainmod.app) as c:
        yield c
