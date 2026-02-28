"""
Integration Tests — Query Flow.

Tests the full query execution pipeline against live AWS Bedrock.
Requires valid AWS credentials and a configured Bedrock Agent.
"""

import uuid

import pytest

from streamlit_app.services.bedrock_client import BedrockAgentClient
from streamlit_app.services.s3_handler import S3Handler
from tests.fixtures.mock_responses import create_test_csv


@pytest.mark.integration
class TestQueryFlow:
    """Integration tests for full query execution (requires live AWS)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with Bedrock client and test dataset."""
        self.bedrock = BedrockAgentClient()
        self.s3 = S3Handler()
        self.session_id = f"test-{uuid.uuid4().hex[:8]}"

        # Upload test dataset
        csv = create_test_csv(rows=100)
        self.dataset_uri = self.s3.upload_dataset(csv, self.session_id)
        yield
        try:
            self.s3.delete_session_data(self.session_id)
        except Exception:
            pass

    def test_simple_aggregation(self):
        """Test simple average query returns code and results."""
        result = self.bedrock.invoke_agent(
            "What is the average revenue?",
            self.session_id,
            self.dataset_uri
        )
        assert result['code'] is not None
        assert result['results'] is not None

    def test_groupby_query(self):
        """Test group-by aggregation query includes groupby logic."""
        result = self.bedrock.invoke_agent(
            "What is the average revenue by region?",
            self.session_id,
            self.dataset_uri
        )
        assert 'groupby' in result['code'].lower() or 'group' in result['code'].lower()

    def test_visualization_generation(self):
        """Test that chart-related code is generated when requested."""
        result = self.bedrock.invoke_agent(
            "Show me a bar chart of revenue by region",
            self.session_id,
            self.dataset_uri
        )
        assert len(result['visualizations']) > 0 or 'plt' in result['code']

    def test_follow_up_query(self):
        """Test context retention for follow-up queries."""
        # First query
        self.bedrock.invoke_agent(
            "What are the top 5 products by revenue?",
            self.session_id,
            self.dataset_uri
        )
        # Follow-up using session context
        result = self.bedrock.invoke_agent(
            "Now show me their monthly trends",
            self.session_id,
            self.dataset_uri
        )
        assert result['code'] is not None
