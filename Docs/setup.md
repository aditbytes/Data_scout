# DataScout — Setup Guide

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Prerequisites

### 1.1 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.9+ | 3.11 |
| RAM | 2 GB | 4 GB |
| Disk Space | 500 MB | 1 GB |
| OS | macOS / Linux / Windows | macOS / Linux |
| Network | Internet access | Low latency to AWS |

### 1.2 AWS Account Requirements

- Active AWS account with billing enabled
- IAM user or role with permissions to create:
  - S3 buckets
  - IAM roles and policies
  - Bedrock Agent and Alias
  - App Runner services (optional, for production)
  - CloudWatch log groups
- Access to **Claude 3.5 Sonnet** model in Amazon Bedrock (request access in the AWS Console → Bedrock → Model Access)

### 1.3 Required Tools

```bash
# Verify installations
python3 --version    # 3.9+
pip3 --version       # 21+
aws --version        # 2.x
git --version        # 2.x
docker --version     # 20+ (optional, for containerized deployment)
```

---

## 2. Local Development Setup

### 2.1 Clone & Virtual Environment

```bash
# Clone the repository
git clone https://github.com/org/datascout.git
cd datascout

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install production dependencies
pip install -r requirements.txt

# Install dev dependencies (includes test & lint tools)
pip install -r requirements-dev.txt
```

### 2.2 Environment Configuration

```bash
# Copy the template
cp .env.example .env
```

Edit `.env` with your values:

```env
# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=datascout-storage

# Bedrock Agent (filled after Step 3)
BEDROCK_AGENT_ID=<your-agent-id>
BEDROCK_AGENT_ALIAS_ID=<your-alias-id>

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
MAX_FILE_SIZE_MB=100
MAX_CONCURRENT_QUERIES=5
```

### 2.3 AWS Credentials

Configure AWS credentials using one of these methods:

**Option A: AWS CLI (Recommended for local dev)**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_DEFAULT_REGION=us-east-1
```

**Option C: IAM Role (Recommended for production)**
Attach an IAM instance role to your EC2/App Runner service.

---

## 3. AWS Resource Provisioning

### 3.1 Create S3 Bucket

```bash
./scripts/create_buckets.sh datascout-storage us-east-1
```

This creates an S3 bucket with:
- ✅ AES-256 server-side encryption
- ✅ Versioning enabled
- ✅ Public access blocked
- ✅ Lifecycle rules (auto-delete sessions after 7 days, archive logs after 7 days)

**Manual alternative:**
```bash
aws s3 mb s3://datascout-storage --region us-east-1
```

### 3.2 Create IAM Roles

```bash
./scripts/create_iam_roles.sh datascout-storage
```

This creates two IAM roles:
1. **DataScout-AppRunnerRole** — for the Streamlit app (Bedrock, S3, CloudWatch access)
2. **DataScout-BedrockAgentRole** — for the Bedrock Agent (S3 read access)

### 3.3 Create Bedrock Agent

```bash
./scripts/setup_agent.sh
```

This script:
1. Creates a Bedrock Agent named `DataScout-Analyst`
2. Configures it with Claude 3.5 Sonnet
3. Sets detailed analysis instructions
4. Creates a `PRODUCTION` alias
5. Outputs the Agent ID and Alias ID

**Copy the IDs into your `.env` file:**
```env
BEDROCK_AGENT_ID=<output-agent-id>
BEDROCK_AGENT_ALIAS_ID=<output-alias-id>
```

### 3.4 Enable Code Interpreter

> ⚠️ **Manual Step Required** — Code Interpreter must be enabled in the AWS Console.

1. Go to **AWS Console → Amazon Bedrock → Agents**
2. Select the `DataScout-Analyst` agent
3. Click **Edit** → **Action groups**
4. Enable **Code Interpreter**
5. Click **Save** → **Prepare**

---

## 4. Running the Application

### 4.1 Start Locally

> **Important:** Always activate the virtual environment before running the app, or use the venv's `streamlit` directly. Dependencies like `boto3`, `pandas`, and `openpyxl` are installed inside the venv, not globally.

```bash
# Option A — activate venv first, then run
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows
streamlit run streamlit_app/app.py

