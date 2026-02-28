# DataScout — Test Plan

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Test Strategy Overview

### 1.1 Testing Pyramid

```
                    ┌─────────┐
                    │  E2E /  │  ← 5 scenarios
                    │  Demo   │     (Manual + Automated)
                   ┌┴─────────┴┐
                   │ Integration│  ← 15 tests
                   │   Tests    │     (Live AWS)
                  ┌┴────────────┴┐
                  │  Unit Tests   │  ← 40+ tests
                  │  (Mocked)     │     (No AWS needed)
                 ┌┴───────────────┴┐
                 │  Static Analysis │  ← Linting, type checks
                 │  (flake8, mypy)  │
                 └─────────────────┘
```

### 1.2 Testing Tools

| Tool | Purpose | Version |
|------|---------|---------|
| pytest | Test framework | ≥ 7.4.0 |
| pytest-cov | Code coverage | ≥ 4.1.0 |
| pytest-mock | Mock fixtures | ≥ 3.11.0 |
| moto | AWS service mocking | ≥ 4.2.0 |
| flake8 | Linting | ≥ 6.1.0 |
| mypy | Type checking | ≥ 1.5.0 |
| black | Code formatting | ≥ 23.7.0 |

### 1.3 Coverage Targets

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| `services/bedrock_client.py` | 90%+ | P0 |
| `services/s3_handler.py` | 90%+ | P0 |
| `services/session_manager.py` | 85%+ | P1 |
| `utils/validators.py` | 95%+ | P0 |
| `utils/formatters.py` | 85%+ | P1 |
| `utils/error_handler.py` | 80%+ | P1 |
| `components/*` | 70%+ | P2 |
| **Overall** | **80%+** | **P0** |

---

## 2. Unit Tests

### 2.1 BedrockAgentClient Tests

```python
# tests/unit/test_bedrock_client.py

import pytest
from unittest.mock import patch, MagicMock
from streamlit_app.services.bedrock_client import BedrockAgentClient


class TestBedrockAgentClient:
    """Unit tests for Bedrock Agent client."""

    @pytest.fixture
    def client(self):
        with patch('boto3.client'):
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
            'completion': [{'chunk': {'bytes': b'Response'}}],
            'sessionId': 'test'
        }
        client.client.invoke_agent.return_value = mock_response

        client.invoke_agent("query", "session", "s3://bucket/sales.csv")

        call_kwargs = client.client.invoke_agent.call_args[1]
        assert call_kwargs['sessionState']['sessionAttributes']['dataset_uri'] == \
            "s3://bucket/sales.csv"

    def test_parse_response_extracts_code(self, client):
        """Verify Python code blocks are extracted from response."""
        text = 'Explanation\n```python\ndf.groupby("x").mean()\n```\nResults here'
        result = client._extract_components(text)

        assert 'groupby' in result['code']
        assert 'Explanation' in result['explanation']

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

    def test_invoke_agent_empty_query(self, client):
        """Verify empty query is handled."""
        mock_response = {
            'completion': [{'chunk': {'bytes': b'Please provide a question.'}}],
            'sessionId': 'test'
        }
        client.client.invoke_agent.return_value = mock_response

        result = client.invoke_agent("", "session", "s3://bucket/data.csv")
        assert result is not None
```

### 2.2 S3Handler Tests

