from typing import Iterator

from sqlalchemy.orm import Session

from service import db as dbmod


def get_db() -> Iterator[Session]:
    assert dbmod.SessionLocal is not None, "DB not initialized"
    s = dbmod.SessionLocal()
    try:
        yield s
    finally:
        s.close()
