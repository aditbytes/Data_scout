"""
Unit Tests — Error Handler.

Tests error classification and user-friendly message display.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestErrorHandler:
    """Unit tests for error handling and messaging."""

    @patch('streamlit_app.utils.error_handler.st')
    def test_known_error_type_value_error(self, mock_st):
        """ValueError displays correct title."""
        from streamlit_app.utils.error_handler import handle_error
        mock_st.session_state = {}
        handle_error(ValueError("Bad input"))
        mock_st.error.assert_called_once()
        error_msg = str(mock_st.error.call_args)
        assert "Invalid Input" in error_msg

    @patch('streamlit_app.utils.error_handler.st')
    def test_known_error_type_timeout(self, mock_st):
        """TimeoutError displays correct title."""
        from streamlit_app.utils.error_handler import handle_error
        mock_st.session_state = {}
        handle_error(TimeoutError("Timed out"))
        error_msg = str(mock_st.error.call_args)
        assert "Timed Out" in error_msg

    @patch('streamlit_app.utils.error_handler.st')
    def test_unknown_error_type(self, mock_st):
        """Unknown errors display default message."""
        from streamlit_app.utils.error_handler import handle_error
        mock_st.session_state = {}
        handle_error(RuntimeError("Unexpected"))
        error_msg = str(mock_st.error.call_args)
        assert "Something Went Wrong" in error_msg

    @patch('streamlit_app.utils.error_handler.st')
    def test_error_stores_in_session_state(self, mock_st):
        """Error message is stored in session state."""
        from streamlit_app.utils.error_handler import handle_error
        mock_st.session_state = {}
        handle_error(ValueError("Test error"))
        assert mock_st.session_state['last_error'] == "Test error"

    @patch('streamlit_app.utils.error_handler.st')
    def test_suggestion_displayed(self, mock_st):
        """Suggestion is displayed alongside error."""
        from streamlit_app.utils.error_handler import handle_error
        mock_st.session_state = {}
        handle_error(ValueError("Bad input"))
        mock_st.info.assert_called_once()
        info_msg = str(mock_st.info.call_args)
        assert "💡" in info_msg

    def test_classify_error_input(self):
        """Input errors are classified correctly."""
        from streamlit_app.utils.error_handler import classify_error
        assert classify_error(ValueError("x")) == 'input'
        assert classify_error(TypeError("x")) == 'input'

    def test_classify_error_network(self):
        """Network errors are classified correctly."""
        from streamlit_app.utils.error_handler import classify_error
        assert classify_error(TimeoutError("x")) == 'network'
        assert classify_error(ConnectionError("x")) == 'network'

    def test_classify_error_unknown(self):
        """Unknown errors are classified as 'unknown'."""
        from streamlit_app.utils.error_handler import classify_error
        assert classify_error(RuntimeError("x")) == 'unknown'