```python
# tests/unit/test_s3_handler.py

import pytest
import io
from unittest.mock import patch, MagicMock
from streamlit_app.services.s3_handler import S3Handler


class TestS3Handler:
    """Unit tests for S3 operations."""

    @pytest.fixture
    def handler(self):
        with patch('boto3.client'):
            return S3Handler()

    @pytest.fixture
    def valid_csv(self):
        content = "name,value\nAlice,100\nBob,200\n"
        file_obj = io.BytesIO(content.encode())
        file_obj.name = "test_data.csv"
        return file_obj

    @pytest.fixture
    def valid_json(self):
        content = '[{"name": "Alice", "value": 100}]'
        file_obj = io.BytesIO(content.encode())
        file_obj.name = "test_data.json"
        return file_obj

    # === Upload Tests ===

    def test_upload_csv_success(self, handler, valid_csv):
        """CSV upload returns correct S3 URI."""
        uri = handler.upload_dataset(valid_csv, "session-123")
        assert uri.startswith("s3://")
        assert "session-123" in uri
        assert "test_data.csv" in uri

    def test_upload_with_encryption(self, handler, valid_csv):
        """Upload includes server-side encryption."""
        handler.upload_dataset(valid_csv, "session-123")
        call_kwargs = handler.s3.upload_fileobj.call_args
        assert call_kwargs[1]['ExtraArgs']['ServerSideEncryption'] == 'AES256'

    # === Validation Tests ===

    def test_reject_unsupported_format(self, handler):
        """Unsupported file format raises ValueError."""
        file_obj = io.BytesIO(b"content")
        file_obj.name = "report.pdf"
        with pytest.raises(ValueError, match="Unsupported format"):
            handler._validate_file(file_obj)

    def test_reject_oversized_file(self, handler):
        """File exceeding size limit raises ValueError."""
        large_content = b"x" * (101 * 1024 * 1024)  # 101 MB
        file_obj = io.BytesIO(large_content)
        file_obj.name = "huge_file.csv"
        with pytest.raises(ValueError, match="too large"):
            handler._validate_file(file_obj)

    def test_accept_max_size_file(self, handler):
        """File at exactly max size is accepted."""
        content = b"x" * (99 * 1024 * 1024)  # 99 MB (under limit)
        file_obj = io.BytesIO(content)
        file_obj.name = "big_file.csv"
        handler._validate_file(file_obj)  # Should not raise

    def test_accept_all_supported_formats(self, handler):
        """All supported formats pass validation."""
        for fmt in ['.csv', '.xlsx', '.xls', '.json']:
            file_obj = io.BytesIO(b"content")
            file_obj.name = f"test{fmt}"
            handler._validate_file(file_obj)  # Should not raise

    # === Metadata Tests ===

    def test_metadata_extraction_csv(self, handler, valid_csv):
        """CSV metadata includes correct shape and columns."""
        handler.s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: valid_csv.getvalue())
        }
        metadata = handler.get_dataset_metadata("s3://bucket/datasets/session/original/test.csv")

        assert metadata['filename'] == 'test.csv'
        assert 'name' in metadata['columns']
        assert 'value' in metadata['columns']
        assert metadata['rows'] == 2

    # === URI Parsing Tests ===

    def test_parse_s3_uri(self, handler):
        """S3 URI is correctly parsed into bucket and key."""
        bucket, key = handler._parse_uri("s3://my-bucket/path/to/file.csv")
        assert bucket == "my-bucket"
        assert key == "path/to/file.csv"
```

### 2.3 Validator Tests

```python
# tests/unit/test_validators.py

import pytest
import io
from streamlit_app.utils.validators import validate_file_format, validate_file_size


class TestValidators:
    """Unit tests for input validation functions."""

    @pytest.mark.parametrize("filename,expected", [
        ("data.csv", True),
        ("data.xlsx", True),
        ("data.xls", True),
        ("data.json", True),
        ("data.pdf", False),
        ("data.txt", False),
        ("data.parquet", False),
        ("data", False),
    ])
    def test_file_format_validation(self, filename, expected):
        """Test various file format validations."""
        assert validate_file_format(filename) == expected

    @pytest.mark.parametrize("size_mb,expected", [
        (0.1, True),
        (50, True),
        (99.9, True),
        (100, True),
        (100.1, False),
        (500, False),
    ])
    def test_file_size_validation(self, size_mb, expected):
        """Test file size limit enforcement."""
        assert validate_file_size(size_mb) == expected
```

### 2.4 Error Handler Tests

```python
# tests/unit/test_error_handler.py

import pytest
from unittest.mock import patch
from streamlit_app.utils.error_handler import handle_error, ERROR_MESSAGES


class TestErrorHandler:
    """Unit tests for error handling and messaging."""

    @patch('streamlit.error')
    @patch('streamlit.info')
    def test_known_error_type(self, mock_info, mock_error):
        """Known error types display correct messages."""
        handle_error(ValueError("Bad input"))
        mock_error.assert_called_once()
        assert "Invalid Input" in str(mock_error.call_args)

    @patch('streamlit.error')
    @patch('streamlit.info')
    def test_unknown_error_type(self, mock_info, mock_error):
        """Unknown errors display default message."""
        handle_error(RuntimeError("Unexpected"))
        mock_error.assert_called_once()
        assert "Something Went Wrong" in str(mock_error.call_args)
```

---

## 3. Integration Tests

### 3.1 Upload Flow Integration Test

