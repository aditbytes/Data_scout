"""
Unit Tests — Lambda Handler.

Tests the DataScout REST API Lambda function routes including
health check, analyze, and history endpoints.
"""

import json

import pytest
from unittest.mock import patch, MagicMock


class TestLambdaHandler:
    """Unit tests for the Lambda API handler."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Set environment variables for the Lambda handler."""
        monkeypatch.setenv('AWS_REGION', 'us-east-1')
        monkeypatch.setenv('BEDROCK_AGENT_ID', 'TEST_AGENT_ID')
        monkeypatch.setenv('BEDROCK_AGENT_ALIAS_ID', 'TEST_ALIAS_ID')
        monkeypatch.setenv('DYNAMODB_TABLE', 'datascout-queries-test')
        monkeypatch.setenv('S3_BUCKET', 'datascout-test')

    @pytest.fixture
    def handler_module(self):
        """Import the Lambda handler with mocked AWS clients."""
        with patch('boto3.client') as mock_client, \
             patch('boto3.resource') as mock_resource:
            mock_table = MagicMock()
            mock_resource.return_value.Table.return_value = mock_table

            # Force reimport to pick up patched boto3
            import importlib
            import lambda_function.handler as handler_mod
            importlib.reload(handler_mod)

            handler_mod._mock_table = mock_table
            handler_mod._mock_bedrock = mock_client.return_value
            return handler_mod

    def test_health_endpoint(self, handler_module):
        """GET /health returns 200 with service info."""
        event = {'httpMethod': 'GET', 'path': '/health'}
        result = handler_module.lambda_handler(event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['status'] == 'ok'
        assert body['service'] == 'datascout-api'

    def test_health_has_cors_headers(self, handler_module):
        """Health response includes CORS headers."""
        event = {'httpMethod': 'GET', 'path': '/health'}
        result = handler_module.lambda_handler(event, None)

        assert result['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Content-Type' in result['headers']

    def test_analyze_missing_query_returns_400(self, handler_module):
        """POST /analyze with empty body returns 400."""
        event = {
            'httpMethod': 'POST',
            'path': '/analyze',
            'body': json.dumps({}),
        }
        result = handler_module.lambda_handler(event, None)

        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'Missing required field' in body['error']

    def test_analyze_success(self, handler_module):
        """POST /analyze invokes Bedrock and returns response."""
        # Mock Bedrock response
        handler_module._mock_bedrock.invoke_agent.return_value = {
            'completion': [
                {'chunk': {'bytes': b'The average revenue is $5,234.'}},
            ]
        }
        handler_module._mock_table.put_item.return_value = {}

        event = {
            'httpMethod': 'POST',
            'path': '/analyze',
            'body': json.dumps({
                'query': 'What is the average revenue?',
                'session_id': 'test-session',
                'dataset_uri': 's3://bucket/data.csv',
            }),
        }
        result = handler_module.lambda_handler(event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'response' in body
        assert body['query'] == 'What is the average revenue?'
        assert body['session_id'] == 'test-session'

    def test_history_endpoint(self, handler_module):
        """GET /history/{session_id} returns query history."""
        handler_module._mock_table.query.return_value = {
            'Items': [
                {'session_id': 's1', 'timestamp': '2026-01-01',
                 'query': 'Test Q', 'record_type': 'QUERY',
                 'execution_time_ms': 1500},
            ]
        }

        event = {'httpMethod': 'GET', 'path': '/history/s1'}
        result = handler_module.lambda_handler(event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['session_id'] == 's1'
        assert body['count'] == 1

    def test_not_found_route(self, handler_module):
        """Unknown routes return 404."""
        event = {'httpMethod': 'GET', 'path': '/unknown'}
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 404

    def test_analyze_without_agent_returns_503(self, handler_module):
        """POST /analyze returns 503 when agent is not configured."""
        # Temporarily clear the agent ID
        original = handler_module.BEDROCK_AGENT_ID
        handler_module.BEDROCK_AGENT_ID = ''

        event = {
            'httpMethod': 'POST',
            'path': '/analyze',
            'body': json.dumps({'query': 'test'}),
        }
        result = handler_module.lambda_handler(event, None)
        assert result['statusCode'] == 503

        handler_module.BEDROCK_AGENT_ID = original
