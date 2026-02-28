# DataScout — Implementation Guide

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Implementation Overview

This guide provides step-by-step implementation instructions for building DataScout from scratch. It covers the development workflow, code implementation for every module, configuration, and integration patterns.

### 1.1 Development Timeline

```
Hours 0–12   → Infrastructure Setup (AWS services, IAM, S3)
Hours 12–24  → Agent Creation (Bedrock Agent, instructions, tools)
Hours 24–36  → Frontend & Backend (Streamlit UI, API integration)
Hours 36–48  → Testing & Polish (E2E testing, UI/UX, demo prep)
```

### 1.2 Prerequisites

```bash
# System requirements
python --version   # 3.9+
aws --version      # 2.x+
docker --version   # 20.x+ (optional for deployment)

# AWS access
aws sts get-caller-identity  # Verify credentials

# Clone repository
git clone https://github.com/org/datascout.git
cd datascout

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Phase 1: Infrastructure Setup (Hours 0–12)

### 2.1 S3 Bucket Creation

```python
# scripts/create_buckets.sh

#!/bin/bash
set -e

BUCKET_NAME="datascout-storage"
REGION="us-east-1"

echo "Creating S3 bucket: $BUCKET_NAME"
aws s3 mb s3://$BUCKET_NAME --region $REGION

echo "Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

echo "Enabling encryption..."
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

echo "Blocking public access..."
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,\
        BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "Setting lifecycle rules..."
aws s3api put-bucket-lifecycle-configuration \
    --bucket $BUCKET_NAME \
    --lifecycle-configuration file://lifecycle-config.json

echo "✅ S3 bucket setup complete"
```

### 2.2 IAM Role Creation

```python
# scripts/create_iam_roles.sh

#!/bin/bash
set -e

# App Runner execution role
aws iam create-role \
    --role-name DataScout-AppRunnerRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "tasks.apprunner.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# Attach Bedrock access
aws iam attach-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Create and attach S3 + CloudWatch policies
# (See deployment.md for full policy documents)

