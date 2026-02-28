"""DataScout Utilities — validation, formatting, error handling, and logging."""

# Submodules are imported directly by callers (e.g. app.py).
# Keeping this __init__ import-free avoids side-effects at package load time.

__all__ = [
    'validate_file_format',
    'validate_file_size',
    'format_number',
    'format_table',
    'handle_error',
]
