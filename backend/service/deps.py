from typing import Iterator

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from service import db as dbmod
from service.session import session_store


def get_db() -> Iterator[Session]:
    assert dbmod.SessionLocal is not None, "DB not initialized"
    s = dbmod.SessionLocal()
    try:
        yield s
    finally:
        s.close()


def require_auth(request: Request) -> str:
    """Dependency that validates session and returns username."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    data = session_store.get_session(session_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
    return data.username
