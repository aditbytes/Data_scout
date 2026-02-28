"""
Integration Tests — Upload Flow.

Tests the complete dataset upload pipeline against live AWS services.
Requires valid AWS credentials.
"""

import uuid

import pytest

from streamlit_app.services.s3_handler import S3Handler
from tests.fixtures.mock_responses import create_test_csv, create_test_json


@pytest.mark.integration
class TestUploadFlow:
    """Integration tests for dataset upload pipeline (requires live AWS)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with fresh S3Handler and session."""
        self.s3 = S3Handler()
        self.session_id = f"test-{uuid.uuid4().hex[:8]}"
        yield
        # Cleanup uploaded test data
        try:
            self.s3.delete_session_data(self.session_id)
        except Exception:
            pass

    def test_csv_upload_and_metadata(self):
        """Upload CSV and verify metadata extraction."""
        csv_file = create_test_csv(rows=100)
        uri = self.s3.upload_dataset(csv_file, self.session_id)

        assert uri.startswith("s3://")
        metadata = self.s3.get_dataset_metadata(uri)
        assert metadata['rows'] == 100
        assert len(metadata['columns']) > 0
        assert metadata['size_mb'] > 0

    def test_json_upload_and_metadata(self):
        """Upload JSON and verify metadata extraction."""
        json_file = create_test_json(records=30)
        uri = self.s3.upload_dataset(json_file, self.session_id)

        metadata = self.s3.get_dataset_metadata(uri)
        assert metadata['rows'] == 30

    def test_upload_creates_correct_s3_path(self):
        """Verify uploaded file is stored with session-scoped path."""
        csv_file = create_test_csv(rows=10)
        uri = self.s3.upload_dataset(csv_file, self.session_id)

        assert self.session_id in uri
        assert "datasets/" in uri
        assert "original/" in uri

    def test_metadata_preview_has_rows(self):
        """Verify metadata preview contains data rows."""
        csv_file = create_test_csv(rows=50)
        uri = self.s3.upload_dataset(csv_file, self.session_id)
        metadata = self.s3.get_dataset_metadata(uri)

        assert len(metadata['preview']) == 5  # head(5)
        assert len(metadata['columns']) > 0

    def test_metadata_null_counts(self):
        """Verify null counts are tracked correctly."""
        csv_file = create_test_csv(rows=50)
        uri = self.s3.upload_dataset(csv_file, self.session_id)
        metadata = self.s3.get_dataset_metadata(uri)

        assert 'null_counts' in metadata
        assert isinstance(metadata['null_counts'], dict)