echo "✅ IAM roles created"
```

### 2.3 Environment Configuration

```python
# config.py

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized application configuration."""

    # AWS
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET = os.getenv('S3_BUCKET', 'datascout-storage')
    BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID')
    BEDROCK_AGENT_ALIAS_ID = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'PRODUCTION')

    # Application limits
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls', '.json'}
    SESSION_TIMEOUT_SECONDS = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30')) * 60
    CODE_EXECUTION_TIMEOUT = 30
    MAX_CONCURRENT_QUERIES = int(os.getenv('MAX_CONCURRENT_QUERIES', '5'))

    # Feature flags
    ENABLE_VISUALIZATIONS = True
    ENABLE_ADVANCED_STATS = True
    DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

    @classmethod
    def validate(cls):
        """Validate required configuration on startup."""
        required = {
            'BEDROCK_AGENT_ID': cls.BEDROCK_AGENT_ID,
            'S3_BUCKET': cls.S3_BUCKET,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        return True
```

---

## 3. Phase 2: Agent Creation (Hours 12–24)

### 3.1 Bedrock Agent Setup

```bash
# scripts/setup_agent.sh

#!/bin/bash
set -e

AGENT_NAME="DataScout-Analyst"
MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
ROLE_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/DataScout-BedrockAgentRole"

# Read instructions from file
INSTRUCTIONS=$(cat agent_instructions.txt)

# Create agent
AGENT_ID=$(aws bedrock-agent create-agent \
    --agent-name "$AGENT_NAME" \
    --foundation-model "$MODEL_ID" \
    --instruction "$INSTRUCTIONS" \
    --agent-resource-role-arn "$ROLE_ARN" \
    --idle-session-ttl-in-seconds 600 \
    --query 'agent.agentId' --output text)

echo "Agent created: $AGENT_ID"

# Prepare agent
aws bedrock-agent prepare-agent --agent-id "$AGENT_ID"
echo "Agent prepared"

# Create production alias
ALIAS_ID=$(aws bedrock-agent create-agent-alias \
    --agent-id "$AGENT_ID" \
    --agent-alias-name PRODUCTION \
    --query 'agentAlias.agentAliasId' --output text)

echo "Alias created: $ALIAS_ID"
echo ""
echo "Add these to your .env file:"
echo "BEDROCK_AGENT_ID=$AGENT_ID"
echo "BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID"
```

### 3.2 Agent Instructions

```
# agent_instructions.txt

You are DataScout, an autonomous enterprise data analyst AI. Your primary role
is to help users analyze datasets by writing and executing Python code.

## CRITICAL RULES (MUST FOLLOW)
1. NEVER guess or hallucinate numerical values — ALL numbers must come from code execution
2. ALWAYS use the Code Interpreter to compute results
3. Generate clean, readable Python code using pandas and numpy
4. Include error handling in all generated code
5. Explain your analytical approach clearly
6. Show all code to the user for full transparency

## WORKFLOW
1. Understand the user's analytical question
2. Plan the analysis steps mentally
3. Write Python code to perform the analysis
4. Execute the code using Code Interpreter
5. Validate the results (check for nulls, errors)
6. Create visualizations if they add value
7. Present results with clear explanations

## CODE STRUCTURE (Always follow this pattern)
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load data
df = pd.read_csv('/tmp/uploaded_data.csv')

# 2. Validate data
print(f"Dataset shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# 3. Perform analysis
# [Your analysis code here]

# 4. Validate results
if result.isnull().any():
    print("Warning: Null values detected in results")

# 5. Create visualization (if helpful)
plt.figure(figsize=(10, 6))
# [Visualization code]
plt.savefig('/tmp/output.png', dpi=150, bbox_inches='tight')

# 6. Print results
print(result.to_markdown(index=False))
```

## RESPONSE FORMAT
1. **Analysis Approach:** Brief explanation of what you'll do
2. **Code:** The Python code in a code block
3. **Results:** Tables, statistics, key findings
4. **Visualization:** Charts (if created)
5. **Insights:** Key takeaways and next steps

## LIBRARIES AVAILABLE
pandas, numpy, matplotlib, seaborn, scipy, scikit-learn
```

---

## 4. Phase 3: Frontend & Backend Integration (Hours 24–36)

### 4.1 Main Application Entry Point

```python
# streamlit_app/app.py

import streamlit as st
import uuid
from datetime import datetime
from config import Config
from services.bedrock_client import BedrockAgentClient
from services.s3_handler import S3Handler
from services.session_manager import SessionManager
from components.file_upload import render_upload_widget
from components.query_input import render_query_input
from components.results_display import render_results
from components.dataset_preview import render_preview
from utils.error_handler import handle_error
from utils.logger import log_query_execution, log_dataset_upload

# Page configuration
st.set_page_config(
    page_title="DataScout — Enterprise Data Analyst",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
with open("streamlit_app/assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def initialize_session():
    """Initialize session state on first load."""
    defaults = {
        'session_id': str(uuid.uuid4()),
        'session_created_at': datetime.utcnow(),
        'dataset_loaded': False,
        'dataset_s3_uri': None,
        'dataset_metadata': None,
        'conversation_history': [],
        'is_processing': False,
        'last_error': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """Main application entry point."""
    # Validate config
    Config.validate()

    # Initialize session
    initialize_session()

    # Initialize services
    bedrock = BedrockAgentClient()
    s3 = S3Handler()

    # Header
    st.title("🔬 DataScout")
    st.caption("Autonomous Enterprise Data Analyst • Powered by Claude 3.5 Sonnet")
    st.divider()

    # === SECTION 1: File Upload ===
    uploaded_file = render_upload_widget()

    if uploaded_file and not st.session_state.dataset_loaded:
        with st.spinner("Uploading and analyzing dataset..."):
            try:
                # Upload to S3
                s3_uri = s3.upload_dataset(
                    uploaded_file,
                    st.session_state.session_id
                )
                st.session_state.dataset_s3_uri = s3_uri

                # Extract metadata
                metadata = s3.get_dataset_metadata(s3_uri)
                st.session_state.dataset_metadata = metadata
                st.session_state.dataset_loaded = True

                # Log upload
                log_dataset_upload(
                    st.session_state.session_id,
                    metadata['filename'],
                    metadata['rows'],
                    len(metadata['columns']),
                    metadata['size_mb']
                )

                st.success(f"✅ Dataset loaded: {metadata['filename']}")
            except Exception as e:
                handle_error(e)

    # === SECTION 2: Dataset Preview ===
    if st.session_state.dataset_loaded:
        render_preview(st.session_state.dataset_metadata)
        st.divider()

    # === SECTION 3: Query Input ===
    query = render_query_input(st.session_state.dataset_loaded)

    if query and not st.session_state.is_processing:
        st.session_state.is_processing = True
        start_time = datetime.utcnow()

        with st.spinner("🔍 Analyzing your data..."):
            try:
                response = bedrock.invoke_agent(
                    query=query,
                    session_id=st.session_state.session_id,
                    dataset_uri=st.session_state.dataset_s3_uri
                )

                execution_time = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                # Store in conversation history
                st.session_state.conversation_history.append({
                    'id': str(uuid.uuid4()),
                    'query': query,
                    'response': response,
                    'execution_time_ms': execution_time,
                    'success': True,
                    'timestamp': datetime.utcnow()
                })

                # Log query
                log_query_execution(
                    st.session_state.session_id,
                    query, execution_time, True
                )

            except Exception as e:
                handle_error(e)
                log_query_execution(
                    st.session_state.session_id,
                    query, 0, False, error=e
                )
            finally:
                st.session_state.is_processing = False

    # === SECTION 4: Results Display ===
    if st.session_state.conversation_history:
        latest = st.session_state.conversation_history[-1]
        if latest['success']:
            render_results(latest['response'])

    # === SECTION 5: Conversation History ===
    if len(st.session_state.conversation_history) > 1:
        st.divider()
        st.subheader("📜 Query History")
        for i, entry in enumerate(
            reversed(st.session_state.conversation_history[:-1]), 1
        ):
            status = "✅" if entry['success'] else "❌"
            time_str = f"{entry['execution_time_ms']}ms"
            with st.expander(f"{status} Q{i}: {entry['query']} ({time_str})"):
                render_results(entry['response'])

    # Footer
    st.divider()
    st.caption("DataScout v1.0 • Powered by Claude 3.5 Sonnet on Amazon Bedrock")


if __name__ == '__main__':
    main()
```

### 4.2 Service Layer Implementation

#### Bedrock Client

```python
# streamlit_app/services/bedrock_client.py

import os
import re
import boto3
import botocore.config
from config import Config


class BedrockAgentClient:
    """Amazon Bedrock Agent Runtime client wrapper."""

    def __init__(self):
        config = botocore.config.Config(
            region_name=Config.AWS_REGION,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60
        )
        self.client = boto3.client('bedrock-agent-runtime', config=config)
        self.agent_id = Config.BEDROCK_AGENT_ID
        self.agent_alias_id = Config.BEDROCK_AGENT_ALIAS_ID

    def invoke_agent(self, query: str, session_id: str,
                     dataset_uri: str) -> dict:
        """Invoke Bedrock Agent and return parsed response."""
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

    def _parse_response(self, response: dict) -> dict:
        """Parse streaming response into components."""
        chunks = []
        for event in response['completion']:
            if 'chunk' in event:
                chunks.append(event['chunk']['bytes'].decode('utf-8'))

        full_text = ''.join(chunks)
        return self._extract_components(full_text)

    def _extract_components(self, text: str) -> dict:
        """Extract structured components from response text."""
        components = {
            'explanation': '',
            'code': '',
            'results': '',
            'visualizations': [],
            'next_steps': []
        }

        # Extract Python code blocks
        code_blocks = re.findall(r'```python\n(.*?)```', text, re.DOTALL)
        if code_blocks:
            components['code'] = code_blocks[-1].strip()

        # Extract S3 visualization URIs
        s3_uris = re.findall(r's3://[^\s\)\"\']+\.png', text)
        components['visualizations'] = s3_uris

        # Split text around code blocks for explanation and results
        parts = re.split(r'```python.*?```', text, flags=re.DOTALL)
        if len(parts) >= 1:
            components['explanation'] = parts[0].strip()
        if len(parts) >= 2:
            components['results'] = parts[-1].strip()

        return components
```

#### S3 Handler

```python
# streamlit_app/services/s3_handler.py

import io
import boto3
import pandas as pd
from pathlib import Path
from config import Config


class S3Handler:
    """Amazon S3 operations for dataset and artifact management."""

    def __init__(self):
        self.s3 = boto3.client('s3', region_name=Config.AWS_REGION)
        self.bucket = Config.S3_BUCKET

    def upload_dataset(self, file_obj, session_id: str) -> str:
        """Upload dataset to S3 with validation."""
        self._validate_file(file_obj)

        key = f"datasets/{session_id}/original/{file_obj.name}"
        self.s3.upload_fileobj(
            file_obj, self.bucket, key,
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )
        return f"s3://{self.bucket}/{key}"

    def get_dataset_metadata(self, s3_uri: str) -> dict:
        """Extract metadata from uploaded dataset."""
        bucket, key = self._parse_uri(s3_uri)
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
            raise ValueError(f"Unsupported format: {ext}")

        return {
            'filename': filename,
            'rows': len(df),
            'columns': list(df.columns),
            'dtypes': {c: str(d) for c, d in df.dtypes.items()},
            'size_mb': round(len(body) / (1024 * 1024), 2),
            'preview': df.head(5).to_dict(orient='records'),
            'null_counts': df.isnull().sum().to_dict()
        }

    def download_artifact(self, s3_uri: str) -> bytes:
        """Download artifact bytes from S3."""
        bucket, key = self._parse_uri(s3_uri)
        response = self.s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    def _validate_file(self, file_obj):
        """Validate file format and size."""
        ext = Path(file_obj.name).suffix.lower()
        if ext not in Config.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported: {', '.join(Config.SUPPORTED_FORMATS)}"
            )
        file_obj.seek(0, 2)
        size_mb = file_obj.tell() / (1024 * 1024)
        file_obj.seek(0)
        if size_mb > Config.MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large: {size_mb:.1f}MB > {Config.MAX_FILE_SIZE_MB}MB")

    @staticmethod
    def _parse_uri(uri: str) -> tuple:
        parts = uri.replace('s3://', '').split('/', 1)
        return parts[0], parts[1]
```

### 4.3 Utility Modules

#### Error Handler

```python
# streamlit_app/utils/error_handler.py

import streamlit as st
import logging

logger = logging.getLogger('datascout')

ERROR_MESSAGES = {
    'ValueError': {
        'title': '⚠️ Invalid Input',
        'suggestion': 'Please check your file format and try again.'
    },
    'FileNotFoundError': {
        'title': '📁 File Not Found',
        'suggestion': 'The requested file could not be located.'
    },
    'TimeoutError': {
        'title': '⏱️ Request Timed Out',
        'suggestion': 'Try a simpler query or smaller dataset.'
    },
    'default': {
        'title': '❌ Something Went Wrong',
        'suggestion': 'Please try again. If the issue persists, contact support.'
    }
}


def handle_error(error: Exception):
    """Display user-friendly error and log details."""
    error_type = type(error).__name__
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['default'])

    st.error(f"**{error_info['title']}**\n\n{str(error)}")
    st.info(f"💡 {error_info['suggestion']}")

    logger.error(f"[{error_type}] {str(error)}", exc_info=True)
    st.session_state.last_error = str(error)
```

#### Logger

```python
# streamlit_app/utils/logger.py

import logging
import json
import hashlib
from datetime import datetime

logger = logging.getLogger('datascout')
logger.setLevel(logging.INFO)


def log_query_execution(session_id: str, query: str,
                        execution_time_ms: int, success: bool,
                        error: Exception = None):
    """Log query execution without capturing data values."""
    logger.info(json.dumps({
        'event': 'query_executed',
        'session_id': session_id,
        'query_length': len(query),
        'execution_time_ms': execution_time_ms,
        'success': success,
        'error_type': type(error).__name__ if error else None,
        'timestamp': datetime.utcnow().isoformat()
    }))


def log_dataset_upload(session_id: str, filename: str,
                       rows: int, columns: int, size_mb: float):
    """Log dataset upload event."""
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

---

## 5. Phase 4: Testing & Polish (Hours 36–48)

### 5.1 Demo Dataset Preparation

```python
# scripts/seed_demo_data.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sales_dataset():
    """Generate a realistic sales dataset for demo."""
    np.random.seed(42)
    n = 1000

    regions = ['North', 'South', 'East', 'West']
    products = ['Widget A', 'Widget B', 'Gadget X', 'Gadget Y', 'Tool Z']
    categories = ['Electronics', 'Hardware', 'Software']

    dates = [datetime(2025, 1, 1) + timedelta(days=np.random.randint(0, 365))
             for _ in range(n)]

    df = pd.DataFrame({
        'date': dates,
        'region': np.random.choice(regions, n),
        'product': np.random.choice(products, n),
        'category': np.random.choice(categories, n),
        'revenue': np.random.uniform(100, 10000, n).round(2),
        'quantity': np.random.randint(1, 100, n),
        'cost': np.random.uniform(50, 5000, n).round(2),
        'customer_id': np.random.randint(1000, 9999, n)
    })

    df['profit'] = (df['revenue'] - df['cost']).round(2)
    df.to_csv('demo/datasets/sales_data.csv', index=False)
    print(f"Created sales_data.csv: {len(df)} rows")

if __name__ == '__main__':
    create_sales_dataset()
```

### 5.2 Demo Scenario Runner

```python
# scripts/run_demo.py

DEMO_QUERIES = [
    "What are the top 5 products by total revenue?",
    "Show me monthly revenue trends",
    "What is the average revenue by region?",
    "What is the correlation between quantity and revenue?",
    "Show me the profit distribution across categories"
]

# Run each query and verify results
# See test_plan.md for detailed validation criteria
```

---

## 6. Coding Standards

### 6.1 Python Style Guide

| Rule | Standard |
|------|----------|
| Formatting | PEP 8 (enforced by flake8) |
| Max line length | 120 characters |
| Docstrings | Google style |
| Type hints | Required for all public methods |
| Imports | Sorted with isort |
| Naming | snake_case for functions/vars, PascalCase for classes |

### 6.2 Git Workflow

```bash
# Branch naming
feature/add-file-upload
bugfix/fix-session-timeout
docs/update-api-guide

# Commit message format
[type] Brief description

# Examples
[feat] Add file upload component
[fix] Handle missing columns in query
[docs] Update deployment guide
[test] Add integration tests for S3 handler
[refactor] Extract validation logic to utils
```

### 6.3 Code Review Checklist

- [ ] All public methods have docstrings with type hints
- [ ] Error handling is comprehensive (no bare `except`)
- [ ] No hardcoded credentials or secrets
- [ ] Unit tests cover new functionality
- [ ] No data values are logged (privacy compliance)
- [ ] Imports are sorted and minimal
- [ ] No TODO comments left without tracking

---

## 7. Troubleshooting Common Issues

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| `ModuleNotFoundError: streamlit` | Virtual env not activated | `source venv/bin/activate` |
| `NoCredentialsError` | AWS not configured | `aws configure` |
| `Agent returns empty` | Code Interpreter not bound | Re-run `setup_agent.sh` |
| `S3 Access Denied` | IAM policy wrong | Check role ARN and bucket policy |
| Port 8501 in use | Another Streamlit running | Kill process or use different port |
| `ValidationException` | Agent alias not prepared | Run `aws bedrock-agent prepare-agent` |

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
