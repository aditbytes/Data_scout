"""
Unit Tests — Validators.

Tests file format, size, and query validation functions.
"""

import pytest
from unittest.mock import patch


class TestValidators:
    """Unit tests for input validation functions."""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        with patch('streamlit_app.utils.validators.Config') as mock_config:
            mock_config.SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls', '.json'}
            mock_config.MAX_FILE_SIZE_MB = 100
            yield

    def _import_validators(self):
        from streamlit_app.utils.validators import validate_file_format, validate_file_size, validate_query
        return validate_file_format, validate_file_size, validate_query

    @pytest.mark.parametrize("filename,expected", [
        ("data.csv", True),
        ("data.xlsx", True),
        ("data.xls", True),
        ("data.json", True),
        ("data.pdf", False),
        ("data.txt", False),
        ("data.parquet", False),
        ("data", False),
        ("DATA.CSV", True),
        ("report.PDF", False),
    ])
    def test_file_format_validation(self, filename, expected):
        """Test various file format validations."""
        validate_file_format, _, _ = self._import_validators()
        assert validate_file_format(filename) == expected

    @pytest.mark.parametrize("size_mb,expected", [
        (0.1, True),
        (50, True),
        (99.9, True),
        (100, True),
        (100.1, False),
        (500, False),
    ])
    def test_file_size_validation(self, size_mb, expected):
        """Test file size limit enforcement."""
        _, validate_file_size, _ = self._import_validators()
        assert validate_file_size(size_mb) == expected

    def test_query_validation_valid(self):
        """Valid queries pass validation."""
        _, _, validate_query = self._import_validators()
        assert validate_query("What is the average revenue?") is True

    def test_query_validation_empty(self):
        """Empty queries fail validation."""
        _, _, validate_query = self._import_validators()
        assert validate_query("") is False
        assert validate_query("   ") is False

    def test_query_validation_too_long(self):
        """Queries exceeding max length fail validation."""
        _, _, validate_query = self._import_validators()
        long_query = "a" * 501
        assert validate_query(long_query) is False