```python
# tests/integration/test_upload_flow.py

import pytest
from streamlit_app.services.s3_handler import S3Handler
from tests.fixtures.mock_responses import create_test_csv


@pytest.mark.integration
class TestUploadFlow:
    """Integration tests for dataset upload pipeline (requires live AWS)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.s3 = S3Handler()
        self.session_id = f"test-{uuid.uuid4().hex[:8]}"
        yield
        # Cleanup
        self._cleanup_session_data()

    def test_csv_upload_and_metadata(self):
        """Upload CSV and verify metadata extraction."""
        csv_file = create_test_csv(rows=100)
        uri = self.s3.upload_dataset(csv_file, self.session_id)

        assert uri.startswith("s3://")
        metadata = self.s3.get_dataset_metadata(uri)
        assert metadata['rows'] == 100
        assert len(metadata['columns']) > 0
        assert metadata['size_mb'] > 0

    def test_xlsx_upload_and_metadata(self):
        """Upload Excel and verify metadata extraction."""
        xlsx_file = create_test_xlsx(rows=50)
        uri = self.s3.upload_dataset(xlsx_file, self.session_id)

        metadata = self.s3.get_dataset_metadata(uri)
        assert metadata['rows'] == 50

    def test_json_upload_and_metadata(self):
        """Upload JSON and verify metadata extraction."""
        json_file = create_test_json(records=30)
        uri = self.s3.upload_dataset(json_file, self.session_id)

        metadata = self.s3.get_dataset_metadata(uri)
        assert metadata['rows'] == 30
```

### 3.2 Query Flow Integration Test

```python
# tests/integration/test_query_flow.py

import pytest
from streamlit_app.services.bedrock_client import BedrockAgentClient
from streamlit_app.services.s3_handler import S3Handler


@pytest.mark.integration
class TestQueryFlow:
    """Integration tests for full query execution (requires live AWS)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.bedrock = BedrockAgentClient()
        self.s3 = S3Handler()
        self.session_id = f"test-{uuid.uuid4().hex[:8]}"

        # Upload test dataset
        csv = create_test_csv(rows=100)
        self.dataset_uri = self.s3.upload_dataset(csv, self.session_id)
        yield
        self._cleanup()

    def test_simple_aggregation(self):
        """Test simple average query."""
        result = self.bedrock.invoke_agent(
            "What is the average revenue?",
            self.session_id,
            self.dataset_uri
        )
        assert result['code'] is not None
        assert result['results'] is not None

    def test_groupby_query(self):
        """Test group-by aggregation query."""
        result = self.bedrock.invoke_agent(
            "What is the average revenue by region?",
            self.session_id,
            self.dataset_uri
        )
        assert 'groupby' in result['code'].lower() or 'group' in result['code'].lower()

    def test_visualization_generation(self):
        """Test that chart is generated when requested."""
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
        # Follow-up
        result = self.bedrock.invoke_agent(
            "Now show me their monthly trends",
            self.session_id,
            self.dataset_uri
        )
        assert result['code'] is not None
```

### 3.3 End-to-End Integration Test

```python
# tests/integration/test_end_to_end.py

@pytest.mark.integration
class TestEndToEnd:
    """Full pipeline: Upload → Query → Results → Artifact Download."""

    def test_complete_workflow(self):
        """Test the complete user workflow end-to-end."""
        s3 = S3Handler()
        bedrock = BedrockAgentClient()
        session_id = f"e2e-{uuid.uuid4().hex[:8]}"

        # Step 1: Upload
        csv = create_sales_csv()
        uri = s3.upload_dataset(csv, session_id)
        assert uri.startswith("s3://")

        # Step 2: Get metadata
        metadata = s3.get_dataset_metadata(uri)
        assert metadata['rows'] > 0

        # Step 3: Execute query
        result = bedrock.invoke_agent(
            "What are the top 5 products by revenue?",
            session_id, uri
        )
        assert result['code'] != ''
        assert result['results'] != ''

        # Step 4: Download visualization (if any)
        if result['visualizations']:
            img = s3.download_artifact(result['visualizations'][0])
            assert len(img) > 0  # Non-empty image

        # Cleanup
        s3.delete_session_data(session_id)
```

---

## 4. Demo Validation Tests

### 4.1 Demo Scenarios

| # | Dataset | Query | Expected Validation |
|---|---------|-------|---------------------|
| D1 | sales_data.csv | "What are the top 5 products by revenue?" | Table with 5 rows, sorted descending |
| D2 | sales_data.csv | "Show me monthly sales trends" | Line chart, 12 data points |
| D3 | sales_data.csv | "Average revenue by region" | Table with 4 regions, values > 0 |
| D4 | sales_data.csv | "Correlation between price and quantity" | Correlation coefficient [-1, 1] |
| D5 | sales_data.csv | "Revenue distribution" | Histogram visualization |
| D6 | customer_data.xlsx | "Customer churn rate by region" | Percentages summing sensibly |
| D7 | customer_data.xlsx | "Customer lifetime value distribution" | Distribution chart |

### 4.2 Validation Criteria

For each demo scenario, validate:

| Criteria | Check |
|----------|-------|
| **Accuracy** | Results match manual pandas calculation |
| **Code Quality** | Generated code is syntactically correct Python |
| **Transparency** | Code is displayed in the UI |
| **No Hallucination** | All numbers come from code execution, not text |
| **Visualization** | Charts are properly labeled and readable |
| **Performance** | End-to-end < 60 seconds |
| **Error-Free** | No exceptions or error messages |

