"""
DataScout — Demo Dataset Seeder.

Generates realistic demo datasets and uploads them to S3
for testing and demonstration purposes.
"""

import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_sales_dataset(output_path: str = 'demo/datasets/sales_data.csv') -> None:
    """Generate a realistic sales dataset for demo.

    Creates 1000 rows of simulated sales data with dates, regions,
    products, categories, revenue, quantity, cost, and calculated profit.

    Args:
        output_path: File path for the output CSV.
    """
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

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Created {output_path}: {len(df)} rows, {len(df.columns)} columns")


def create_customer_dataset(output_path: str = 'demo/datasets/customer_data.csv') -> None:
    """Generate a customer dataset for demo.

    Args:
        output_path: File path for the output CSV file.
    """
    np.random.seed(123)
    n = 500

    df = pd.DataFrame({
        'customer_id': range(1000, 1000 + n),
        'name': [f'Customer_{i}' for i in range(n)],
        'region': np.random.choice(['North', 'South', 'East', 'West'], n),
        'signup_date': pd.date_range('2023-01-01', periods=n, freq='12h').strftime('%Y-%m-%d'),
        'lifetime_value': np.random.uniform(100, 50000, n).round(2),
        'total_orders': np.random.randint(1, 200, n),
        'churn_risk': np.random.choice(['Low', 'Medium', 'High'], n, p=[0.6, 0.25, 0.15]),
        'active': np.random.choice([True, False], n, p=[0.85, 0.15])
    })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Created {output_path}: {len(df)} rows, {len(df.columns)} columns")


def create_product_catalog(output_path: str = 'demo/datasets/product_catalog.json') -> None:
    """Generate a product catalog for demo.

    Args:
        output_path: File path for the output JSON file.
    """
    products = [
        {"id": "WA001", "name": "Widget A", "category": "Electronics", "price": 29.99, "stock": 1500},
        {"id": "WB002", "name": "Widget B", "category": "Electronics", "price": 49.99, "stock": 800},
        {"id": "GX003", "name": "Gadget X", "category": "Hardware", "price": 149.99, "stock": 350},
        {"id": "GY004", "name": "Gadget Y", "category": "Hardware", "price": 199.99, "stock": 200},
        {"id": "TZ005", "name": "Tool Z", "category": "Software", "price": 99.99, "stock": 5000},
    ]

    import json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(products, f, indent=2)
    print(f"✅ Created {output_path}: {len(products)} products")


if __name__ == '__main__':
    print("═══════════════════════════════════════════════════════")
    print(" DataScout — Seeding Demo Data")
    print("═══════════════════════════════════════════════════════")
    create_sales_dataset()
    create_customer_dataset()
    create_product_catalog()
    print("\n✅ All demo datasets created!")
