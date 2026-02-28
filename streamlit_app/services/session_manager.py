"""
DataScout — Session Manager.

Manages user session lifecycle including creation, validation,
timeout enforcement, and cleanup.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from config import Config


class SessionManager:
    """User session lifecycle management.

    Tracks active sessions, enforces timeouts, and coordinates
    session cleanup when sessions expire.
    """

    def __init__(self):
        """Initialize the session manager."""
        self._sessions: Dict[str, dict] = {}

    def create_session(self) -> str:
        """Create a new user session.

        Returns:
            A unique session ID (UUID4).
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            'created_at': datetime.now(timezone.utc),
            'last_active': datetime.now(timezone.utc),
            'query_count': 0,
            'dataset_loaded': False,
            'dataset_uri': None
        }
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Check if a session is valid and not expired.

        Args:
            session_id: The session ID to validate.

        Returns:
            True if the session exists and has not timed out.
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        elapsed = datetime.now(timezone.utc) - session['last_active']
        if elapsed.total_seconds() > Config.SESSION_TIMEOUT_SECONDS:
            self._sessions.pop(session_id, None)
            return False

        return True

    def touch_session(self, session_id: str) -> None:
        """Update the last-active timestamp for a session.

        Args:
            session_id: The session ID to refresh.
        """
        if session_id in self._sessions:
            self._sessions[session_id]['last_active'] = datetime.now(timezone.utc)

    def increment_query_count(self, session_id: str) -> int:
        """Increment and return the query count for a session.

        Args:
            session_id: The session ID.

        Returns:
            Updated query count.
        """
        if session_id in self._sessions:
            self._sessions[session_id]['query_count'] += 1
            self.touch_session(session_id)
            return self._sessions[session_id]['query_count']
        return 0

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Get session metadata.

        Args:
            session_id: The session ID.

        Returns:
            Session info dict, or None if session doesn't exist.
        """
        return self._sessions.get(session_id)

    def end_session(self, session_id: str) -> None:
        """Explicitly end and remove a session.

        Args:
            session_id: The session ID to end.
        """
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        """Remove all expired sessions.

        Returns:
            Number of sessions that were cleaned up.
        """
        now = datetime.now(timezone.utc)
        timeout = timedelta(seconds=Config.SESSION_TIMEOUT_SECONDS)
        expired = [
            sid for sid, info in self._sessions.items()
            if (now - info['last_active']) > timeout
        ]
        for sid in expired:
            self._sessions.pop(sid, None)
        return len(expired)
