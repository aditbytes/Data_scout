"""
Unit Tests — BedrockAgentClient.

Tests the Bedrock Agent client wrapper with mocked AWS services.
Covers multiple response formats for model-agnostic parsing.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestBedrockAgentClient:
    """Unit tests for the Bedrock Agent client."""

    @pytest.fixture
    def client(self):
        """Create a BedrockAgentClient with mocked boto3."""
        with patch('streamlit_app.services.bedrock_client.boto3.client'):
            with patch('streamlit_app.services.bedrock_client.Config') as mock_config:
                mock_config.AWS_REGION = 'us-east-1'
                mock_config.BEDROCK_AGENT_ID = 'test-agent-id'
                mock_config.BEDROCK_AGENT_ALIAS_ID = 'test-alias-id'
                from streamlit_app.services.bedrock_client import BedrockAgentClient
                return BedrockAgentClient()

    def test_invoke_agent_success(self, client):
        """Verify successful agent invocation returns structured response."""
        mock_response = {
            'completion': [
                {'chunk': {'bytes': b'Here is the analysis...\n```python\nimport pandas\n```\nResults: done'}}
            ],
            'sessionId': 'test-session'
        }
        client.client.invoke_agent.return_value = mock_response

        result = client.invoke_agent("What is the average?", "session-1", "s3://bucket/data.csv")

        assert 'explanation' in result
        assert 'code' in result
        assert 'results' in result
        assert 'visualizations' in result
        client.client.invoke_agent.assert_called_once()

    def test_invoke_agent_with_dataset_context(self, client):
        """Verify dataset URI is passed in session attributes."""
        mock_response = {
            'completion': [{'chunk': {'bytes': b'Response text'}}],
            'sessionId': 'test'
        }
        client.client.invoke_agent.return_value = mock_response

        client.invoke_agent("query", "session", "s3://bucket/sales.csv")

        call_kwargs = client.client.invoke_agent.call_args[1]
        assert call_kwargs['sessionState']['sessionAttributes']['dataset_uri'] == \
            "s3://datascout-storage-use2/datasets/session/original/sales.csv"

    def test_parse_response_extracts_python_code(self, client):
        """Verify ```python code blocks are extracted from response."""
        text = 'Explanation\n```python\ndf.groupby("x").mean()\n```\nResults here'
        result = client._extract_components(text)

        assert 'groupby' in result['code']
        assert 'Explanation' in result['explanation']

    def test_parse_response_extracts_py_code(self, client):
        """Verify ```py code blocks are extracted (Nova Pro format)."""
        text = 'Analysis\n```py\ndf.describe()\n```\nDone'
        result = client._extract_components(text)

        assert 'describe' in result['code']
        assert 'Analysis' in result['explanation']

    def test_parse_response_extracts_bare_code(self, client):
        """Verify bare ``` code blocks are extracted (no language tag)."""
        text = 'Here is the code:\n```\nimport pandas as pd\ndf = pd.read_csv("data.csv")\n```\nFinished'
        result = client._extract_components(text)

        assert 'pandas' in result['code']
        assert 'Here is the code' in result['explanation']

    def test_parse_response_extracts_visualization_uris(self, client):
        """Verify S3 URIs for charts are extracted."""
        text = 'Chart saved to s3://bucket/artifacts/session/chart_001.png'
        result = client._extract_components(text)

        assert len(result['visualizations']) == 1
        assert 'chart_001.png' in result['visualizations'][0]

    def test_parse_response_handles_no_code(self, client):
        """Verify graceful handling when no code block exists."""
        text = 'I need more information to answer your question.'
        result = client._extract_components(text)

        assert result['code'] == ''
        assert 'more information' in result['explanation']

    def test_parse_response_fallback_raw_text(self, client):
        """Verify entire raw text is shown as explanation when no structure found."""
        text = 'The dataset contains 500 rows with sales data across 4 regions.'
        result = client._extract_components(text)

        assert result['explanation'] == text
        assert result['code'] == ''
        assert result['results'] == ''

    def test_invoke_agent_empty_query(self, client):
        """Verify empty query is handled without exception."""
        mock_response = {
            'completion': [{'chunk': {'bytes': b'Please provide a question.'}}],
            'sessionId': 'test'
        }
        client.client.invoke_agent.return_value = mock_response

        result = client.invoke_agent("", "session", "s3://bucket/data.csv")
        assert result is not None
        assert result['explanation'] != ''

    def test_parse_response_multiple_code_blocks(self, client):
        """Verify only the last code block is used."""
        text = '```python\nfirst_block()\n```\nMore text\n```python\nsecond_block()\n```\nEnd'
        result = client._extract_components(text)

        assert 'second_block' in result['code']
        assert 'first_block' not in result['code']

    def test_parse_response_multiple_visualizations(self, client):
        """Verify multiple visualization URIs are extracted."""
        text = 'Chart 1: s3://bucket/chart1.png\nChart 2: s3://bucket/chart2.png'
        result = client._extract_components(text)

        assert len(result['visualizations']) == 2

    def test_parse_response_empty_response(self, client):
        """Verify empty response returns a helpful message."""
        mock_response = {
            'completion': [{'chunk': {'bytes': b''}}],
            'sessionId': 'test'
        }
        result = client._parse_response(mock_response)

        assert 'empty response' in result['explanation'].lower()

    def test_parse_response_extracts_next_steps(self, client):
        """Verify next steps are extracted from bulleted lists."""
        text = (
            'Analysis complete.\n\n'
            'Next steps:\n'
            '- Investigate outliers in the revenue column\n'
            '- Create a pivot table by region\n'
            '- Visualize monthly trends\n'
        )
        result = client._extract_components(text)

        assert len(result['next_steps']) >= 2
        assert any('outlier' in s.lower() for s in result['next_steps'])

    def test_parse_response_jpg_visualization(self, client):
        """Verify JPG visualization URIs are also extracted."""
        text = 'Chart saved to s3://bucket/artifacts/chart.jpg'
        result = client._extract_components(text)

        assert len(result['visualizations']) == 1
        assert 'chart.jpg' in result['visualizations'][0]
