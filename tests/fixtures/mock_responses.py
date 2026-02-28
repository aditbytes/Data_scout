"""
DataScout — Test Fixtures & Mock Response Factories.

Provides factory functions for generating test datasets and
mock AWS service responses for both unit and integration tests.
"""

import io
import json
from typing import Optional

import numpy as np
import pandas as pd


def create_test_csv(rows: int = 100, seed: int = 42) -> io.BytesIO:
    """Create a test CSV dataset with realistic sales data.

    Args:
        rows: Number of rows to generate.
        seed: Random seed for reproducibility.

    Returns:
        BytesIO object containing CSV data with .name attribute.
    """
    np.random.seed(seed)
    regions = ['North', 'South', 'East', 'West']
    products = ['Widget A', 'Widget B', 'Gadget X', 'Gadget Y', 'Tool Z']
    categories = ['Electronics', 'Hardware', 'Software']

    df = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=rows).astype(str),
        'region': np.random.choice(regions, rows),
        'product': np.random.choice(products, rows),
        'category': np.random.choice(categories, rows),
        'revenue': np.random.uniform(100, 10000, rows).round(2),
        'quantity': np.random.randint(1, 100, rows),
        'cost': np.random.uniform(50, 5000, rows).round(2),
    })
    df['profit'] = (df['revenue'] - df['cost']).round(2)

    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    buf.name = "test_sales.csv"
    return buf


def create_test_json(records: int = 30, seed: int = 42) -> io.BytesIO:
    """Create a test JSON dataset.

    Args:
        records: Number of records to generate.
        seed: Random seed for reproducibility.

    Returns:
        BytesIO object containing JSON data with .name attribute.
    """
    np.random.seed(seed)
    data = []
    for i in range(records):
        data.append({
            'id': i + 1,
            'name': f'Customer_{i + 1}',
            'region': np.random.choice(['North', 'South', 'East', 'West']),
            'lifetime_value': round(np.random.uniform(100, 50000), 2),
            'active': bool(np.random.choice([True, False]))
        })

    buf = io.BytesIO(json.dumps(data).encode())
    buf.name = "test_customers.json"
    return buf


def create_test_xlsx(rows: int = 50, seed: int = 42) -> io.BytesIO:
    """Create a test Excel dataset.

    Args:
        rows: Number of rows to generate.
        seed: Random seed for reproducibility.

    Returns:
        BytesIO object containing XLSX data with .name attribute.
    """
    np.random.seed(seed)
    df = pd.DataFrame({
        'product': np.random.choice(['A', 'B', 'C', 'D'], rows),
        'sales': np.random.randint(100, 5000, rows),
        'rating': np.random.uniform(1, 5, rows).round(1)
    })

    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine='openpyxl')
    buf.seek(0)
    buf.name = "test_products.xlsx"
    return buf


def mock_bedrock_response(text: str = "Analysis complete",
                          code: Optional[str] = None) -> dict:
    """Create a mock Bedrock Agent API response.

    Args:
        text: The response text.
        code: Optional Python code to include in the response.

    Returns:
        Dict structured like a Bedrock invoke_agent response.
    """
    if code:
        full_text = f"{text}\n```python\n{code}\n```\nResults generated."
    else:
        full_text = text

    return {
        'completion': [
            {'chunk': {'bytes': full_text.encode('utf-8')}}
        ],
        'sessionId': 'mock-session-id'
    }


def mock_s3_get_response(content: bytes, content_type: str = 'text/csv') -> dict:
    """Create a mock S3 GetObject response.

    Args:
        content: File content bytes.
        content_type: MIME type of the content.

    Returns:
        Dict structured like a boto3 S3 get_object response.
    """
    from unittest.mock import MagicMock
    mock_body = MagicMock()
    mock_body.read.return_value = content
    return {
        'Body': mock_body,
        'ContentType': content_type,
        'ContentLength': len(content)
    }
