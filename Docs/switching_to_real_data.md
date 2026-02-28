# DataScout — Switching from Demo to Real Data

> This guide walks you through every step needed to move DataScout from its
> built-in demo mode (local CSV/XLSX/JSON files, placeholder agent) to a
> production-ready setup backed by **real AWS services and live datasets**.

---

## Table of Contents

1. [Overview — Demo vs Real Mode](#1-overview--demo-vs-real-mode)
2. [Prerequisites](#2-prerequisites)
3. [Step 1 — Provision Real AWS Resources](#step-1--provision-real-aws-resources)
4. [Step 2 — Configure Environment Variables](#step-2--configure-environment-variables)
5. [Step 3 — Prepare Your Bedrock Agent](#step-3--prepare-your-bedrock-agent)
6. [Step 4 — Verify S3 Connectivity](#step-4--verify-s3-connectivity)
7. [Step 5 — Upload Real Datasets](#step-5--upload-real-datasets)
8. [Step 6 — Run & Validate](#step-6--run--validate)
9. [Rollback to Demo Mode](#7-rollback-to-demo-mode)
10. [FAQ & Troubleshooting](#8-faq--troubleshooting)

---

## 1. Overview — Demo vs Real Mode

| Aspect | Demo Mode | Real / Production Mode |
|--------|-----------|------------------------|
| **Datasets** | Pre-generated files in `demo/datasets/` (`sales_data.csv`, `customer_data.csv`, `product_catalog.json`) | Your own enterprise datasets uploaded through the UI |
| **Bedrock Agent** | Placeholder ID (or offline) — no real LLM calls | Live Amazon Bedrock Agent powered by Claude 3.5 Sonnet |
| **S3 Bucket** | Optional / local-only | Dedicated S3 bucket (`datascout-storage` or custom) with SSE-AES256 encryption |
| **IAM Roles** | Not required | Proper IAM roles with least-privilege policies for Bedrock + S3 |
| **Environment** | `.env` with placeholder values | `.env` with real AWS credentials and resource IDs |

---

## 2. Prerequisites

Before switching to real data, ensure you have:

- [ ] **AWS Account** with billing enabled
- [ ] **AWS CLI** installed and configured (`aws configure`)
- [ ] **IAM permissions** to create S3 buckets, Bedrock agents, and IAM roles
- [ ] **Python 3.10+** with project dependencies installed (`pip install -r requirements.txt`)
- [ ] Familiarity with the [Setup Guide](setup.md) and [User Guide](guide.md)

---

## Step 1 — Provision Real AWS Resources

### A. Create the S3 Bucket

Run the provided script to create and configure the S3 bucket:

```bash
bash scripts/create_buckets.sh
```

This creates a bucket with:
- Server-side encryption (AES-256)
- Versioning enabled
- Public access blocked

> **Manual alternative:**
> ```bash
> aws s3 mb s3://your-datascout-bucket --region us-east-1
> aws s3api put-bucket-encryption \
>   --bucket your-datascout-bucket \
>   --server-side-encryption-configuration \
>     '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
> ```

### B. Create IAM Roles

```bash
bash scripts/create_iam_roles.sh
```

This creates roles with policies for:
- S3 read/write access (scoped to your bucket)
- Bedrock Agent invocation permissions

### C. Deploy the Bedrock Agent

```bash
bash scripts/setup_agent.sh
```

After the script completes, note down the **Agent ID** and **Alias ID** — you will need them in the next step.

> **Or deploy via CloudFormation:**
> ```bash
> aws cloudformation deploy \
>   --template-file cloudformation/datascout-stack.yaml \
>   --stack-name datascout-prod \
>   --capabilities CAPABILITY_NAMED_IAM
> ```

---

## Step 2 — Configure Environment Variables

Copy the example file and fill in your **real** values:

```bash
cp .env.example .env
```

Open `.env` and update every placeholder:

```dotenv
# ── AWS Configuration ────────────────────────────────────────────────────────
AWS_REGION=us-east-1                          # your AWS region
S3_BUCKET=your-datascout-bucket               # ← real bucket name

# ── Bedrock Agent ─────────────────────────────────────────────────────────────
BEDROCK_AGENT_ID=ABCDEFGHIJ                   # ← real agent ID from Step 1C
BEDROCK_AGENT_ALIAS_ID=TSTALIASID             # ← real alias ID (or PRODUCTION)

# ── Application Settings ─────────────────────────────────────────────────────
DEBUG=false                                   # set true only for debugging
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
MAX_FILE_SIZE_MB=100                          # adjust for your data sizes
MAX_CONCURRENT_QUERIES=5
```

### Key Differences from Demo `.env`

| Variable | Demo Value | Real Value |
|----------|-----------|------------|
| `BEDROCK_AGENT_ID` | `<your-agent-id>` (placeholder) | Actual 10-character agent ID |
| `BEDROCK_AGENT_ALIAS_ID` | `<your-alias-id>` (placeholder) | Actual alias ID or `PRODUCTION` |
| `S3_BUCKET` | `datascout-storage` (may not exist) | Your provisioned bucket name |
| `DEBUG` | `true` | `false` |

> [!IMPORTANT]
> The app validates `BEDROCK_AGENT_ID` and `S3_BUCKET` on startup. If either is
> missing or empty, you will see a **"Configuration Incomplete"** error in the UI.

---

## Step 3 — Prepare Your Bedrock Agent

Ensure the Bedrock Agent is in **Prepared** status:

```bash
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID \
  --query 'agent.agentStatus'
```

If the status is not `PREPARED`, run:

```bash
aws bedrock-agent prepare-agent --agent-id YOUR_AGENT_ID
```

Wait for the status to change to `PREPARED` (usually < 60 seconds).

---

## Step 4 — Verify S3 Connectivity

Test that the app's IAM role can access the bucket:

```bash
# List bucket contents
aws s3 ls s3://your-datascout-bucket/

# Test upload
echo "test" > /tmp/test.txt
aws s3 cp /tmp/test.txt s3://your-datascout-bucket/test.txt
aws s3 rm s3://your-datascout-bucket/test.txt
```

All three commands should succeed without errors.

---

## Step 5 — Upload Real Datasets

### Option A: Through the UI (Recommended)

1. Start the app: `streamlit run streamlit_app/app.py`
2. Drag-and-drop your dataset into the upload zone
3. The app automatically:
   - Validates format (`.csv`, `.xlsx`, `.xls`, `.json`) and size (≤ 100 MB)
   - Uploads to `s3://your-bucket/datasets/{session_id}/original/{filename}`
   - Extracts metadata (columns, types, row count, nulls)

### Option B: Direct S3 Upload

```bash
aws s3 cp your_real_data.csv s3://your-datascout-bucket/datasets/manual/original/your_real_data.csv
```

> [!NOTE]
> Supported file formats: `.csv`, `.xlsx`, `.xls`, `.json`
> Maximum file size: configured via `MAX_FILE_SIZE_MB` (default: 100 MB)

---

## Step 6 — Run & Validate

Start the application:

```bash
streamlit run streamlit_app/app.py
```

### Validation Checklist

- [ ] App starts without a "Configuration Incomplete" error
- [ ] File upload succeeds and shows row/column count
- [ ] Dataset preview renders correctly
- [ ] A natural-language query returns results with:
  - ✅ Explanation tab
  - ✅ Generated Python code tab
  - ✅ Computed results tab
  - ✅ Visualization (if applicable)
- [ ] Query history accumulates

### Quick Smoke Test Queries

Try these against your real data to confirm end-to-end flow:

```text
"How many rows and columns does this dataset have?"
"Show me the first 10 rows"
"What is the distribution of [your_column_name]?"
```

---

## 7. Rollback to Demo Mode

If you need to revert to demo mode:

1. **Regenerate demo data** (if it was deleted):
   ```bash
   python scripts/seed_demo_data.py
   ```

2. **Reset `.env`** to placeholder values:
   ```bash
   cp .env.example .env
   ```

3. **Use demo datasets** by uploading files from `demo/datasets/` through the UI:
   - `sales_data.csv` — 1,000 sales transactions
   - `customer_data.csv` — 500 customer records
   - `product_catalog.json` — 5 product entries

4. **Run the automated demo** (optional):
   ```bash
   python scripts/run_demo.py
   ```

> [!TIP]
> Keep a backup of your production `.env` before reverting:
> ```bash
> cp .env .env.production.bak
> ```

---

## 8. FAQ & Troubleshooting

### "Missing required environment variables: BEDROCK_AGENT_ID"

Your `.env` file is missing the `BEDROCK_AGENT_ID` value.
→ Follow [Step 2](#step-2--configure-environment-variables) to set it.

### Uploads fail with "Access Denied"

The IAM role attached to your machine or instance lacks `s3:PutObject` permission.
→ Run `scripts/create_iam_roles.sh` or manually attach the S3 policy.

### Agent returns empty or nonsensical results

The Bedrock Agent may not be prepared or may lack access to the dataset.
→ Run `aws bedrock-agent prepare-agent --agent-id YOUR_ID` and retry.

### Query timeouts

By default, the Bedrock client has a 60-second read timeout.
→ Try a simpler query, or ensure your Bedrock Agent's region matches `AWS_REGION` in `.env`.

### "Unsupported format" on upload

Only `.csv`, `.xlsx`, `.xls`, and `.json` are supported.
→ Convert your data to one of these formats before uploading.

### Want to increase the upload size limit?

Edit `MAX_FILE_SIZE_MB` in your `.env` file:

```dotenv
MAX_FILE_SIZE_MB=500
```

---

> **Need more help?** See the full [Setup Guide](setup.md) and [User Guide](guide.md), or open an issue on GitHub.
