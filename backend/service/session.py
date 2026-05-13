import secrets
import time
from dataclasses import dataclass
from typing import Optional


SESSION_TTL_SECONDS = 24 * 60 * 60  # 24 hours


@dataclass
class SessionData:
    username: str
    expires_at: float


class SessionStore:
    """In-memory session store. NOT for multi-process deployments."""

    def __init__(self):
        self._sessions: dict[str, SessionData] = {}

    def create_session(self, username: str) -> str:
        """Create a new session and return the session ID."""
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = SessionData(
            username=username,
            expires_at=time.time() + SESSION_TTL_SECONDS,
        )
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data if valid and not expired."""
        data = self._sessions.get(session_id)
        if data is None:
            return None
        if time.time() > data.expires_at:
            del self._sessions[session_id]
            return None
        return data

    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        now = time.time()
        expired = [
            sid for sid, data in self._sessions.items()
            if now > data.expires_at
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


# Global singleton — one store per process
session_store = SessionStore()
