from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from service.config import settings


class Base(DeclarativeBase):
    pass


engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def create_engine_for_path(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
    )

    @event.listens_for(eng, "connect")
    def _set_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()

    with eng.connect() as _:
        pass
    return eng


def init_engine() -> None:
    global engine, SessionLocal
    engine = create_engine_for_path(settings.db_path)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
