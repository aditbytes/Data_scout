# DataScout — Demo Script

## Prerequisites
1. AWS credentials configured (`aws configure`)
2. Bedrock Agent deployed (run `scripts/setup_agent.sh`)
3. S3 bucket created (run `scripts/create_buckets.sh`)
4. `.env` file configured with agent and bucket IDs
5. Virtual environment activated with dependencies installed

## Step 1: Generate Demo Data
```bash
python scripts/seed_demo_data.py
```
This creates 3 demo datasets in `demo/datasets/`:
- `sales_data.csv` — 1,000 rows of sales transactions
- `customer_data.xlsx` — 500 customer records
- `product_catalog.json` — 5 product entries

## Step 2: Start the Application
```bash
streamlit run streamlit_app/app.py
```
Open http://localhost:8501 in your browser.

## Step 3: Demo Walkthrough

### 3.1 Upload Dataset
1. Drag `demo/datasets/sales_data.csv` into the upload zone
2. Verify the dataset info bar shows:
   - ✅ 1,000 rows
   - ✅ 9 columns
   - ✅ Size displayed
3. Expand "Preview Dataset" to verify the data looks correct

### 3.2 Run Demo Queries
Execute these queries one at a time:

| # | Query | Expected |
|---|-------|----------|
| 1 | "What are the top 5 products by total revenue?" | Table with 5 rows, sorted descending |
| 2 | "Show me monthly revenue trends" | Line chart with 12 data points |
| 3 | "What is the average revenue by region?" | Table with 4 regions, values > 0 |
| 4 | "What is the correlation between quantity and revenue?" | Correlation coefficient [-1, 1] |
| 5 | "Show me the profit distribution across categories" | Histogram/distribution chart |

### 3.3 Verify Each Result
For each query, check:
- ✅ **Explanation tab** has a clear approach description
- ✅ **Results tab** shows computed data (no hallucinated numbers)
- ✅ **Code tab** shows the generated Python code
- ✅ **Charts tab** shows visualization (for queries 2, 5)
- ✅ All results appear within 60 seconds

### 3.4 Verify Conversation History
After multiple queries:
- Scroll down to "Query History" section
- Verify all past queries are shown with ✅ status
- Click an expander to review past results

## Step 4: Automated Demo (Optional)
```bash
python scripts/run_demo.py
```
This runs all 5 demo queries programmatically and reports pass/fail.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Missing required environment variables" | Check `.env` file has `BEDROCK_AGENT_ID` |
| Upload fails | Verify S3 bucket exists and IAM role has access |
| Query returns empty | Check Bedrock Agent is prepared (`prepare-agent`) |
| Timeout errors | Try a simpler query or check AWS region |
