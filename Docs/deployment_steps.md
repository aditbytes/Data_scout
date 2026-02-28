# DataScout — Deployment Steps (Beginner Guide)

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Audience:** First-time deployers, junior developers, students  

---

> 💡 **This guide assumes you have ZERO prior experience with AWS or cloud deployment.** Every step is explained in full detail with exact commands, expected outputs, and screenshots descriptions.

---

## Table of Contents

1. [What You Need Before Starting](#1-what-you-need-before-starting)
2. [Step 1: Install Required Tools](#2-step-1-install-required-tools)
3. [Step 2: Create an AWS Account](#3-step-2-create-an-aws-account)
4. [Step 3: Create an IAM User](#4-step-3-create-an-iam-user)
5. [Step 4: Configure AWS CLI](#5-step-4-configure-aws-cli)
6. [Step 5: Clone the Project](#6-step-5-clone-the-project)
7. [Step 6: Set Up Python Environment](#7-step-6-set-up-python-environment)
8. [Step 7: Create S3 Bucket](#8-step-7-create-s3-bucket)
9. [Step 8: Create IAM Roles](#9-step-8-create-iam-roles)
10. [Step 9: Enable Bedrock Model Access](#10-step-9-enable-bedrock-model-access)
11. [Step 10: Create Bedrock Agent](#11-step-10-create-bedrock-agent)
12. [Step 11: Enable Code Interpreter](#12-step-11-enable-code-interpreter)
13. [Step 12: Configure Environment File](#13-step-12-configure-environment-file)
14. [Step 13: Run Locally & Test](#14-step-13-run-locally--test)
15. [Step 14: Run the Test Suite](#15-step-14-run-the-test-suite)
16. [Step 15: Build Docker Image](#16-step-15-build-docker-image)
17. [Step 16: Deploy to AWS App Runner](#17-step-16-deploy-to-aws-app-runner)
18. [Step 17: Set Up CI/CD](#18-step-17-set-up-cicd)
19. [Step 18: Post-Deployment Verification](#19-step-18-post-deployment-verification)
20. [Step 19: Monitoring & Maintenance](#20-step-19-monitoring--maintenance)
21. [Cost Estimate](#21-cost-estimate)
22. [Teardown (Delete Everything)](#22-teardown-delete-everything)
23. [Troubleshooting A-Z](#23-troubleshooting-a-z)

---

## 1. What You Need Before Starting

Before you begin, make sure you have:

- [ ] A computer with macOS, Linux, or Windows
- [ ] Internet connection
- [ ] A credit/debit card (for AWS account — free tier available)
- [ ] About 2–3 hours of time
- [ ] A text editor (VS Code recommended — [download here](https://code.visualstudio.com/))

---

## 2. Step 1: Install Required Tools

### 1.1 Install Python 3.11

**macOS:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Verify installation
python3 --version
# Expected output: Python 3.11.x
```

**Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.11.x
3. Run the installer
4. ⚠️ **CHECK the box** "Add Python to PATH" during installation
5. Open Command Prompt and verify:
```cmd
python --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y
python3.11 --version
```

### 1.2 Install Git

**macOS:**
```bash
brew install git
git --version
# Expected: git version 2.x.x
```

**Windows:**
1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Run installer with default options
3. Verify in Command Prompt: `git --version`

**Linux:**
```bash
sudo apt install git -y
```

### 1.3 Install AWS CLI v2

**macOS:**
```bash
# Download and install
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify
aws --version
# Expected: aws-cli/2.x.x
```

**Windows:**
1. Download from [aws.amazon.com/cli](https://aws.amazon.com/cli/)
2. Run the MSI installer
3. Verify in Command Prompt: `aws --version`

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

### 1.4 Install Docker (Optional — for containerized deployment)

**macOS:**
1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. Drag to Applications → Open
3. Wait for Docker to start (whale icon in menu bar)
4. Verify: `docker --version`

**Windows:**
1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Install and restart if prompted
3. Verify: `docker --version`

---

## 3. Step 2: Create an AWS Account

> 💰 **Cost:** AWS Free Tier covers most services for 12 months. Expected cost for DataScout: **$5–15/month** beyond free tier.

1. Go to [aws.amazon.com](https://aws.amazon.com/)
2. Click **"Create an AWS Account"**
3. Enter your email address and choose an account name
4. Verify your email
5. Enter your credit/debit card information
6. Choose the **Basic Support (Free)** plan
7. Complete setup

**Expected time:** 10–15 minutes

---

## 4. Step 3: Create an IAM User

> 🔐 **Why?** Never use your root AWS account for development. Create a separate IAM user with limited permissions.

### 4.1 Open IAM Console

1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. In the search bar at the top, type **"IAM"** and click on **IAM**

### 4.2 Create User

1. Click **"Users"** in the left sidebar
2. Click **"Create user"**
3. Username: `datascout-developer`
4. Check **"Provide user access to the AWS Management Console"** (optional)
5. Click **Next**

### 4.3 Set Permissions

1. Select **"Attach policies directly"**
2. Search for and check these policies:
   - `AmazonS3FullAccess`
   - `AmazonBedrockFullAccess`
   - `IAMFullAccess`
   - `AWSAppRunnerFullAccess`
   - `CloudWatchFullAccess`
3. Click **Next** → **Create user**

### 4.4 Create Access Keys

1. Click on the newly created user `datascout-developer`
2. Go to the **"Security credentials"** tab
3. Scroll down to **"Access keys"**
4. Click **"Create access key"**
5. Select **"Command Line Interface (CLI)"**
6. Click **Next** → **Create access key**
7. ⚠️ **IMPORTANT:** Download the `.csv` file or copy both keys NOW. You will **never see the Secret Access Key again**.

```
Access Key ID:     AKIA...............
Secret Access Key: wJalrX...........
```

> 🛡️ **NEVER** share these keys, commit them to Git, or put them in code files.

---

## 5. Step 4: Configure AWS CLI

Open your terminal and run:

```bash
aws configure
```

You'll be prompted for 4 values. Enter them one by one:

```
AWS Access Key ID [None]: AKIA...............    ← paste your Access Key ID
AWS Secret Access Key [None]: wJalrX..........  ← paste your Secret Access Key
Default region name [None]: us-east-1           ← type us-east-1
Default output format [None]: json              ← type json
```

### Verify it works:

```bash
aws sts get-caller-identity
```

**Expected output:**
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/datascout-developer"
}
```

If you see your account info, AWS CLI is configured correctly! ✅

---

## 6. Step 5: Clone the Project

```bash
# Navigate to where you want the project
cd ~/Projects    # or any folder you prefer

# Clone the repository
git clone https://github.com/org/datascout.git

# Enter the project directory
cd datascout
```

**Verify the project structure:**
```bash
ls -la
```

You should see:
```
.env.example
.flake8
.github/
.gitignore
Dockerfile
Docs/
LICENSE
README.md
cloudformation/
demo/
pyproject.toml
requirements-dev.txt
requirements.txt
scripts/
streamlit_app/
tests/
```

---

## 7. Step 6: Set Up Python Environment

### 7.1 Create Virtual Environment

```bash
# Create a virtual environment called 'venv'
python3 -m venv venv
```

> 💡 **What is a virtual environment?** It's an isolated Python installation so this project's packages don't interfere with other projects on your computer.

### 7.2 Activate Virtual Environment

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

Your terminal prompt should now show `(venv)` at the beginning:
```
(venv) ~/Projects/datascout $
```

### 7.3 Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (testing, linting)
pip install -r requirements-dev.txt
```

**Expected output:** Lines ending with `Successfully installed streamlit-1.xx boto3-1.xx pandas-2.xx ...`

### 7.4 Verify Installation

```bash
python3 -c "import streamlit; import boto3; import pandas; print('All packages installed ✅')"
```

---

## 8. Step 7: Create S3 Bucket

The S3 bucket stores uploaded datasets and generated artifacts.

### Option A: Using the script (recommended)

```bash
chmod +x scripts/create_buckets.sh
./scripts/create_buckets.sh datascout-storage us-east-1
```

**Expected output:**
```
═══════════════════════════════════════════════════════
 DataScout — S3 Bucket Setup
 Bucket: datascout-storage
 Region: us-east-1
═══════════════════════════════════════════════════════
→ Creating S3 bucket...
→ Enabling versioning...
→ Enabling server-side encryption...
→ Blocking public access...
→ Setting lifecycle rules...

✅ S3 bucket 'datascout-storage' setup complete!
```

### Option B: Using the AWS Console (manual)

1. Go to [S3 Console](https://s3.console.aws.amazon.com/)
2. Click **"Create bucket"**
3. Bucket name: `datascout-storage` (must be globally unique — add your initials, e.g., `datascout-storage-pk123`)
4. Region: `US East (N. Virginia) us-east-1`
5. **Block all public access:** ✅ Keep checked
6. **Bucket Versioning:** Enable
7. **Default encryption:** Amazon S3-managed keys (SSE-S3)
8. Click **"Create bucket"**

### Verify the bucket exists:

```bash
aws s3 ls | grep datascout
```

**Expected output:**
```
2026-02-24 23:00:00 datascout-storage
```

> ⚠️ If your bucket name was different (e.g., `datascout-storage-pk123`), remember it — you'll use it in Step 12.

---

## 9. Step 8: Create IAM Roles

IAM roles define what the application is allowed to do in AWS.

### Using the script:

```bash
chmod +x scripts/create_iam_roles.sh
./scripts/create_iam_roles.sh datascout-storage
```

**Expected output:**
```
═══════════════════════════════════════════════════════
 DataScout — IAM Role Setup
═══════════════════════════════════════════════════════
→ Creating App Runner execution role...
→ Attaching Bedrock access...
→ Attaching S3 access policy...
→ Attaching CloudWatch policy...
→ Creating Bedrock Agent role...
→ Attaching S3 read access for Code Interpreter...

✅ IAM roles created successfully!
```

### Verify roles exist:

```bash
aws iam get-role --role-name DataScout-AppRunnerRole --query 'Role.Arn' --output text
aws iam get-role --role-name DataScout-BedrockAgentRole --query 'Role.Arn' --output text
```

Each command should print an ARN like:
```
arn:aws:iam::123456789012:role/DataScout-AppRunnerRole
```

---

## 10. Step 9: Enable Bedrock Model Access

> ⚠️ **This is a manual step** — it cannot be done via CLI.

1. Go to [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Make sure you're in the **us-east-1** region (top-right dropdown)
3. In the left sidebar, click **"Model access"**
4. Click **"Manage model access"**
5. Find **"Anthropic"** → **"Claude 3.5 Sonnet v2"**
6. Check the box next to it
7. Click **"Request model access"**
8. Accept the terms and submit

**Wait time:** Usually instant, but can take up to 24 hours for first-time users.

### Verify model access:

```bash
aws bedrock list-foundation-models \
    --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20241022-v2:0'].modelId" \
    --output text
```

**Expected output:**
```
anthropic.claude-3-5-sonnet-20241022-v2:0
```

---

## 11. Step 10: Create Bedrock Agent

The Bedrock Agent is the AI brain that processes your queries.

### Using the script:

```bash
chmod +x scripts/setup_agent.sh
./scripts/setup_agent.sh
```

**Expected output:**
```
═══════════════════════════════════════════════════════
 DataScout — Bedrock Agent Setup
═══════════════════════════════════════════════════════
→ Creating Bedrock Agent...
  Agent ID: ABCDEF1234
→ Preparing agent...
  Agent prepared.
→ Creating production alias...
  Alias ID: XYZ789

═══════════════════════════════════════════════════════
 ✅ Setup Complete!
═══════════════════════════════════════════════════════

 Add these to your .env file:
  BEDROCK_AGENT_ID=ABCDEF1234
  BEDROCK_AGENT_ALIAS_ID=XYZ789
```

> 📝 **Write down** the `BEDROCK_AGENT_ID` and `BEDROCK_AGENT_ALIAS_ID` — you need them in Step 12.

---

## 12. Step 11: Enable Code Interpreter

> ⚠️ **This is a manual step** — Code Interpreter must be enabled in the AWS Console.

1. Go to [Bedrock Console → Agents](https://console.aws.amazon.com/bedrock/home#/agents)
2. Click on **"DataScout-Analyst"**
3. Scroll down and click **"Edit in Agent builder"**
4. In the left panel, find **"Action groups"**
5. Click **"Add"** → Select **"Code Interpreter"**
6. Enable it and click **Save**
7. Click **"Prepare"** at the top of the page
8. Wait for status to change to **"Prepared"**

### Verify the agent is ready:

```bash
aws bedrock-agent get-agent \
    --agent-id <YOUR_AGENT_ID> \
    --query 'agent.agentStatus' \
    --output text
```

**Expected output:** `PREPARED`

---

## 13. Step 12: Configure Environment File

```bash
# Copy the template
cp .env.example .env
```

Open `.env` in your text editor and fill in your values:

```env
# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=datascout-storage              ← your bucket name from Step 7

# Bedrock Agent (from Step 10 output)
BEDROCK_AGENT_ID=ABCDEF1234              ← your Agent ID
BEDROCK_AGENT_ALIAS_ID=XYZ789           ← your Alias ID

# Application Settings (keep defaults)
DEBUG=false
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
MAX_FILE_SIZE_MB=100
MAX_CONCURRENT_QUERIES=5
```

Save the file.

### Verify config loads correctly:

```bash
python3 -c "
from streamlit_app.config import Config
Config.validate()
print(f'Region:    {Config.AWS_REGION}')
print(f'Bucket:    {Config.S3_BUCKET}')
print(f'Agent ID:  {Config.BEDROCK_AGENT_ID}')
print('✅ Configuration valid!')
"
```

**Expected output:**
```
Region:    us-east-1
Bucket:    datascout-storage
Agent ID:  ABCDEF1234
✅ Configuration valid!
```

---

## 14. Step 13: Run Locally & Test

### 14.1 Generate Demo Data

```bash
python3 scripts/seed_demo_data.py
```

**Expected output:**
```
═══════════════════════════════════════════════════════
 DataScout — Seeding Demo Data
═══════════════════════════════════════════════════════
✅ Created demo/datasets/sales_data.csv: 1000 rows, 9 columns
✅ Created demo/datasets/customer_data.csv: 500 rows, 8 columns
✅ Created demo/datasets/product_catalog.json: 5 products

✅ All demo datasets created!
```

### 14.2 Start the Application

```bash
streamlit run streamlit_app/app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.xxx:8501
```

### 14.3 Test the Application

1. Open **http://localhost:8501** in your browser
2. You should see the DataScout interface with:
   - 🔬 **DataScout** header
   - 📁 Upload section
   - 💬 Query input (disabled until dataset uploaded)

3. **Upload test dataset:**
   - Drag `demo/datasets/sales_data.csv` into the upload area
   - Verify: "✅ Dataset loaded: sales_data.csv — 1,000 rows, 9 columns"

4. **Run a test query:**
   - Type: `What are the top 5 products by total revenue?`
   - Click **🔍 Ask**
   - Wait 10–30 seconds for the response
   - Verify all 4 tabs have content (Explanation, Results, Code, Charts)

5. **Stop the server:** Press `Ctrl + C` in the terminal

---

## 15. Step 14: Run the Test Suite

### 15.1 Unit Tests (no AWS needed)

```bash
pytest tests/unit/ -v --cov=streamlit_app --cov-report=term-missing
```

**Expected output:**
```
tests/unit/test_bedrock_client.py::TestBedrockAgentClient::test_invoke_agent_success PASSED
tests/unit/test_bedrock_client.py::TestBedrockAgentClient::test_parse_response_extracts_code PASSED
...
==================== X passed in Y.YYs ====================

---------- coverage: ... ----------
Name                                         Stmts   Miss  Cover
streamlit_app/config.py                         25      3    88%
streamlit_app/utils/validators.py               30      2    93%
...
TOTAL                                          XXX     XX    XX%
```

### 15.2 Lint Check

```bash
flake8 streamlit_app/ tests/ --max-line-length 120
```

**Expected:** No output = no lint errors ✅

### 15.3 Integration Tests (requires live AWS)

```bash
pytest tests/integration/ -v -m integration
```

### 15.4 Automated Demo

```bash
python3 scripts/run_demo.py
```

---

## 16. Step 15: Build Docker Image

> 💡 **Skip this step** if you don't need Docker deployment.

### 16.1 Build

```bash
docker build -t datascout-frontend .
```

**Expected:** Lines ending with `Successfully built ...` and `Successfully tagged datascout-frontend:latest`

### 16.2 Run Locally in Docker

```bash
docker run -p 8501:8501 \
  -e AWS_REGION=us-east-1 \
  -e S3_BUCKET=datascout-storage \
  -e BEDROCK_AGENT_ID=ABCDEF1234 \
  -e BEDROCK_AGENT_ALIAS_ID=XYZ789 \
  -e AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
  -e AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key) \
  datascout-frontend
```

Open **http://localhost:8501** — the app should work identically to Step 13.

### 16.3 Stop the Container

```bash
docker ps                     # Find the CONTAINER ID
docker stop <CONTAINER_ID>    # Stop it
```

---

## 17. Step 16: Deploy to AWS App Runner

### Option A: Using CloudFormation (recommended)

```bash
chmod +x cloudformation/scripts/deploy.sh
./cloudformation/scripts/deploy.sh datascout-prod prod
```

**Expected output:**
```
═══════════════════════════════════════════════════════
 DataScout — Deploying Stack: datascout-prod
 Environment: prod
═══════════════════════════════════════════════════════
→ Validating CloudFormation template...
→ Deploying stack...
→ Stack outputs:
----------------------------------------------
|  OutputKey       |  OutputValue             |
|  AppUrl          |  abcdef.us-east-1...     |
|  BucketName      |  datascout-storage-...   |
----------------------------------------------

✅ Deployment complete!
```

Copy the **AppUrl** — that's your live application URL!

### Option B: Using AWS Console (manual)

1. Go to [App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Click **"Create service"**
3. Source: **Source code repository**
4. Connect to your GitHub repo
5. Branch: `main`
6. Build settings:
   - Runtime: **Python 3.11**
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run streamlit_app/app.py --server.port 8080 --server.address 0.0.0.0 --server.headless true`
   - Port: `8080`
7. Instance: 1 vCPU, 2 GB RAM
8. Instance role: `DataScout-AppRunnerRole`
9. Add environment variables:
   - `AWS_REGION` = `us-east-1`
   - `S3_BUCKET` = `datascout-storage`
   - `BEDROCK_AGENT_ID` = your agent ID
   - `BEDROCK_AGENT_ALIAS_ID` = your alias ID
10. Click **"Create & deploy"**
11. Wait 5–10 minutes until status shows **"Running"**
12. Click the **Default domain** URL to access your app

---

## 18. Step 17: Set Up CI/CD

### 18.1 Add GitHub Secrets

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** and add each:

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret key |
| `BEDROCK_AGENT_ID` | Your Bedrock Agent ID |
| `BEDROCK_AGENT_ALIAS_ID` | Your Bedrock Alias ID |
| `S3_BUCKET` | Your S3 bucket name |
| `APP_RUNNER_SERVICE_ARN` | Your App Runner service ARN |

### 18.2 How It Works

After setup, every push to the `main` branch will:

```
Push to main
    ↓
Run linter (flake8) → Run type checker (mypy) → Run unit tests (pytest)
    ↓ (all pass)
Deploy to App Runner automatically
```

The workflows are already defined in `.github/workflows/`.

---

## 19. Step 18: Post-Deployment Verification

After deployment, run through this checklist:

### Basic Health Check

```bash
# Replace with your App Runner URL
curl -s https://<your-app-url>/_stcore/health
```

**Expected:** Returns `ok`

### Functional Verification

1. Open your App Runner URL in a browser
2. Upload `demo/datasets/sales_data.csv`
3. Run: `"What are the top 5 products by total revenue?"`
4. Verify you get a response with code and results
5. Run 2 more queries to test session continuity
6. Check that Query History shows all 3 queries

### Log Verification

```bash
aws logs tail /datascout/prod/app --since 5m
```

You should see structured JSON log entries for upload and query events.

---

## 20. Step 19: Monitoring & Maintenance

### Daily Checks
- [ ] App Runner service status is **"Running"**
- [ ] No error logs in CloudWatch
- [ ] S3 bucket size is not growing unexpectedly

### Weekly Checks
- [ ] Review CloudWatch metrics (latency, error rate)
- [ ] Check S3 lifecycle rules are cleaning up old data
- [ ] Review CI/CD pipeline runs for failures

### Monthly Checks
- [ ] Review AWS cost report
- [ ] Update dependencies: `pip install --upgrade -r requirements.txt`
- [ ] Review and rotate IAM access keys

---

## 21. Cost Estimate

| Service | Free Tier | Estimated Monthly Cost |
|---------|-----------|----------------------|
| **App Runner** | None | $5–15 (1 vCPU, 2 GB, running 24/7) |
| **Amazon Bedrock** | Pay per use | $1–10 (depends on query volume) |
| **S3** | 5 GB free | $0.01–0.50 |
| **CloudWatch** | 5 GB logs free | $0–1 |
| **Total** | | **$6–27/month** |

> 💡 **To minimize costs:** Pause the App Runner service when not in use.

---

## 22. Teardown (Delete Everything)

If you want to remove all AWS resources:

```bash
# Using the teardown script
chmod +x cloudformation/scripts/teardown.sh
./cloudformation/scripts/teardown.sh datascout-prod
```

### Manual teardown (if script fails):

```bash
# 1. Empty and delete S3 bucket
aws s3 rm s3://datascout-storage --recursive
aws s3 rb s3://datascout-storage

# 2. Delete Bedrock Agent
aws bedrock-agent delete-agent-alias \
    --agent-id <AGENT_ID> --agent-alias-id <ALIAS_ID>
aws bedrock-agent delete-agent --agent-id <AGENT_ID>

# 3. Delete IAM roles
aws iam delete-role-policy --role-name DataScout-AppRunnerRole --policy-name DataScoutS3Access
aws iam delete-role-policy --role-name DataScout-AppRunnerRole --policy-name DataScoutCloudWatch
aws iam detach-role-policy --role-name DataScout-AppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
aws iam delete-role --role-name DataScout-AppRunnerRole

aws iam delete-role-policy --role-name DataScout-BedrockAgentRole --policy-name BedrockS3Access
aws iam delete-role --role-name DataScout-BedrockAgentRole

# 4. Delete App Runner service (if created manually)
aws apprunner delete-service --service-arn <SERVICE_ARN>

# 5. Delete CloudWatch log group
aws logs delete-log-group --log-group-name /datascout/prod/app
```

---

## 23. Troubleshooting A-Z

| # | Problem | Cause | Solution |
|---|---------|-------|----------|
| 1 | `aws configure` — "command not found" | AWS CLI not installed | Go back to Step 1.3 |
| 2 | `aws sts get-caller-identity` — error | Bad credentials | Re-run `aws configure` with correct keys |
| 3 | `make_bucket failed: BucketAlreadyExists` | Bucket name taken globally | Add a suffix: `datascout-storage-pk123` |
| 4 | `AccessDeniedException` on Bedrock | Model access not granted | Complete Step 9 (Enable Model Access) |
| 5 | `ResourceNotFoundException` on Agent | Agent not prepared | Go to Bedrock Console → Agent → Click "Prepare" |
| 6 | `EnvironmentError: Missing required env vars` | `.env` not configured | Complete Step 12 |
| 7 | `ModuleNotFoundError: streamlit` | venv not activated | Run `source venv/bin/activate` |
| 8 | `ModuleNotFoundError: boto3` | Dependencies not installed | Run `pip install -r requirements.txt` |
| 9 | Port 8501 already in use | Another Streamlit instance | Kill it: `lsof -ti:8501 \| xargs kill` |
| 10 | Docker build fails | Docker not running | Start Docker Desktop |
| 11 | App Runner deploy stuck | Build error | Check App Runner logs in AWS Console |
| 12 | Query timeout (>60s) | Large dataset or complex query | Try simpler query or smaller dataset |
| 13 | Upload rejected | Wrong format or >100 MB | Use CSV, XLSX, XLS, or JSON under 100 MB |
| 14 | "No code generated" | Query too vague | Be more specific: "What is the average X by Y?" |
| 15 | Charts not showing | Matplotlib issue | Check Code tab for errors, retry query |
| 16 | Session expired | 30 min inactivity | Refresh the page to start a new session |
| 17 | `pip install` fails | Python version mismatch | Use Python 3.9–3.11, not 3.12+ |
| 18 | Git clone fails | No access | Check repo URL or SSH key configuration |
| 19 | Tests fail | Missing dev dependencies | Run `pip install -r requirements-dev.txt` |
| 20 | High AWS bill | App Runner running 24/7 | Pause service when not in use |

---

**🎉 Congratulations!** You've successfully deployed DataScout from scratch!

For day-to-day usage, see [guide.md](guide.md).  
For technical details, see [implementation.md](implementation.md).

---

**Document Generated:** February 24, 2026  
**Author:** DataScout Development Team
