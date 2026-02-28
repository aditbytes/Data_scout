"""
DataScout — Automated Demo Runner.

Executes a sequence of demo queries against a live DataScout instance
and captures results for validation and demonstration.
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlit_app.config import Config
from streamlit_app.services.bedrock_client import BedrockAgentClient
from streamlit_app.services.s3_handler import S3Handler

# Demo queries to execute in sequence
DEMO_QUERIES = [
    "What are the top 5 products by total revenue?",
    "Show me monthly revenue trends",
    "What is the average revenue by region?",
    "What is the correlation between quantity and revenue?",
    "Show me the profit distribution across categories",
]


def run_demo():
    """Run the complete demo scenario."""
    print("═══════════════════════════════════════════════════════")
    print(" DataScout — Demo Runner")
    print("═══════════════════════════════════════════════════════")

    Config.validate()
    bedrock = BedrockAgentClient()
    s3 = S3Handler()

    # Upload demo dataset
    print("\n→ Uploading demo dataset...")
    import uuid
    session_id = f"demo-{uuid.uuid4().hex[:8]}"

    from tests.fixtures.mock_responses import create_test_csv
    csv_file = create_test_csv(rows=500)
    dataset_uri = s3.upload_dataset(csv_file, session_id)
    print(f"  Uploaded to: {dataset_uri}")

    # Execute queries
    results = []
    for i, query in enumerate(DEMO_QUERIES, 1):
        print(f"\n{'─' * 60}")
        print(f"  Query {i}/{len(DEMO_QUERIES)}: {query}")
        print(f"{'─' * 60}")

        start = time.perf_counter()
        try:
            response = bedrock.invoke_agent(query, session_id, dataset_uri)
            elapsed = time.perf_counter() - start

            results.append({
                'query': query,
                'success': True,
                'time_s': round(elapsed, 2),
                'has_code': bool(response.get('code')),
                'has_viz': len(response.get('visualizations', [])) > 0
            })

            print(f"  ✅ Success ({elapsed:.2f}s)")
            if response.get('code'):
                print(f"  📝 Code generated: {len(response['code'])} chars")
            if response.get('visualizations'):
                print(f"  📊 Visualizations: {len(response['visualizations'])}")

        except Exception as e:
            elapsed = time.perf_counter() - start
            results.append({
                'query': query,
                'success': False,
                'time_s': round(elapsed, 2),
                'error': str(e)
            })
            print(f"  ❌ Failed ({elapsed:.2f}s): {str(e)}")

    # Print summary
    print(f"\n{'═' * 60}")
    print(" Demo Summary")
    print(f"{'═' * 60}")
    passed = sum(1 for r in results if r['success'])
    print(f"  Total:  {len(results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {len(results) - passed}")
    print(f"  Avg Time: {sum(r['time_s'] for r in results) / len(results):.2f}s")

    # Cleanup
    print("\n→ Cleaning up session data...")
    s3.delete_session_data(session_id)
    print("  ✅ Cleanup complete.")

    return all(r['success'] for r in results)


if __name__ == '__main__':
    success = run_demo()
    sys.exit(0 if success else 1)
