"""Shared pytest fixtures."""
import pytest
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
