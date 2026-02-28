"""
DataScout — Output Formatters.

Utilities for formatting numbers, tables, statistics, and markdown
output for clean display in the Streamlit UI.
"""

from typing import Any, Dict, List, Optional

import pandas as pd


def format_number(value: float, precision: int = 2, prefix: str = '',
                  suffix: str = '') -> str:
    """Format a number with thousand separators and optional prefix/suffix.

    Args:
        value: The numeric value to format.
        precision: Number of decimal places.
        prefix: String to prepend (e.g., '$').
        suffix: String to append (e.g., '%').

    Returns:
        Formatted number string.
    """
    formatted = f"{value:,.{precision}f}"
    return f"{prefix}{formatted}{suffix}"


def format_table(data: List[Dict[str, Any]], max_rows: int = 50) -> pd.DataFrame:
    """Convert list of dicts to a pandas DataFrame for display.

    Args:
        data: List of row dictionaries.
        max_rows: Maximum number of rows to include.

    Returns:
        pandas DataFrame ready for Streamlit display.
    """
    df = pd.DataFrame(data)
    if len(df) > max_rows:
        df = df.head(max_rows)
    return df


def format_stats(stats: Dict[str, Any]) -> str:
    """Format a statistics dictionary as markdown.

    Args:
        stats: Dictionary of stat_name -> value pairs.

    Returns:
        Markdown-formatted string of statistics.
    """
    lines = []
    for key, value in stats.items():
        label = key.replace('_', ' ').title()
        if isinstance(value, float):
            lines.append(f"- **{label}:** {format_number(value)}")
        else:
            lines.append(f"- **{label}:** {value}")
    return '\n'.join(lines)


def format_file_size(size_bytes: int) -> str:
    """Format bytes into a human-readable file size string.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Human-readable size string (e.g., '2.3 MB').
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(milliseconds: int) -> str:
    """Format milliseconds into a human-readable duration.

    Args:
        milliseconds: Duration in milliseconds.

    Returns:
        Formatted duration string (e.g., '1.5s' or '250ms').
    """
    if milliseconds < 1000:
        return f"{milliseconds}ms"
    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    return f"{minutes:.1f}m"
