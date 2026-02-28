"""
Integration Tests — End-to-End.

Tests the complete user workflow: Upload → Query → Results → Download.
Requires valid AWS credentials and a configured Bedrock Agent.
"""

import uuid

import pytest

from streamlit_app.services.bedrock_client import BedrockAgentClient
from streamlit_app.services.s3_handler import S3Handler
from tests.fixtures.mock_responses import create_test_csv


@pytest.mark.integration
class TestEndToEnd:
    """Full pipeline: Upload → Query → Results → Artifact Download."""

    def test_complete_workflow(self):
        """Test the complete user workflow end-to-end."""
        s3 = S3Handler()
        bedrock = BedrockAgentClient()
        session_id = f"e2e-{uuid.uuid4().hex[:8]}"

        try:
            # Step 1: Upload dataset
            csv = create_test_csv(rows=200)
            uri = s3.upload_dataset(csv, session_id)
            assert uri.startswith("s3://")

            # Step 2: Get metadata
            metadata = s3.get_dataset_metadata(uri)
            assert metadata['rows'] > 0
            assert len(metadata['columns']) > 0
            assert metadata['size_mb'] > 0

            # Step 3: Execute analytical query
            result = bedrock.invoke_agent(
                "What are the top 5 products by total revenue?",
                session_id, uri
            )
            assert result['code'] != ''
            assert result['results'] != ''

            # Step 4: Download visualization (if any)
            if result['visualizations']:
                img = s3.download_artifact(result['visualizations'][0])
                assert len(img) > 0  # Non-empty image bytes

        finally:
            # Cleanup
            try:
                s3.delete_session_data(session_id)
            except Exception:
                pass

    def test_multi_query_workflow(self):
        """Test multiple sequential queries in one session."""
        s3 = S3Handler()
        bedrock = BedrockAgentClient()
        session_id = f"e2e-multi-{uuid.uuid4().hex[:8]}"

        try:
            csv = create_test_csv(rows=100)
            uri = s3.upload_dataset(csv, session_id)

            queries = [
                "What is the total revenue?",
                "Break it down by region",
                "Which product has the highest average revenue?"
            ]

            for query in queries:
                result = bedrock.invoke_agent(query, session_id, uri)
                assert result is not None
                assert result['explanation'] != '' or result['results'] != ''

        finally:
            try:
                s3.delete_session_data(session_id)
            except Exception:
                pass
