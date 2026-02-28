# DataScout — API Integration Guide

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Overview

DataScout integrates with multiple AWS services to deliver its autonomous data analysis capabilities. This document details every API integration point, request/response formats, authentication mechanisms, and error handling strategies.

### 1.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                       │
│                        (AWS App Runner)                         │
└──────┬──────────────────┬──────────────────┬────────────────────┘
       │                  │                  │
       │ boto3            │ boto3            │ boto3
       ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐
│  Amazon S3   │  │   Amazon     │  │   Amazon CloudWatch      │
│  (Storage)   │  │   Bedrock    │  │   (Logging & Monitoring)  │
│              │  │   Agent      │  │                           │
│  - Upload    │  │   Runtime    │  │  - Query logs             │
│  - Download  │  │              │  │  - Error tracking         │
│  - Metadata  │  │  - Invoke    │  │  - Performance metrics    │
└──────────────┘  │  - Sessions  │  └──────────────────────────┘
                  │  - Code Exec │
                  └──────────────┘
```

---

## 2. Amazon Bedrock Agent API

### 2.1 Agent Configuration

```yaml
Service: Amazon Bedrock Agents
Region: us-east-1
Agent Name: DataScout-Analyst
Foundation Model: anthropic.claude-3-5-sonnet-20241022-v2:0
Agent ID: Stored in environment variable BEDROCK_AGENT_ID
Agent Alias ID: Stored in environment variable BEDROCK_AGENT_ALIAS_ID
Idle Session TTL: 600 seconds
```

### 2.2 Agent Invocation API

#### Endpoint
```
POST bedrock-agent-runtime.{region}.amazonaws.com
Action: InvokeAgent
```

#### Request Format
```python
import boto3

client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

response = client.invoke_agent(
    agentId='AGENT_ID',                    # Required: Agent identifier
    agentAliasId='AGENT_ALIAS_ID',         # Required: Agent alias
    sessionId='unique-session-id',          # Required: Session identifier
    inputText='What is the average revenue by region?',  # Required: User query
    enableTrace=True,                       # Optional: Enable execution trace
    sessionState={                          # Optional: Session context
        'sessionAttributes': {
            'dataset_uri': 's3://datascout-storage/datasets/abc123/original/sales.csv',
            'dataset_format': 'csv',
            'dataset_columns': 'date,region,product,revenue,quantity',
            'dataset_rows': '1234'
        }
    }
)
```

#### Response Format (Streaming)
```python
# Response is a streaming EventStream
{
    'completion': EventStream([
        {
            'chunk': {
                'bytes': b'Analysis text and results...',
                'attribution': {
                    'citations': [...]
                }
            }
        },
        {
            'trace': {               # Only when enableTrace=True
                'agentId': 'string',
                'sessionId': 'string',
                'trace': {
                    'orchestrationTrace': {
                        'modelInvocationInput': {...},
                        'rationale': {...},
                        'invocationInput': {...},
                        'observation': {...}
                    }
                }
            }
        }
    ]),
    'contentType': 'application/json',
    'sessionId': 'unique-session-id'
}
```

#### Response Parsing Logic
```python
class BedrockAgentClient:
    """Wrapper for Amazon Bedrock Agent Runtime API."""

    def __init__(self, region='us-east-1'):
        self.client = boto3.client('bedrock-agent-runtime', region_name=region)
        self.agent_id = os.environ['BEDROCK_AGENT_ID']
        self.agent_alias_id = os.environ['BEDROCK_AGENT_ALIAS_ID']

    def invoke_agent(self, query: str, session_id: str, dataset_uri: str) -> dict:
        """
        Invoke the Bedrock Agent with a user query.

        Args:
            query: Natural language analytical question
            session_id: Unique session identifier for conversation continuity
            dataset_uri: S3 URI of the uploaded dataset

        Returns:
            dict with keys: explanation, code, results, visualizations, next_steps
        """
        try:
            response = self.client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=query,
                enableTrace=True,
                sessionState={
                    'sessionAttributes': {
                        'dataset_uri': dataset_uri,
                        'dataset_format': 'csv'
                    }
                }
            )
            return self._parse_response(response)

        except self.client.exceptions.ThrottlingException:
            raise RateLimitError("Bedrock API rate limit exceeded. Please retry.")
        except self.client.exceptions.ValidationException as e:
            raise QueryValidationError(f"Invalid query format: {e}")
        except Exception as e:
            raise AgentInvocationError(f"Agent invocation failed: {e}")

    def _parse_response(self, response: dict) -> dict:
        """Parse streaming response into structured components."""
        chunks = []
        traces = []

        for event in response['completion']:
            if 'chunk' in event:
                chunks.append(event['chunk']['bytes'].decode('utf-8'))
            if 'trace' in event:
                traces.append(event['trace'])

        full_response = ''.join(chunks)
        return self._extract_components(full_response, traces)

    def _extract_components(self, text: str, traces: list) -> dict:
        """Extract structured components from agent response."""
        components = {
            'explanation': '',
            'code': '',
            'results': '',
            'visualizations': [],
            'next_steps': [],
            'execution_trace': traces
        }

        # Extract code blocks (```python ... ```)
        import re
        code_blocks = re.findall(r'```python\n(.*?)```', text, re.DOTALL)
        if code_blocks:
            components['code'] = code_blocks[-1].strip()

        # Extract S3 URIs for visualizations
        s3_uris = re.findall(r's3://[^\s\)]+\.png', text)
        components['visualizations'] = s3_uris

        # Extract explanation (text before first code block)
        parts = text.split('```python')
        if parts:
            components['explanation'] = parts[0].strip()

        # Extract results (text after last code block)
        last_block_end = text.rfind('```')
        if last_block_end != -1:
            components['results'] = text[last_block_end + 3:].strip()

        return components
