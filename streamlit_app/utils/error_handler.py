"""
DataScout — Error Handler.

Classifies errors and displays user-friendly messages with
actionable suggestions in the Streamlit UI.
"""

import logging

import streamlit as st

logger = logging.getLogger('datascout')

# ── Error Message Catalog ─────────────────────────────────────────────────────
ERROR_MESSAGES = {
    'ValueError': {
        'title': '⚠️ Invalid Input',
        'suggestion': 'Please check your file format and try again.'
    },
    'FileNotFoundError': {
        'title': '📁 File Not Found',
        'suggestion': 'The requested file could not be located.'
    },
    'TimeoutError': {
        'title': '⏱️ Request Timed Out',
        'suggestion': 'Try a simpler query or a smaller dataset.'
    },
    'ConnectionError': {
        'title': '🌐 Connection Error',
        'suggestion': 'Check your network connection and try again.'
    },
    'PermissionError': {
        'title': '🔒 Permission Denied',
        'suggestion': 'You don\'t have access to this resource. Contact support.'
    },
    'EnvironmentError': {
        'title': '⚙️ Configuration Error',
        'suggestion': 'Required environment variables may be missing. Check .env file.'
    },
    'default': {
        'title': '❌ Something Went Wrong',
        'suggestion': 'Please try again. If the issue persists, contact support.'
    }
}


def handle_error(error: Exception) -> None:
    """Display a user-friendly error message and log the details.

    Classifies the error by type, shows an appropriate message and
    suggestion to the user, and logs the full traceback for debugging.

    Args:
        error: The exception that was caught.
    """
    error_type = type(error).__name__
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['default'])

    st.error(f"**{error_info['title']}**\n\n{str(error)}")
    st.info(f"💡 {error_info['suggestion']}")

    logger.error(f"[{error_type}] {str(error)}", exc_info=True)
    st.session_state['last_error'] = str(error)


def classify_error(error: Exception) -> str:
    """Classify an error into a user-friendly category.

    Args:
        error: The exception to classify.

    Returns:
        Error category string (e.g., 'input', 'network', 'config', 'unknown').
    """
    error_type = type(error).__name__

    input_errors = {'ValueError', 'TypeError', 'KeyError'}
    network_errors = {'ConnectionError', 'TimeoutError', 'OSError'}
    config_errors = {'EnvironmentError', 'AttributeError'}

    if error_type in input_errors:
        return 'input'
    elif error_type in network_errors:
        return 'network'
    elif error_type in config_errors:
        return 'config'
    return 'unknown'
