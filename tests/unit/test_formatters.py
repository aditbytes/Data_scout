"""
Unit Tests — Formatters.

Tests output formatting utilities for numbers, tables, sizes, and durations.
"""

import pytest
import pandas as pd


class TestFormatters:
    """Unit tests for output formatting utilities."""

    def test_format_number_default(self):
        """Format number with default precision."""
        from streamlit_app.utils.formatters import format_number
        assert format_number(1234567.89) == "1,234,567.89"

    def test_format_number_with_prefix(self):
        """Format number with dollar prefix."""
        from streamlit_app.utils.formatters import format_number
        assert format_number(1234.56, prefix='$') == "$1,234.56"

    def test_format_number_with_suffix(self):
        """Format number with percent suffix."""
        from streamlit_app.utils.formatters import format_number
        assert format_number(85.5, precision=1, suffix='%') == "85.5%"

    def test_format_table_basic(self):
        """Format list of dicts into DataFrame."""
        from streamlit_app.utils.formatters import format_table
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = format_table(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["a", "b"]

    def test_format_table_truncation(self):
        """Large tables are truncated to max_rows."""
        from streamlit_app.utils.formatters import format_table
        data = [{"x": i} for i in range(100)]
        result = format_table(data, max_rows=10)
        assert len(result) == 10

    def test_format_file_size(self):
        """File sizes are formatted correctly."""
        from streamlit_app.utils.formatters import format_file_size
        assert "KB" in format_file_size(1536)
        assert "MB" in format_file_size(2 * 1024 * 1024)
        assert "B" in format_file_size(512)

    def test_format_duration_milliseconds(self):
        """Durations under 1s show in milliseconds."""
        from streamlit_app.utils.formatters import format_duration
        assert format_duration(250) == "250ms"

    def test_format_duration_seconds(self):
        """Durations over 1s show in seconds."""
        from streamlit_app.utils.formatters import format_duration
        assert format_duration(1500) == "1.5s"

    def test_format_duration_minutes(self):
        """Durations over 60s show in minutes."""
        from streamlit_app.utils.formatters import format_duration
        result = format_duration(90000)
        assert "m" in result

    def test_format_stats(self):
        """Stats dict formats as markdown."""
        from streamlit_app.utils.formatters import format_stats
        stats = {"total_revenue": 1234.56, "row_count": 100}
        result = format_stats(stats)
        assert "Total Revenue" in result
        assert "Row Count" in result