```

### 2.3 Session Management

```python
class SessionManager:
    """Manage user sessions for Bedrock Agent interactions."""

    SESSION_TIMEOUT = 600  # 10 minutes (matches Bedrock Agent TTL)

    def __init__(self):
        self.sessions = {}

    def create_session(self) -> str:
        """Create a new unique session ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'query_count': 0,
            'dataset_uri': None
        }
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Check if session is still valid (not expired)."""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        elapsed = (datetime.utcnow() - session['last_activity']).total_seconds()
        return elapsed < self.SESSION_TIMEOUT

    def update_session(self, session_id: str, dataset_uri: str = None):
        """Update session activity timestamp and optional dataset."""
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = datetime.utcnow()
            self.sessions[session_id]['query_count'] += 1
            if dataset_uri:
                self.sessions[session_id]['dataset_uri'] = dataset_uri
```

---

## 3. Amazon S3 API

### 3.1 Bucket Configuration

```yaml
Bucket Name: datascout-storage
Region: us-east-1
Versioning: Enabled
Encryption: AES-256 (SSE-S3)
Lifecycle:
  - datasets/*: Delete after 7 days
  - artifacts/*: Delete after 7 days
  - logs/*: Transition to Glacier after 7 days, delete after 90 days
```

### 3.2 S3 Operations

#### Upload Dataset
```python
class S3Handler:
    """Handle all S3 operations for DataScout."""

    BUCKET_NAME = os.environ.get('S3_BUCKET', 'datascout-storage')
    MAX_FILE_SIZE_MB = 100
    SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls', '.json'}

    def __init__(self):
        self.s3 = boto3.client('s3')

    def upload_dataset(self, file_obj, session_id: str) -> str:
        """
        Upload user dataset to S3.

        Args:
            file_obj: Streamlit UploadedFile object
            session_id: Current user session ID

        Returns:
            S3 URI of uploaded file (s3://bucket/key)

        Raises:
            DataUploadError: If file validation fails
        """
        # Validate file
        self._validate_file(file_obj)

        # Construct S3 key
        key = f"datasets/{session_id}/original/{file_obj.name}"

        # Upload with server-side encryption
        self.s3.upload_fileobj(
            file_obj,
            self.BUCKET_NAME,
            key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',
                'ContentType': self._get_content_type(file_obj.name),
                'Metadata': {
                    'session-id': session_id,
                    'upload-timestamp': datetime.utcnow().isoformat()
                }
            }
        )

        return f"s3://{self.BUCKET_NAME}/{key}"

    def _validate_file(self, file_obj):
        """Validate file format and size before upload."""
        # Check file extension
        ext = Path(file_obj.name).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise DataUploadError(
                f"Unsupported format: {ext}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Check file size
        file_obj.seek(0, 2)  # Seek to end
        size_mb = file_obj.tell() / (1024 * 1024)
        file_obj.seek(0)     # Reset to beginning

        if size_mb > self.MAX_FILE_SIZE_MB:
            raise DataUploadError(
                f"File size ({size_mb:.1f}MB) exceeds limit ({self.MAX_FILE_SIZE_MB}MB)"
            )
```

#### Get Dataset Metadata
```python
    def get_dataset_metadata(self, s3_uri: str) -> dict:
        """
        Extract metadata from uploaded dataset without downloading fully.

        Args:
            s3_uri: S3 URI of the dataset

        Returns:
            dict with keys: filename, rows, columns, dtypes, size_mb, preview
        """
        bucket, key = self._parse_s3_uri(s3_uri)

        # Get object metadata
        head = self.s3.head_object(Bucket=bucket, Key=key)
        size_mb = head['ContentLength'] / (1024 * 1024)

        # Download and parse
        response = self.s3.get_object(Bucket=bucket, Key=key)
        body = response['Body'].read()

        filename = key.split('/')[-1]
        ext = Path(filename).suffix.lower()

        if ext == '.csv':
            df = pd.read_csv(io.BytesIO(body), nrows=1000)
        elif ext in ('.xlsx', '.xls'):
            df = pd.read_excel(io.BytesIO(body), nrows=1000)
        elif ext == '.json':
            df = pd.read_json(io.BytesIO(body))
        else:
            raise DataUploadError(f"Cannot parse format: {ext}")

        return {
            'filename': filename,
            'rows': len(df),
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'size_mb': round(size_mb, 2),
            'preview': df.head(5).to_dict(orient='records'),
            'null_counts': df.isnull().sum().to_dict()
        }
```

#### Download Artifact
```python
    def download_artifact(self, s3_uri: str) -> bytes:
        """
        Download a generated artifact (chart, report) from S3.

        Args:
            s3_uri: S3 URI of the artifact

        Returns:
            Raw bytes of the artifact file
        """
        bucket, key = self._parse_s3_uri(s3_uri)

        response = self.s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    def list_artifacts(self, session_id: str) -> list:
        """List all artifacts generated in a session."""
        prefix = f"artifacts/{session_id}/"

        response = self.s3.list_objects_v2(
            Bucket=self.BUCKET_NAME,
            Prefix=prefix
        )

        artifacts = []
        for obj in response.get('Contents', []):
            artifacts.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
                'uri': f"s3://{self.BUCKET_NAME}/{obj['Key']}"
            })

        return artifacts

    @staticmethod
    def _parse_s3_uri(uri: str) -> tuple:
        """Parse S3 URI into bucket and key components."""
        parts = uri.replace('s3://', '').split('/', 1)
        return parts[0], parts[1]

    @staticmethod
    def _get_content_type(filename: str) -> str:
        """Determine MIME type from filename."""
        types = {
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.json': 'application/json',
            '.png': 'image/png',
            '.pdf': 'application/pdf'
        }
        ext = Path(filename).suffix.lower()
        return types.get(ext, 'application/octet-stream')
```

### 3.3 IAM Policy for S3 Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSessionScopedAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:HeadObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::datascout-storage",
        "arn:aws:s3:::datascout-storage/*"
      ]
    },
    {
      "Sid": "DenyPublicAccess",
      "Effect": "Deny",
      "Action": "s3:PutBucketPolicy",
      "Resource": "arn:aws:s3:::datascout-storage",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "public-read"
        }
      }
    }
  ]
}
```

---

## 4. Amazon CloudWatch API

### 4.1 Logging Configuration

```python
import logging
import json
import watchtower

# Configure CloudWatch logging
logger = logging.getLogger('datascout')
logger.setLevel(logging.INFO)

# CloudWatch handler
cw_handler = watchtower.CloudWatchLogHandler(
    log_group='datascout-app',
    stream_name=f'datascout-{datetime.utcnow().strftime("%Y-%m-%d")}',
    create_log_group=True
)
logger.addHandler(cw_handler)
```

### 4.2 Structured Log Events

#### Query Execution Log
```python
def log_query_execution(session_id: str, query: str, execution_time_ms: int,
                        success: bool, error: str = None):
    """Log a query execution event (no data values logged)."""
    logger.info(json.dumps({
        'event': 'query_executed',
        'session_id': session_id,
        'query_length': len(query),
        'query_type': classify_query_type(query),  # e.g., 'aggregation', 'trend'
        'execution_time_ms': execution_time_ms,
        'success': success,
        'error_type': type(error).__name__ if error else None,
        'timestamp': datetime.utcnow().isoformat()
    }))
```

#### Dataset Upload Log
```python
def log_dataset_upload(session_id: str, filename: str, rows: int,
                       columns: int, size_mb: float):
    """Log a dataset upload event (no data values logged)."""
    logger.info(json.dumps({
        'event': 'dataset_uploaded',
        'session_id': session_id,
        'filename_hash': hashlib.sha256(filename.encode()).hexdigest()[:12],
        'row_count': rows,
        'column_count': columns,
        'size_mb': size_mb,
        'timestamp': datetime.utcnow().isoformat()
    }))
```

### 4.3 CloudWatch Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_metric(metric_name: str, value: float, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    cloudwatch.put_metric_data(
        Namespace='DataScout',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }]
    )

# Usage examples
put_metric('QueryCount', 1)
put_metric('QueryLatency', 2500, 'Milliseconds')
put_metric('ErrorCount', 1)
put_metric('DatasetSizeMB', 45.2, 'Megabytes')
```

### 4.4 CloudWatch Alarms

```yaml
Alarms:
  - Name: DataScout-HighErrorRate
    Metric: ErrorCount
    Namespace: DataScout
    Period: 300  # 5 minutes
    EvaluationPeriods: 1
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - arn:aws:sns:us-east-1:ACCOUNT:datascout-alerts

  - Name: DataScout-HighLatency
    Metric: QueryLatency
    Namespace: DataScout
    Statistic: p95
    Period: 300
    Threshold: 45000  # 45 seconds
    ComparisonOperator: GreaterThanThreshold

  - Name: DataScout-AgentFailure
    Metric: AgentInvocationErrors
    Namespace: DataScout
    Period: 300
    Threshold: 5
    AlarmActions:
      - arn:aws:sns:us-east-1:ACCOUNT:datascout-critical-alerts
```

---

## 5. Code Interpreter Integration

### 5.1 Execution Environment Specifications

| Property | Value |
|----------|-------|
| Runtime | Python 3.11 |
| Memory | 2 GB |
| CPU | 2 vCPU |
| Execution Timeout | 30 seconds |
| Network Access | None (air-gapped) |
| Storage | 512 MB (/tmp read/write) |

### 5.2 Pre-installed Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| pandas | 2.0.3 | Data manipulation |
| numpy | 1.24.3 | Numerical computing |
| matplotlib | 3.7.1 | Static visualizations |
| seaborn | 0.12.2 | Statistical visualizations |
| scipy | 1.11.1 | Scientific computing |
| scikit-learn | 1.3.0 | Machine learning utilities |

### 5.3 Security Constraints

```python
# Blocked imports in the sandbox
BLOCKED_IMPORTS = [
    'os', 'subprocess', 'socket', 'urllib',
    'requests', 'sys', 'shutil', 'pathlib',
    'importlib', 'ctypes', 'multiprocessing'
]

# Resource limits
RESOURCE_LIMITS = {
    'max_execution_time_seconds': 30,
    'max_memory_mb': 2048,
    'max_file_size_mb': 100,
    'max_output_lines': 10000,
    'allowed_read_paths': ['/tmp'],
    'allowed_write_paths': ['/tmp']
}
```

### 5.4 Code Execution Flow

```
1. Agent generates Python code
       ↓
2. Code Interpreter receives code
       ↓
3. Syntax validation (reject invalid Python)
       ↓
4. Security scan (check for blocked patterns)
       ↓
5. Load dataset from S3 → /tmp/
       ↓
6. Execute code in sandbox
       ↓
7. Monitor resource usage (CPU, memory, time)
       ↓
8. Capture stdout, stderr, exceptions
       ↓
9. Collect generated files (/tmp/*.png, /tmp/*.csv)
       ↓
10. Upload artifacts to S3 artifacts/{session_id}/
       ↓
11. Return results + artifact URIs to Agent
```

---

## 6. Authentication & Authorization

### 6.1 AWS Authentication Flow

```
┌─────────────────┐
│  App Runner      │
│  (Frontend)      │
│                  │
│  Uses IAM Role:  │
│  AppRunnerRole   │
└────────┬─────────┘
         │
         │ AssumeRole (automatic)
         ▼
┌─────────────────────────────┐
│  IAM Role: AppRunnerRole    │
│                             │
│  Permissions:               │
│  - bedrock:InvokeAgent      │
│  - bedrock:InvokeModel      │
│  - s3:PutObject             │
│  - s3:GetObject             │
│  - s3:DeleteObject          │
│  - s3:HeadObject            │
│  - s3:ListBucket            │
│  - logs:CreateLogGroup      │
│  - logs:PutLogEvents        │
│  - cloudwatch:PutMetricData │
└─────────────────────────────┘
```

### 6.2 Environment Variables

```bash
# Required environment variables
AWS_REGION=us-east-1
S3_BUCKET=datascout-storage
BEDROCK_AGENT_ID=<agent-id>
BEDROCK_AGENT_ALIAS_ID=<alias-id>

# Optional
DEBUG=false
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_QUERIES=5
```

---

## 7. Error Handling & Retry Strategy

### 7.1 Error Classification

| Error Type | HTTP Code | Retryable | Action |
|-----------|-----------|-----------|--------|
| ThrottlingException | 429 | Yes | Exponential backoff (1s, 2s, 4s) |
| ServiceUnavailable | 503 | Yes | Retry after 5 seconds |
| ValidationException | 400 | No | Return user-friendly error |
| AccessDeniedException | 403 | No | Log and alert |
| ResourceNotFoundException | 404 | No | Check agent/alias configuration |
| InternalServerError | 500 | Yes | Retry up to 3 times |

### 7.2 Retry Logic

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=30.0):
    """Decorator for retrying API calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as e:
                    if attempt == max_retries:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Retry {attempt + 1}/{max_retries}: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

RETRYABLE_EXCEPTIONS = (
    botocore.exceptions.ClientError,  # ThrottlingException, 503
    ConnectionError,
    TimeoutError
)
```

### 7.3 User-Facing Error Messages

```python
ERROR_MESSAGES = {
    'file_too_large': {
        'title': '📁 File Too Large',
        'message': 'Your dataset is {size}MB, but the maximum allowed is 100MB.',
        'suggestion': 'Try uploading a sample of your data or splitting into smaller files.'
    },
    'invalid_format': {
        'title': '⚠️ Unsupported File Format',
        'message': 'DataScout supports CSV, Excel (.xlsx), and JSON formats.',
        'suggestion': 'Convert your file to one of these formats and try again.'
    },
    'execution_timeout': {
        'title': '⏱️ Analysis Timed Out',
        'message': 'Your analysis exceeded the 30-second time limit.',
        'suggestion': 'Try simplifying your query or using a smaller dataset.'
    },
    'missing_column': {
        'title': '🔍 Column Not Found',
        'message': 'The column "{column}" doesn\'t exist in your dataset.',
        'suggestion': 'Available columns: {available_columns}'
    },
    'rate_limited': {
        'title': '🚦 System Busy',
        'message': 'Too many requests. Please wait a moment and try again.',
        'suggestion': 'The system will be ready in a few seconds.'
    },
    'agent_error': {
        'title': '🤖 Analysis Error',
        'message': 'The AI analyst encountered an issue processing your query.',
        'suggestion': 'Try rephrasing your question or breaking it into simpler parts.'
    }
}
```

---

## 8. Rate Limits & Quotas

### 8.1 AWS Service Limits

| Service | Limit | Default | Notes |
|---------|-------|---------|-------|
| Bedrock InvokeAgent | Requests/second | 10 | Can request increase |
| Bedrock Code Interpreter | Concurrent executions | 5 | Per agent |
| S3 PutObject | Requests/second | 3,500 | Per prefix |
| S3 GetObject | Requests/second | 5,500 | Per prefix |
| CloudWatch PutMetricData | Requests/second | 150 | Per account |

### 8.2 Application-Level Limits

| Limit | Value | Enforcement |
|-------|-------|-------------|
| Max concurrent queries per session | 1 | Queue + lock |
| Max queries per session | 50 | Counter check |
| Max file upload size | 100 MB | Client + server validation |
| Max dataset rows | 1,000,000 | pandas check after load |
| Session timeout | 30 minutes | Timer-based cleanup |
| Code execution timeout | 30 seconds | Bedrock enforced |

---

## 9. Testing API Integrations

### 9.1 Unit Tests (Mocked)

```python
import pytest
from unittest.mock import patch, MagicMock

class TestBedrockAgentClient:
    @patch('boto3.client')
    def test_invoke_agent_success(self, mock_boto):
        """Test successful agent invocation."""
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke_agent.return_value = {
            'completion': [
                {'chunk': {'bytes': b'Analysis results here'}}
            ],
            'sessionId': 'test-session'
        }

        client = BedrockAgentClient()
        result = client.invoke_agent(
            query="What is the average?",
            session_id="test-session",
            dataset_uri="s3://bucket/test.csv"
        )

        assert result is not None
        assert 'explanation' in result
        mock_client.invoke_agent.assert_called_once()

    @patch('boto3.client')
    def test_invoke_agent_throttling(self, mock_boto):
        """Test rate limiting handling."""
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke_agent.side_effect = \
            mock_client.exceptions.ThrottlingException({'Error': {}}, 'InvokeAgent')

        client = BedrockAgentClient()
        with pytest.raises(RateLimitError):
            client.invoke_agent("query", "session", "s3://bucket/data.csv")

class TestS3Handler:
    @patch('boto3.client')
    def test_upload_dataset(self, mock_boto):
        """Test dataset upload to S3."""
        mock_client = MagicMock()
        mock_boto.return_value = mock_client

        handler = S3Handler()
        file_obj = create_test_csv(rows=100)
        uri = handler.upload_dataset(file_obj, "test-session")

        assert uri.startswith("s3://datascout-storage/datasets/")
        mock_client.upload_fileobj.assert_called_once()

    def test_validate_file_too_large(self):
        """Test file size validation."""
        handler = S3Handler()
        large_file = create_test_csv(rows=10_000_000)  # > 100MB

        with pytest.raises(DataUploadError, match="exceeds limit"):
            handler._validate_file(large_file)
```

### 9.2 Integration Tests

```python
class TestEndToEndFlow:
    """Integration tests requiring live AWS services."""

    @pytest.mark.integration
    def test_upload_and_query(self):
        """Test full upload → query → result flow."""
        # 1. Upload dataset
        s3 = S3Handler()
        uri = s3.upload_dataset(create_sales_csv(), "integration-test")

        # 2. Invoke agent
        agent = BedrockAgentClient()
        result = agent.invoke_agent(
            query="What is the total revenue?",
            session_id="integration-test",
            dataset_uri=uri
        )

        # 3. Verify
        assert result['code'] is not None
        assert result['results'] is not None
        assert 'revenue' in result['results'].lower()

        # 4. Cleanup
        s3.delete_session_data("integration-test")
```

---

## 10. SDK Dependencies

### 10.1 Required Python Packages

```txt
# requirements.txt — API integration dependencies
boto3>=1.26.0
botocore>=1.29.0
streamlit>=1.25.0
pandas>=1.5.0
numpy>=1.23.0
watchtower>=3.0.0     # CloudWatch logging
python-dotenv>=1.0.0  # Environment variable management
```

### 10.2 AWS SDK Configuration

```python
# Recommended boto3 configuration
import botocore.config

boto3_config = botocore.config.Config(
    region_name='us-east-1',
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'      # Adaptive retry mode for throttling
    },
    connect_timeout=10,
    read_timeout=60,             # Longer timeout for agent invocations
    max_pool_connections=25
)

bedrock_client = boto3.client(
    'bedrock-agent-runtime',
    config=boto3_config
)
```

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
