"""
Unit Tests — S3Handler.

Tests S3 operations with mocked boto3 services.
"""

import io

import pytest
from unittest.mock import patch, MagicMock


class TestS3Handler:
    """Unit tests for S3 operations."""

    @pytest.fixture
    def handler(self):
        """Create an S3Handler with mocked boto3."""
        with patch('streamlit_app.services.s3_handler.boto3.client'):
            with patch('streamlit_app.services.s3_handler.Config') as mock_config:
                mock_config.AWS_REGION = 'us-east-1'
                mock_config.S3_BUCKET = 'test-bucket'
                mock_config.MAX_FILE_SIZE_MB = 100
                mock_config.SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls', '.json'}
                from streamlit_app.services.s3_handler import S3Handler
                return S3Handler()

    @pytest.fixture
    def valid_csv(self):
        content = "name,value\nAlice,100\nBob,200\n"
        file_obj = io.BytesIO(content.encode())
        file_obj.name = "test_data.csv"
        return file_obj

    @pytest.fixture
    def valid_json(self):
        content = '[{"name": "Alice", "value": 100}]'
        file_obj = io.BytesIO(content.encode())
        file_obj.name = "test_data.json"
        return file_obj

    # === Upload Tests ===

    def test_upload_csv_success(self, handler, valid_csv):
        """CSV upload returns correct S3 URI."""
        uri = handler.upload_dataset(valid_csv, "session-123")
        assert uri.startswith("s3://")
        assert "session-123" in uri
        assert "test_data.csv" in uri

    def test_upload_with_encryption(self, handler, valid_csv):
        """Upload includes server-side encryption."""
        handler.upload_dataset(valid_csv, "session-123")
        call_args = handler.s3.upload_fileobj.call_args
        assert call_args[1]['ExtraArgs']['ServerSideEncryption'] == 'AES256'

    # === Validation Tests ===

    def test_reject_unsupported_format(self, handler):
        """Unsupported file format raises ValueError."""
        file_obj = io.BytesIO(b"content")
        file_obj.name = "report.pdf"
        with pytest.raises(ValueError, match="Unsupported format"):
            handler._validate_file(file_obj)

    def test_reject_oversized_file(self, handler):
        """File exceeding size limit raises ValueError."""
        large_content = b"x" * (101 * 1024 * 1024)
        file_obj = io.BytesIO(large_content)
        file_obj.name = "huge_file.csv"
        with pytest.raises(ValueError, match="too large"):
            handler._validate_file(file_obj)

    def test_accept_max_size_file(self, handler):
        """File under max size is accepted."""
        content = b"x" * (99 * 1024 * 1024)
        file_obj = io.BytesIO(content)
        file_obj.name = "big_file.csv"
        handler._validate_file(file_obj)  # Should not raise

    def test_accept_all_supported_formats(self, handler):
        """All supported formats pass validation."""
        for fmt in ['.csv', '.xlsx', '.xls', '.json']:
            file_obj = io.BytesIO(b"content")
            file_obj.name = f"test{fmt}"
            handler._validate_file(file_obj)  # Should not raise

    # === Metadata Tests ===

    def test_metadata_extraction_csv(self, handler):
        """CSV metadata includes correct shape and columns."""
        csv_content = b"name,value\nAlice,100\nBob,200\n"
        mock_body = MagicMock()
        mock_body.read.return_value = csv_content
        handler.s3.get_object.return_value = {'Body': mock_body}

        metadata = handler.get_dataset_metadata("s3://bucket/datasets/session/original/test.csv")

        assert metadata['filename'] == 'test.csv'
        assert 'name' in metadata['columns']
        assert 'value' in metadata['columns']
        assert metadata['rows'] == 2

    # === URI Parsing Tests ===

    def test_parse_s3_uri(self, handler):
        """S3 URI is correctly parsed into bucket and key."""
        bucket, key = handler._parse_uri("s3://my-bucket/path/to/file.csv")
        assert bucket == "my-bucket"
        assert key == "path/to/file.csv"

    def test_parse_s3_uri_nested_path(self, handler):
        """S3 URI with deeply nested path is parsed correctly."""
        bucket, key = handler._parse_uri("s3://bucket/a/b/c/d/file.json")
        assert bucket == "bucket"
        assert key == "a/b/c/d/file.json"