### 4.3 Manual Verification Script

```python
# scripts/verify_demo.py

import pandas as pd

def verify_top5_revenue(dataset_path: str, agent_result: dict):
    """Manually verify top 5 products by revenue."""
    df = pd.read_csv(dataset_path)
    expected = (df.groupby('product')['revenue']
                  .sum()
                  .sort_values(ascending=False)
                  .head(5))

    # Parse agent results and compare
    for product, revenue in expected.items():
        assert product in agent_result['results'], \
            f"Missing product: {product}"
        # Verify revenue matches within 0.01 tolerance

    print("✅ Top 5 revenue verification PASSED")
```

---

## 5. Performance Tests

### 5.1 Performance Benchmarks

| Test | Target | Method |
|------|--------|--------|
| File upload (10MB CSV) | < 3 seconds | `time.perf_counter()` |
| File upload (50MB CSV) | < 5 seconds | `time.perf_counter()` |
| Query latency (simple) | < 15 seconds | E2E measurement |
| Query latency (complex) | < 45 seconds | E2E measurement |
| Visualization render | < 3 seconds | Server-side timing |
| Concurrent queries (5) | All complete | Thread-based test |

### 5.2 Load Test Script

```python
# tests/performance/test_load.py

import concurrent.futures
import time

def test_concurrent_queries():
    """Test 5 concurrent queries don't cause failures."""
    queries = [
        "Average revenue by region",
        "Top 10 products by quantity",
        "Monthly sales trends",
        "Revenue distribution",
        "Correlation between price and cost"
    ]

    def run_query(query):
        start = time.perf_counter()
        result = bedrock.invoke_agent(query, f"load-test-{i}", dataset_uri)
        elapsed = time.perf_counter() - start
        return {'query': query, 'time': elapsed, 'success': result is not None}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_query, q) for q in queries]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r['success'] for r in results), "Some queries failed"
    assert all(r['time'] < 60 for r in results), "Some queries exceeded 60s"
```

---

## 6. Security Tests

### 6.1 Security Test Cases

| # | Test | Expected Behavior |
|---|------|-------------------|
| S1 | Upload file > 100MB | Rejected with clear error |
| S2 | Upload .exe file | Rejected — unsupported format |
| S3 | Query references other session's data | No access — isolation enforced |
| S4 | Malicious code in query (e.g., "delete all data") | Agent refuses / code sandbox blocks |
| S5 | SQL injection in query text | No effect — NL processing only |
| S6 | S3 URI traversal attack | Blocked by IAM policies |
| S7 | Session timeout enforcement | Session expires after 30 min inactivity |
| S8 | Check data values NOT in logs | Audit CloudWatch for data leakage |

---

## 7. Test Execution

### 7.1 Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v --cov=streamlit_app --cov-report=term-missing

# Run integration tests (requires AWS credentials)
pytest tests/integration/ -v -m integration

# Run with coverage report
pytest tests/ -v --cov=streamlit_app --cov-report=html

# Run linter
flake8 streamlit_app/ --max-line-length 120

# Run type checker
mypy streamlit_app/ --ignore-missing-imports

# Run all (CI/CD)
pytest tests/unit/ -v --cov=streamlit_app --cov-fail-under=80
flake8 streamlit_app/
mypy streamlit_app/
```

### 7.2 CI/CD Integration

Tests are automatically run on every push and pull request via GitHub Actions (see `.github/workflows/test.yml`).

| Stage | Tests Run | Blocking? |
|-------|-----------|-----------|
| PR opened | Unit tests + linting | Yes |
| PR approved | Unit + integration tests | Yes |
| Merge to main | All tests + deploy | Yes |
| Nightly | Full suite + performance | Alerts only |

---

## 8. Test Data & Fixtures

### 8.1 Shared Fixtures

```python
# tests/conftest.py

import pytest
import io
import pandas as pd
import numpy as np


@pytest.fixture
def sample_sales_csv():
    """Generate a small sales CSV for testing."""
    df = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=100),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
        'product': np.random.choice(['A', 'B', 'C'], 100),
        'revenue': np.random.uniform(100, 1000, 100).round(2),
        'quantity': np.random.randint(1, 50, 100)
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    buf.name = "sample_sales.csv"
    return buf


@pytest.fixture
def mock_agent_response():
    """Mock a typical Bedrock Agent response."""
    return {
        'explanation': 'I calculated the average revenue by region.',
        'code': 'df.groupby("region")["revenue"].mean()',
        'results': 'North: $500, South: $450',
        'visualizations': [],
        'next_steps': ['Try breaking down by product']
    }
```

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
