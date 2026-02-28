"""
DataScout — AWS Lambda Handler.

Provides a REST API layer for DataScout via API Gateway + Lambda.
Routes:
  POST /analyze           — invoke Bedrock agent with a query
  GET  /health            — service health check
  GET  /history/{session}  — retrieve query history from DynamoDB
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3
import botocore.config

logger = logging.getLogger('datascout.lambda')
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# ── Environment Variables ─────────────────────────────────────────────────────
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID', '')
BEDROCK_AGENT_ALIAS_ID = os.getenv('BEDROCK_AGENT_ALIAS_ID', '')
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'datascout-queries')
S3_BUCKET = os.getenv('S3_BUCKET', 'datascout-storage')

# ── Clients (initialized once, reused across warm invocations) ────────────────
bedrock_config = botocore.config.Config(
    region_name=AWS_REGION,
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    read_timeout=60,
)
bedrock_client = boto3.client('bedrock-agent-runtime', config=bedrock_config)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)


# ═════════════════════════════════════════════════════════════════════════════
# Lambda Entry Point
# ═════════════════════════════════════════════════════════════════════════════

def lambda_handler(event, context):
    """Route API Gateway requests to the appropriate handler.

    Supports REST API (v1) and HTTP API (v2) event formats.

    Args:
        event: API Gateway proxy event.
        context: Lambda context object.

    Returns:
        API Gateway-compatible response dict.
    """
    # Determine HTTP method and path from the event
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path = event.get('path') or event.get('rawPath', '/')

    logger.info("Received %s %s", http_method, path)

    try:
        if path == '/health' and http_method == 'GET':
            return _handle_health()

        if path == '/analyze' and http_method == 'POST':
            return _handle_analyze(event)

        if path.startswith('/history/') and http_method == 'GET':
            session_id = path.split('/history/')[-1]
            return _handle_history(session_id)

        return _response(404, {'error': 'Not found', 'path': path})

    except Exception as exc:
        logger.exception("Unhandled error")
        return _response(500, {'error': str(exc)})


# ═════════════════════════════════════════════════════════════════════════════
# Route Handlers
# ═════════════════════════════════════════════════════════════════════════════

def _handle_health():
    """Return service health status."""
    return _response(200, {
        'status': 'ok',
        'service': 'datascout-api',
        'region': AWS_REGION,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


def _handle_analyze(event):
    """Invoke the Bedrock Agent with the user's query.

    Expected body:
        {
            "query": "What are the top 5 products by revenue?",
            "session_id": "optional-uuid",
            "dataset_uri": "s3://bucket/path/to/file.csv"
        }
    """
    body = json.loads(event.get('body') or '{}')

    query = body.get('query', '').strip()
    if not query:
        return _response(400, {'error': 'Missing required field: query'})

    session_id = body.get('session_id') or str(uuid.uuid4())
    dataset_uri = body.get('dataset_uri', '')

    if not BEDROCK_AGENT_ID:
        return _response(503, {'error': 'Bedrock agent not configured'})

    # Build session state
    session_state = {
        'sessionAttributes': {'dataset_format': 'csv'}
    }
    if dataset_uri:
        session_state['sessionAttributes']['dataset_uri'] = dataset_uri
        session_state['files'] = [{
            'name': dataset_uri.split('/')[-1],
            'source': {
                'sourceType': 'S3',
                's3Location': {'uri': dataset_uri},
            },
            'useCase': 'CODE_INTERPRETER',
        }]

    enhanced_query = (
        f"{query}\n\n"
        "Please include in your response: "
        "a brief explanation of your approach and key insights, "
        "the Python code you used, "
        "results displayed as a markdown table, "
        "and generate a chart to visualize the results."
    )

    start_time = datetime.now(timezone.utc)

    response = bedrock_client.invoke_agent(
        agentId=BEDROCK_AGENT_ID,
        agentAliasId=BEDROCK_AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=enhanced_query,
        enableTrace=False,
        sessionState=session_state,
    )

    # Collect streaming response
    chunks = []
    for event_item in response.get('completion', []):
        if 'chunk' in event_item:
            chunk_bytes = event_item['chunk'].get('bytes', b'')
            chunks.append(chunk_bytes.decode('utf-8'))

    full_text = ''.join(chunks)
    execution_time_ms = int(
        (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    )

    result = {
        'session_id': session_id,
        'query': query,
        'response': full_text,
        'execution_time_ms': execution_time_ms,
    }

    # Persist to DynamoDB
    try:
        table.put_item(Item={
            'session_id': session_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'record_type': 'QUERY',
            'query': query,
            'response_text': full_text[:4000],
            'execution_time_ms': execution_time_ms,
            'success': True,
            'ttl': int(datetime.now(timezone.utc).timestamp()) + 7 * 86400,
        })
    except Exception as exc:
        logger.warning("DynamoDB write failed: %s", exc)

    return _response(200, result)


def _handle_history(session_id):
    """Retrieve query history for a session from DynamoDB."""
    if not session_id:
        return _response(400, {'error': 'Missing session_id'})

    try:
        from boto3.dynamodb.conditions import Key

        resp = table.query(
            KeyConditionExpression=Key('session_id').eq(session_id),
            FilterExpression='record_type = :rt',
            ExpressionAttributeValues={':rt': 'QUERY'},
            ScanIndexForward=False,
            Limit=50,
        )
        items = resp.get('Items', [])

        # Convert Decimal values to int/float for JSON serialization
        serializable_items = []
        for item in items:
            clean = {}
            for k, v in item.items():
                if hasattr(v, 'as_integer_ratio'):
                    clean[k] = int(v) if v == int(v) else float(v)
                else:
                    clean[k] = v
            serializable_items.append(clean)

        return _response(200, {
            'session_id': session_id,
            'count': len(serializable_items),
            'queries': serializable_items,
        })
    except Exception as exc:
        logger.warning("DynamoDB query failed: %s", exc)
        return _response(500, {'error': f'Failed to retrieve history: {exc}'})


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def _response(status_code: int, body: dict) -> dict:
    """Build an API Gateway-compatible response.

    Args:
        status_code: HTTP status code.
        body: Response body dict (will be JSON-serialized).

    Returns:
        API Gateway proxy response dict with CORS headers.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        },
        'body': json.dumps(body, default=str),
    }
