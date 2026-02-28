"""
DataScout — Shared Test Fixtures.

Provides reusable fixtures for unit and integration tests including
sample datasets, mock responses, and preconfigured service instances.
"""

import io
import uuid

import pytest
import numpy as np
import pandas as pd


@pytest.fixture
def sample_sales_csv():
    """Generate a small sales CSV for testing.

    Returns:
        BytesIO object with CSV data and a .name attribute.
    """
    np.random.seed(42)
    df = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=100).astype(str),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
        'product': np.random.choice(['Widget A', 'Widget B', 'Gadget X'], 100),
        'category': np.random.choice(['Electronics', 'Hardware', 'Software'], 100),
        'revenue': np.random.uniform(100, 10000, 100).round(2),
        'quantity': np.random.randint(1, 100, 100),
        'cost': np.random.uniform(50, 5000, 100).round(2),
    })
    df['profit'] = (df['revenue'] - df['cost']).round(2)

    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    buf.name = "sample_sales.csv"
    return buf


@pytest.fixture
def sample_json_data():
    """Generate a small JSON dataset for testing.

    Returns:
        BytesIO object with JSON data and a .name attribute.
    """
    data = [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "Boston"},
        {"name": "Charlie", "age": 35, "city": "Chicago"},
    ]
    import json
    buf = io.BytesIO(json.dumps(data).encode())
    buf.name = "test_data.json"
    return buf


@pytest.fixture
def mock_agent_response():
    """Mock a typical Bedrock Agent response.

    Returns:
        Dict with explanation, code, results, visualizations, and next_steps.
    """
    return {
        'explanation': 'I calculated the average revenue by region.',
        'code': 'df.groupby("region")["revenue"].mean()',
        'results': '| Region | Avg Revenue |\n|--------|-------------|\n| North | $5,234.56 |\n| South | $4,890.12 |',
        'visualizations': [],
        'next_steps': ['Try breaking down by product category']
    }


@pytest.fixture
def session_id():
    """Generate a test session ID.

    Returns:
        UUID string for test sessions.
    """
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def oversized_file():
    """Create a file that exceeds the size limit.

    Returns:
        BytesIO object > 100 MB.
    """
    content = b"x" * (101 * 1024 * 1024)
    buf = io.BytesIO(content)
    buf.name = "oversized.csv"
    return buf


@pytest.fixture
def unsupported_file():
    """Create a file with an unsupported format.

    Returns:
        BytesIO object with .pdf extension.
    """
    buf = io.BytesIO(b"fake pdf content")
    buf.name = "report.pdf"
    return buf
