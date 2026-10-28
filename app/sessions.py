"""In-memory session management with TTL."""

import time
import uuid
from typing import Any, Dict, List, Optional, Set

from app.personas import Persona, HIDDEN_FACT_KEYS


SESSION_TTL_SECONDS = 30 * 60  # 30 minutes

_sessions: Dict[str, "Session"] = {}


class Session:
    """Tracks one practice call session."""

    def __init__(self, persona: Persona) -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.persona: Persona = persona
        self.conversation: List[Dict[str, str]] = []
        self.revealed_facts: Set[str] = set()
        self.created_at: float = time.time()

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > SESSION_TTL_SECONDS

    def add_user_message(self, text: str) -> None:
        self.conversation.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        self.conversation.append({"role": "assistant", "content": text})

    def mark_revealed(self, keys: Set[str]) -> None:
        self.revealed_facts |= keys

    @property
    def total_facts(self) -> int:
        return len(HIDDEN_FACT_KEYS)

    @property
    def discovery_ratio(self) -> float:
        if self.total_facts == 0:
            return 0.0
        return len(self.revealed_facts) / self.total_facts


def create_session(persona: Persona) -> Session:
    """Create a new session and store it."""
    _cleanup_expired()
    session = Session(persona)
    _sessions[session.id] = session
    return session


def get_session(session_id: str) -> Session:
    """Look up a session by id. Raises KeyError if missing or expired."""
    _cleanup_expired()
    session = _sessions.get(session_id)
    if session is None or session.is_expired:
        _sessions.pop(session_id, None)
        raise KeyError(f"Session '{session_id}' not found or expired")
    return session


def _cleanup_expired() -> None:
    """Remove expired sessions."""
    expired = [sid for sid, s in _sessions.items() if s.is_expired]
    for sid in expired:
        del _sessions[sid]


def clear_all_sessions() -> None:
    """Clear all sessions (for testing)."""
    _sessions.clear()