# Option B — run directly via venv (no activation needed)
venv/bin/streamlit run streamlit_app/app.py
```

The app will open at **http://localhost:8501**.

### 4.2 Start with Custom Port

```bash
source venv/bin/activate
streamlit run streamlit_app/app.py --server.port 8080
```

### 4.3 Start in Docker

```bash
# Build image
docker build -t datascout-frontend .

# Run container
docker run -p 8501:8501 \
  -e AWS_REGION=us-east-1 \
  -e S3_BUCKET=datascout-storage \
  -e BEDROCK_AGENT_ID=<your-id> \
  -e BEDROCK_AGENT_ALIAS_ID=<your-alias-id> \
  datascout-frontend
```

---

## 5. Running Tests

```bash
# Activate venv first
source venv/bin/activate

# Unit tests only
python -m pytest tests/unit/ -v

# Unit tests with coverage
python -m pytest tests/unit/ -v --cov=streamlit_app --cov-report=term-missing

# Integration tests (requires live AWS)
python -m pytest tests/integration/ -v -m integration

# All non-integration tests
python -m pytest tests/ -v -m "not integration"

# Linting
flake8 streamlit_app/ tests/

# Type checking
mypy streamlit_app/ --ignore-missing-imports

# Code formatting check
black --check streamlit_app/ tests/
isort --check-only --profile black streamlit_app/ tests/
```

---

## 6. Production Deployment (App Runner)

### 6.1 Deploy via CloudFormation

```bash
./cloudformation/scripts/deploy.sh datascout-prod prod
```

### 6.2 Deploy via GitHub Actions

1. Add these GitHub secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `BEDROCK_AGENT_ID`
   - `BEDROCK_AGENT_ALIAS_ID`
   - `S3_BUCKET`
   - `APP_RUNNER_SERVICE_ARN`
2. Push to `main` branch — deployment triggers automatically.

### 6.3 Teardown

```bash
./cloudformation/scripts/teardown.sh datascout-prod
```

---

## 7. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'boto3'` | Running with system Python instead of venv | `source venv/bin/activate` then `streamlit run ...` OR use `venv/bin/streamlit run streamlit_app/app.py` |
| `ModuleNotFoundError: No module named 'openpyxl'` | openpyxl missing from env | Run `pip install -r requirements.txt` inside activated venv |
| `EnvironmentError: Missing required env vars` | `.env` not configured | Copy `.env.example` to `.env` and fill in values |
| `NoCredentialsError` | AWS creds not found | Run `aws configure` or set env vars |
| `AccessDenied` on S3 | IAM role missing permissions | Re-run `scripts/create_iam_roles.sh` |
| `ResourceNotFoundException` (Bedrock) | Agent not prepared | Go to Bedrock Console → Agent → Click **Prepare** |
| Port 8501 in use | Another Streamlit running | Use `--server.port 8080` or kill the existing process |
| File upload fails | File > 100 MB or unsupported format | Use CSV, XLSX, XLS, or JSON under 100 MB |
| Docker build fails | Missing Docker daemon | Install and start Docker Desktop |

---

## 8. Directory Overview

```
datascout/
├── streamlit_app/      → Application source code
│   ├── app.py          → Main entry point
│   ├── config.py       → Configuration
│   ├── components/     → UI components (6 files)
│   ├── services/       → AWS integration (3 files)
│   ├── utils/          → Utilities (4 files)
│   └── assets/         → CSS theme
├── tests/              → Test suite (15 files)
├── cloudformation/     → Infrastructure as Code
├── scripts/            → Operational scripts
├── demo/               → Demo datasets & guide
├── .github/            → CI/CD workflows
├── Docs/               → Documentation (12+ files)
├── requirements.txt    → Production deps
├── Dockerfile          → Container build
└── pyproject.toml      → Project config
```
