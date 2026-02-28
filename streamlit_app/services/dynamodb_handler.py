"""
DataScout — Amazon DynamoDB Handler.

Persists query history and session metadata to DynamoDB for durable
storage across sessions and restarts.  Falls back gracefully when
DynamoDB is unavailable so the app continues to work in offline/local mode.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

import boto3
import botocore.exceptions

from config import Config

logger = logging.getLogger('datascout.dynamodb')


class DynamoDBHandler:
    """Amazon DynamoDB handler for query and session persistence.

    Stores query logs and session metadata in a single DynamoDB table
    using ``session_id`` as partition key and ``timestamp`` as sort key.
    """

    def __init__(self):
        """Initialize the DynamoDB resource and table reference."""
        self._enabled = getattr(Config, 'ENABLE_DYNAMODB', True)
        if not self._enabled:
            logger.info("DynamoDB persistence is disabled via config")
            return

        try:
            self._resource = boto3.resource(
                'dynamodb', region_name=Config.AWS_REGION
            )
            table_name = getattr(Config, 'DYNAMODB_TABLE', 'datascout-queries')
            self._table = self._resource.Table(table_name)
            logger.info("DynamoDB handler initialized — table: %s", table_name)
        except Exception as exc:
            logger.warning("Failed to initialize DynamoDB: %s", exc)
            self._enabled = False

    # ── Query Persistence ────────────────────────────────────────────────────

    def save_query(
        self,
        session_id: str,
        query: str,
        response: Dict,
        execution_time_ms: int,
        success: bool = True,
    ) -> bool:
        """Persist a query exchange to DynamoDB.

        Args:
            session_id: The session that owns this query.
            query: The user's natural-language question.
            response: Structured response dict from the Bedrock agent.
            execution_time_ms: Round-trip time in milliseconds.
            success: Whether the query completed successfully.

        Returns:
            True if the item was written, False on failure.
        """
        if not self._enabled:
            return False

        try:
            now = datetime.now(timezone.utc).isoformat()
            # DynamoDB cannot store float — convert to Decimal
            item = {
                'session_id': session_id,
                'timestamp': now,
                'record_type': 'QUERY',
                'query': query,
                'explanation': response.get('explanation', '')[:4000],
                'code': response.get('code', '')[:4000],
                'results': response.get('results', '')[:4000],
                'execution_time_ms': execution_time_ms,
                'success': success,
                'ttl': int(
                    (datetime.now(timezone.utc)).timestamp()
                ) + 7 * 86400,  # expire after 7 days
            }
            self._table.put_item(Item=item)
            logger.info(
                "Saved query to DynamoDB: session=%s, time=%dms",
                session_id, execution_time_ms,
            )
            return True
        except botocore.exceptions.ClientError as exc:
            logger.warning("DynamoDB put_item failed: %s", exc)
            return False
        except Exception as exc:
            logger.warning("Unexpected DynamoDB error: %s", exc)
            return False

    def get_query_history(
        self, session_id: str, limit: int = 50
    ) -> List[Dict]:
        """Retrieve query history for a session, newest first.

        Args:
            session_id: The session to query.
            limit: Maximum number of items to return.

        Returns:
            List of query dicts ordered by timestamp descending.
        """
        if not self._enabled:
            return []

        try:
            from boto3.dynamodb.conditions import Key

            resp = self._table.query(
                KeyConditionExpression=Key('session_id').eq(session_id),
                FilterExpression='record_type = :rt',
                ExpressionAttributeValues={':rt': 'QUERY'},
                ScanIndexForward=False,
                Limit=limit,
            )
            return resp.get('Items', [])
        except Exception as exc:
            logger.warning("DynamoDB query failed: %s", exc)
            return []

    # ── Session Persistence ──────────────────────────────────────────────────

    def save_session(self, session_id: str, metadata: Dict) -> bool:
        """Persist session metadata to DynamoDB.

        Args:
            session_id: Unique session identifier.
            metadata: Session metadata dict (dataset info, created_at, etc.)

        Returns:
            True if successful, False otherwise.
        """
        if not self._enabled:
            return False

        try:
            now = datetime.now(timezone.utc).isoformat()
            item = {
                'session_id': session_id,
                'timestamp': f"SESSION#{now}",
                'record_type': 'SESSION',
                'created_at': now,
                'dataset_loaded': metadata.get('dataset_loaded', False),
                'dataset_filename': metadata.get('filename', ''),
                'dataset_rows': metadata.get('rows', 0),
                'dataset_columns': metadata.get('num_columns', 0),
                'ttl': int(
                    datetime.now(timezone.utc).timestamp()
                ) + 7 * 86400,
            }
            self._table.put_item(Item=item)
            logger.info("Saved session to DynamoDB: %s", session_id)
            return True
        except Exception as exc:
            logger.warning("DynamoDB save_session failed: %s", exc)
            return False

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session metadata from DynamoDB.

        Args:
            session_id: The session to look up.

        Returns:
            Session metadata dict, or None if not found.
        """
        if not self._enabled:
            return None

        try:
            from boto3.dynamodb.conditions import Key

            resp = self._table.query(
                KeyConditionExpression=(
                    Key('session_id').eq(session_id)
                    & Key('timestamp').begins_with('SESSION#')
                ),
                Limit=1,
            )
            items = resp.get('Items', [])
            return items[0] if items else None
        except Exception as exc:
            logger.warning("DynamoDB get_session failed: %s", exc)
            return None
