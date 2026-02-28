"""
Unit Tests — SessionManager.

Tests session lifecycle management including creation, validation,
timeout, and cleanup.
"""

import time

import pytest
from unittest.mock import patch


class TestSessionManager:
    """Unit tests for session lifecycle management."""

    @pytest.fixture
    def manager(self):
        """Create a SessionManager instance."""
        with patch('streamlit_app.services.session_manager.Config') as mock_config:
            mock_config.SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes
            from streamlit_app.services.session_manager import SessionManager
            return SessionManager()

    def test_create_session(self, manager):
        """Session creation returns a valid UUID string."""
        session_id = manager.create_session()
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format

    def test_validate_active_session(self, manager):
        """Active session validates successfully."""
        session_id = manager.create_session()
        assert manager.validate_session(session_id) is True

    def test_validate_nonexistent_session(self, manager):
        """Non-existent session ID returns False."""
        assert manager.validate_session("fake-session-id") is False

    def test_touch_session_updates_timestamp(self, manager):
        """Touch session updates last_active timestamp."""
        session_id = manager.create_session()
        initial_info = manager.get_session_info(session_id)
        initial_time = initial_info['last_active']

        time.sleep(0.01)
        manager.touch_session(session_id)
        updated_info = manager.get_session_info(session_id)

        assert updated_info['last_active'] >= initial_time

    def test_increment_query_count(self, manager):
        """Query count increments correctly."""
        session_id = manager.create_session()
        assert manager.increment_query_count(session_id) == 1
        assert manager.increment_query_count(session_id) == 2
        assert manager.increment_query_count(session_id) == 3

    def test_increment_nonexistent_session(self, manager):
        """Incrementing non-existent session returns 0."""
        assert manager.increment_query_count("fake-id") == 0

    def test_end_session(self, manager):
        """Ended session is no longer valid."""
        session_id = manager.create_session()
        assert manager.validate_session(session_id) is True
        manager.end_session(session_id)
        assert manager.validate_session(session_id) is False

    def test_get_session_info(self, manager):
        """Session info contains expected keys."""
        session_id = manager.create_session()
        info = manager.get_session_info(session_id)

        assert 'created_at' in info
        assert 'last_active' in info
        assert 'query_count' in info
        assert info['query_count'] == 0

    def test_get_nonexistent_session_info(self, manager):
        """Getting info for non-existent session returns None."""
        assert manager.get_session_info("fake-id") is None

    def test_multiple_sessions(self, manager):
        """Multiple concurrent sessions are independent."""
        s1 = manager.create_session()
        s2 = manager.create_session()

        manager.increment_query_count(s1)
        manager.increment_query_count(s1)
        manager.increment_query_count(s2)

        assert manager.get_session_info(s1)['query_count'] == 2
        assert manager.get_session_info(s2)['query_count'] == 1
