"""
DataScout — Input Validators.

Validates file formats, sizes, and query inputs to ensure they meet
application constraints before processing.
"""

from pathlib import Path
from typing import Set

from config import Config


def validate_file_format(filename: str, allowed_formats: Set[str] = None) -> bool:
    """Check if a filename has an accepted file extension.

    Args:
        filename: Name of the file to validate.
        allowed_formats: Set of allowed extensions (e.g., {'.csv', '.xlsx'}).
            Defaults to Config.SUPPORTED_FORMATS.

    Returns:
        True if the file extension is in the allowed list.
    """
    if allowed_formats is None:
        allowed_formats = Config.SUPPORTED_FORMATS

    ext = Path(filename).suffix.lower()
    return ext in allowed_formats


def validate_file_size(size_mb: float, max_size_mb: float = None) -> bool:
    """Check if a file size is within the allowed limit.

    Args:
        size_mb: File size in megabytes.
        max_size_mb: Maximum allowed size in MB. Defaults to Config.MAX_FILE_SIZE_MB.

    Returns:
        True if the file size is within the limit.
    """
    if max_size_mb is None:
        max_size_mb = Config.MAX_FILE_SIZE_MB

    return size_mb <= max_size_mb


def validate_query(query: str, max_length: int = 500) -> bool:
    """Check if a user query is valid for processing.

    Args:
        query: The user's query string.
        max_length: Maximum allowed character length.

    Returns:
        True if the query is non-empty and within length limits.
    """
    if not query or not query.strip():
        return False
    return len(query.strip()) <= max_length


def sanitize_column_name(name: str) -> str:
    """Sanitize a column name for Python compatibility.

    Replaces special characters with underscores and strips whitespace.

    Args:
        name: Raw column name from the dataset.

    Returns:
        Sanitized column name safe for Python identifiers.
    """
    import re
    sanitized = re.sub(r'[^\w\s]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    sanitized = sanitized.lower()
    if sanitized and sanitized[0].isdigit():
        sanitized = f"col_{sanitized}"
    return sanitized or "unnamed"
