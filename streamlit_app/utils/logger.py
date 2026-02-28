"""
DataScout — Structured Logger.

Provides structured JSON logging for query execution and dataset upload
events without capturing any actual data values (privacy compliance).
"""

import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger('datascout')
logger.setLevel(logging.INFO)

# Add console handler if none exist
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    )
    logger.addHandler(handler)


def log_query_execution(session_id: str, query: str,
                        execution_time_ms: int, success: bool,
                        error: Optional[Exception] = None) -> None:
    """Log query execution event without capturing data values.

    Args:
        session_id: Unique session identifier.
        query: The user's query string (only length is logged).
        execution_time_ms: Query execution time in milliseconds.
        success: Whether the query completed successfully.
        error: Optional exception if the query failed.
    """
    logger.info(json.dumps({
        'event': 'query_executed',
        'session_id': session_id,
        'query_length': len(query),
        'execution_time_ms': execution_time_ms,
        'success': success,
        'error_type': type(error).__name__ if error else None,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }))


def log_dataset_upload(session_id: str, filename: str,
                       rows: int, columns: int, size_mb: float) -> None:
    """Log dataset upload event with hashed filename for privacy.

    Args:
        session_id: Unique session identifier.
        filename: Original filename (hashed before logging).
        rows: Number of rows in the dataset.
        columns: Number of columns in the dataset.
        size_mb: File size in megabytes.
    """
    logger.info(json.dumps({
        'event': 'dataset_uploaded',
        'session_id': session_id,
        'filename_hash': hashlib.sha256(filename.encode()).hexdigest()[:12],
        'row_count': rows,
        'column_count': columns,
        'size_mb': size_mb,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }))


def log_session_event(session_id: str, event_type: str,
                      details: Optional[dict] = None) -> None:
    """Log a generic session lifecycle event.

    Args:
        session_id: Unique session identifier.
        event_type: Type of event (e.g., 'session_created', 'session_expired').
        details: Optional additional context.
    """
    log_entry = {
        'event': event_type,
        'session_id': session_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    if details:
        log_entry['details'] = details
    logger.info(json.dumps(log_entry))
