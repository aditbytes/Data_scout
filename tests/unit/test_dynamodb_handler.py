"""
Unit Tests — DynamoDBHandler.

Tests DynamoDB persistence for query history and session management
using mocked boto3 resources.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestDynamoDBHandler:
    """Unit tests for DynamoDB query and session persistence."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Config with DynamoDB settings."""
        config = MagicMock()
        config.AWS_REGION = 'us-east-1'
        config.DYNAMODB_TABLE = 'datascout-queries-test'
        config.ENABLE_DYNAMODB = True
        return config

    @pytest.fixture
    def handler(self, mock_config):
        """Create a DynamoDBHandler with mocked boto3."""
        with patch('streamlit_app.services.dynamodb_handler.Config', mock_config), \
             patch('streamlit_app.services.dynamodb_handler.boto3') as mock_boto3:
            mock_table = MagicMock()
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_boto3.resource.return_value = mock_resource

            from streamlit_app.services.dynamodb_handler import DynamoDBHandler
            ddb = DynamoDBHandler()
            ddb._mock_table = mock_table  # expose for assertions
            return ddb

    def test_save_query_success(self, handler):
        """save_query calls put_item with correct structure."""
        handler._mock_table.put_item.return_value = {}

        result = handler.save_query(
            session_id='test-session-123',
            query='What is the average revenue?',
            response={
                'explanation': 'I computed the average.',
                'code': 'df["revenue"].mean()',
                'results': '| Avg Revenue |\n| $5,234 |',
            },
            execution_time_ms=1500,
            success=True,
        )

        assert result is True
        handler._mock_table.put_item.assert_called_once()
        item = handler._mock_table.put_item.call_args[1]['Item']
        assert item['session_id'] == 'test-session-123'
        assert item['query'] == 'What is the average revenue?'
        assert item['record_type'] == 'QUERY'
        assert item['execution_time_ms'] == 1500
        assert item['success'] is True
        assert 'ttl' in item

    def test_save_query_returns_false_on_error(self, handler):
        """save_query returns False when DynamoDB throws an error."""
        import botocore.exceptions
        handler._mock_table.put_item.side_effect = \
            botocore.exceptions.ClientError(
                {'Error': {'Code': 'ConditionalCheckFailedException',
                           'Message': 'test'}},
                'PutItem',
            )

        result = handler.save_query(
            session_id='test-session',
            query='test query',
            response={},
            execution_time_ms=100,
        )

        assert result is False

    def test_get_query_history_success(self, handler):
        """get_query_history returns items from DynamoDB query."""
        handler._mock_table.query.return_value = {
            'Items': [
                {'session_id': 's1', 'timestamp': '2026-01-01T00:00:00',
                 'query': 'Q1', 'record_type': 'QUERY'},
                {'session_id': 's1', 'timestamp': '2026-01-01T00:01:00',
                 'query': 'Q2', 'record_type': 'QUERY'},
            ]
        }

        items = handler.get_query_history('s1')
        assert len(items) == 2
        assert items[0]['query'] == 'Q1'
        handler._mock_table.query.assert_called_once()

    def test_get_query_history_returns_empty_on_error(self, handler):
        """get_query_history returns [] when DynamoDB fails."""
        handler._mock_table.query.side_effect = Exception("Connection lost")
        items = handler.get_query_history('s1')
        assert items == []

    def test_save_session_success(self, handler):
        """save_session writes session metadata to DynamoDB."""
        handler._mock_table.put_item.return_value = {}

        result = handler.save_session(
            session_id='sess-abc',
            metadata={
                'dataset_loaded': True,
                'filename': 'sales.csv',
                'rows': 1000,
                'num_columns': 9,
            },
        )

        assert result is True
        item = handler._mock_table.put_item.call_args[1]['Item']
        assert item['session_id'] == 'sess-abc'
        assert item['record_type'] == 'SESSION'
        assert item['dataset_filename'] == 'sales.csv'
        assert item['dataset_rows'] == 1000

    def test_get_session_found(self, handler):
        """get_session returns session metadata when found."""
        handler._mock_table.query.return_value = {
            'Items': [
                {'session_id': 'sess-abc', 'record_type': 'SESSION',
                 'dataset_filename': 'data.csv'},
            ]
        }

        session = handler.get_session('sess-abc')
        assert session is not None
        assert session['dataset_filename'] == 'data.csv'

    def test_get_session_not_found(self, handler):
        """get_session returns None when no session exists."""
        handler._mock_table.query.return_value = {'Items': []}
        assert handler.get_session('nonexistent') is None

    def test_disabled_handler_returns_defaults(self, mock_config):
        """When ENABLE_DYNAMODB is False, all methods return gracefully."""
        mock_config.ENABLE_DYNAMODB = False

        with patch('streamlit_app.services.dynamodb_handler.Config', mock_config):
            from streamlit_app.services.dynamodb_handler import DynamoDBHandler
            ddb = DynamoDBHandler()

        assert ddb.save_query('s', 'q', {}, 100) is False
        assert ddb.get_query_history('s') == []
        assert ddb.save_session('s', {}) is False
        assert ddb.get_session('s') is None

    def test_truncates_long_response_fields(self, handler):
        """save_query truncates explanation/code/results to 4000 chars."""
        handler._mock_table.put_item.return_value = {}

        long_text = 'x' * 10000
        handler.save_query(
            session_id='s1',
            query='test',
            response={
                'explanation': long_text,
                'code': long_text,
                'results': long_text,
            },
            execution_time_ms=100,
        )

        item = handler._mock_table.put_item.call_args[1]['Item']
        assert len(item['explanation']) == 4000
        assert len(item['code']) == 4000
        assert len(item['results']) == 4000
