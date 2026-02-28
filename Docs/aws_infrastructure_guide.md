# DataScout — AWS Infrastructure Guide (Beginner Friendly)

**Version:** 2.0  
**Last Updated:** February 27, 2026  
**Audience:** First-time deployers, junior developers, hackathon participants  

---

> 💡 **This guide assumes ZERO prior experience with AWS.** Every step includes exact commands, expected outputs, and what to do if something goes wrong.

---

## Table of Contents

1. [Overview — What AWS Services Does DataScout Use?](#1-overview)
2. [Prerequisites — What You Need Before Starting](#2-prerequisites)
3. [Step 1: Install Required Tools](#3-step-1-install-required-tools)
4. [Step 2: Create AWS Account & IAM User](#4-step-2-create-aws-account--iam-user)
5. [Step 3: Configure AWS CLI](#5-step-3-configure-aws-cli)
6. [Step 4: Create Amazon S3 Bucket](#6-step-4-create-amazon-s3-bucket)
7. [Step 5: Create IAM Roles & Policies](#7-step-5-create-iam-roles--policies)
8. [Step 6: Enable Amazon Bedrock Model Access](#8-step-6-enable-amazon-bedrock-model-access)
9. [Step 7: Create Bedrock Agent with Code Interpreter](#9-step-7-create-bedrock-agent-with-code-interpreter)
10. [Step 8: Create Amazon DynamoDB Table](#10-step-8-create-amazon-dynamodb-table)
11. [Step 9: Create AWS Lambda Function](#11-step-9-create-aws-lambda-function)
12. [Step 10: Create Amazon API Gateway](#12-step-10-create-amazon-api-gateway)
13. [Step 11: Configure Environment Variables](#13-step-11-configure-environment-variables)
14. [Step 12: Run the App Locally & Test](#14-step-12-run-the-app-locally--test)
15. [Step 13: Run the Test Suite](#15-step-13-run-the-test-suite)
16. [Step 14: Deploy with CloudFormation (One-Click)](#16-step-14-deploy-with-cloudformation)
17. [Step 15: Deploy to AWS App Runner](#17-step-15-deploy-to-aws-app-runner)
18. [Step 16: Set Up CloudWatch Monitoring](#18-step-16-set-up-cloudwatch-monitoring)
19. [Step 17: Post-Deployment Verification](#19-step-17-post-deployment-verification)
20. [Cost Estimate](#20-cost-estimate)
21. [Teardown — Delete Everything](#21-teardown)
22. [Troubleshooting A–Z](#22-troubleshooting)

---

## 1. Overview

### What AWS Services Does DataScout Use?

DataScout uses **9 AWS services**. Here's what each one does:

```
┌──────────────────────────────────────────────────────────────────┐
│                   DataScout AWS Architecture                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   👤 User → 🖥️ Streamlit App (App Runner)                       │
│                    │                                              │
│                    ├──→ 🤖 Amazon Bedrock (AI Agent)             │
│                    │         └──→ 🐍 Code Interpreter            │
│                    │                                              │
│                    ├──→ 📦 Amazon S3 (File Storage)              │
│                    │                                              │
│                    ├──→ 📊 Amazon DynamoDB (Query History)        │
│                    │                                              │
│                    └──→ ⚡ API Gateway + Lambda (REST API)        │
│                                                                   │
│   Supporting: IAM (Security) • CloudWatch (Logs) • CFN (IaC)    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

| # | AWS Service | What It Does in DataScout | Why We Need It |
|---|-------------|--------------------------|----------------|
| 1 | **Amazon S3** | Stores uploaded datasets (CSV, Excel, JSON) | Secure, encrypted file storage |
| 2 | **Amazon Bedrock** | Runs the AI agent that analyzes data | AI brain — understands questions, writes Python code |
| 3 | **Amazon DynamoDB** | Saves query history and session data | Persistent storage that survives app restarts |
| 4 | **AWS Lambda** | Runs a serverless REST API | Lets other apps call DataScout via HTTP |
| 5 | **Amazon API Gateway** | Routes HTTP requests to Lambda | Provides URL endpoints like `/analyze`, `/health` |
| 6 | **AWS IAM** | Controls who can access what | Security — each service gets minimum permissions |
| 7 | **Amazon CloudWatch** | Collects logs and metrics | Debugging, monitoring, audit trails |
| 8 | **AWS App Runner** | Hosts the Streamlit web app | Serverless hosting — no server management |
| 9 | **AWS CloudFormation** | Deploys all resources from a template | Infrastructure as Code — one-click deployment |

---

## 2. Prerequisites

Before you begin, make sure you have:

- [ ] A computer (macOS, Linux, or Windows)
- [ ] Internet connection
- [ ] A credit/debit card (for AWS — free tier available)
- [ ] About 2–3 hours of time
- [ ] A text editor (VS Code recommended)

---

## 3. Step 1: Install Required Tools

### 1.1 Install Python 3.11

**macOS:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Verify
python3 --version
# Expected: Python 3.11.x
```

**Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.11.x
3. ⚠️ **CHECK** "Add Python to PATH" during installation
4. Open Command Prompt → `python --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y
```

### 1.2 Install Git

**macOS:**
```bash
brew install git
git --version
# Expected: git version 2.x.x
```

**Windows:** Download from [git-scm.com](https://git-scm.com/download/win)

**Linux:**
```bash
sudo apt install git -y
```

### 1.3 Install AWS CLI v2

> 💡 **What is AWS CLI?** It's a command-line tool that lets you manage AWS services from your terminal instead of clicking through the web console.

**macOS:**
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify
aws --version
# Expected: aws-cli/2.x.x
```

**Windows:** Download from [aws.amazon.com/cli](https://aws.amazon.com/cli/) and run the MSI installer.

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 1.4 Install Docker (Optional)

Only needed if you want to deploy via containers.

- **macOS:** [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- **Windows:** [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

### 1.5 Clone the Project & Set Up Python

```bash
# Clone the repository
git clone <repo-url>
cd Data_scout

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Your prompt should now show (venv):
# (venv) ~/Data_scout $

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify everything installed
python3 -c "import streamlit; import boto3; import pandas; print('All packages installed ✅')"
```

---

## 4. Step 2: Create AWS Account & IAM User

### 2.1 Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com/)
2. Click **"Create an AWS Account"**
3. Enter email, password, account name
4. Add credit/debit card (Free Tier covers most usage)
5. Choose **Basic Support (Free)**

> 💰 **Cost:** Free Tier covers most services for 12 months. DataScout costs ~$6–30/month beyond free tier.

### 2.2 Create IAM User

> 🔐 **Why?** Never use your root account for development. IAM users have limited, specific permissions.

1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. Search for **"IAM"** in the top search bar → click **IAM**
3. Click **"Users"** → **"Create user"**
4. Username: `datascout-developer`
5. Check **"Provide user access to the AWS Management Console"**
6. Click **Next**

### 2.3 Set Permissions

1. Select **"Attach policies directly"**
2. Search for and check these policies:
   - ✅ `AmazonS3FullAccess`
   - ✅ `AmazonBedrockFullAccess`
   - ✅ `AmazonDynamoDBFullAccess`
   - ✅ `AWSLambda_FullAccess`
   - ✅ `AmazonAPIGatewayAdministrator`
   - ✅ `IAMFullAccess`
   - ✅ `AWSAppRunnerFullAccess`
   - ✅ `CloudWatchFullAccess`
   - ✅ `AWSCloudFormationFullAccess`
3. Click **Next** → **Create user**

### 2.4 Create Access Keys

1. Click the user `datascout-developer`
2. Go to **"Security credentials"** tab
3. Scroll to **"Access keys"** → **"Create access key"**
4. Select **"Command Line Interface (CLI)"**
5. Click **Next** → **Create access key**
6. ⚠️ **Download the `.csv` file NOW.** You will **never see the Secret Key again.**

```
Access Key ID:     AKIA...............
Secret Access Key: wJalrX..........
```

> 🛡️ **NEVER** share these keys, commit them to Git, or put them in code files.

---

## 5. Step 3: Configure AWS CLI

Open your terminal and run:

```bash
aws configure
```

Enter these values one by one:

```
AWS Access Key ID [None]: AKIA...............    ← paste your Access Key ID
AWS Secret Access Key [None]: wJalrX..........  ← paste your Secret Access Key
Default region name [None]: us-east-1           ← type exactly: us-east-1
Default output format [None]: json              ← type: json
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

✅ If you see your account info, AWS CLI is configured correctly!

> ⚠️ **If you get an error:** Double-check your Access Key and Secret Key. Run `aws configure` again.

---

## 6. Step 4: Create Amazon S3 Bucket

> 💡 **What is S3?** Amazon Simple Storage Service (S3) is like a cloud hard drive. DataScout stores uploaded datasets here with encryption.

### Option A: Using the Script (Recommended)

```bash
cd Data_scout
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

### Option B: Using AWS Console (Manual)

1. Go to [S3 Console](https://s3.console.aws.amazon.com/)
2. Click **"Create bucket"**
3. **Bucket name:** `datascout-storage` (must be globally unique — add your initials if taken, e.g., `datascout-storage-pk123`)
4. **Region:** `US East (N. Virginia) us-east-1`
5. **Block all public access:** ✅ Keep checked
6. **Bucket Versioning:** Enable
7. **Default encryption:** Amazon S3-managed keys (SSE-S3)
8. Click **"Create bucket"**

### Option C: Using AWS CLI Commands

```bash
# Create the bucket
aws s3 mb s3://datascout-storage --region us-east-1

# Enable versioning (keeps old versions of files)
aws s3api put-bucket-versioning \
    --bucket datascout-storage \
    --versioning-configuration Status=Enabled

# Enable encryption (AES-256 — all files encrypted at rest)
aws s3api put-bucket-encryption \
    --bucket datascout-storage \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }'

# Block ALL public access (security best practice)
aws s3api put-public-access-block \
    --bucket datascout-storage \
    --public-access-block-configuration \
        BlockPublicAcls=true,\
        IgnorePublicAcls=true,\
        BlockPublicPolicy=true,\
        RestrictPublicBuckets=true

# Auto-delete old files after 7 days (cost saving)
aws s3api put-bucket-lifecycle-configuration \
    --bucket datascout-storage \
    --lifecycle-configuration '{
        "Rules": [
            {
                "ID": "DeleteSessionData",
                "Filter": {"Prefix": "datasets/"},
                "Status": "Enabled",
                "Expiration": {"Days": 7}
            },
            {
                "ID": "DeleteArtifacts",
                "Filter": {"Prefix": "artifacts/"},
                "Status": "Enabled",
                "Expiration": {"Days": 7}
            }
        ]
    }'
```

### Verify the bucket exists:

```bash
aws s3 ls | grep datascout
```

**Expected:** `2026-02-27 23:00:00 datascout-storage`

> 📝 **Remember your bucket name** — you'll need it in Step 11.

---

## 7. Step 5: Create IAM Roles & Policies

> 💡 **What are IAM Roles?** They define WHAT each service is allowed to do. For example, the Bedrock Agent role allows the AI to read files from S3, and the Lambda role allows the API to write to DynamoDB.

### Option A: Using the Script (Recommended)

```bash
chmod +x scripts/create_iam_roles.sh
./scripts/create_iam_roles.sh datascout-storage
```

### Option B: Using AWS CLI (Manual)

#### 5.1 Create the App Runner Role

This role lets the Streamlit web app access Bedrock, S3, DynamoDB, and CloudWatch:

```bash
# Create trust policy (tells AWS "App Runner can use this role")
cat > trust-apprunner.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "tasks.apprunner.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create the role
aws iam create-role \
    --role-name DataScout-AppRunnerRole \
    --assume-role-policy-document file://trust-apprunner.json

# Give it Bedrock access
aws iam attach-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Give it S3 access (only our bucket)
cat > s3-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:HeadObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::datascout-storage",
                "arn:aws:s3:::datascout-storage/*"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-name DataScoutS3Access \
    --policy-document file://s3-policy.json

# Give it DynamoDB access
cat > dynamodb-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "arn:aws:dynamodb:us-east-1:*:table/datascout-queries*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-name DataScoutDynamoDB \
    --policy-document file://dynamodb-policy.json

# Give it CloudWatch access (logging)
cat > cw-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "cloudwatch:PutMetricData"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-name DataScoutCloudWatch \
    --policy-document file://cw-policy.json
```

#### 5.2 Create the Bedrock Agent Role

This role lets the AI agent read datasets from S3:

```bash
cat > trust-bedrock.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

aws iam create-role \
    --role-name DataScout-BedrockAgentRole \
    --assume-role-policy-document file://trust-bedrock.json

# Give it S3 read access
aws iam put-role-policy \
    --role-name DataScout-BedrockAgentRole \
    --policy-name BedrockS3Access \
    --policy-document file://s3-policy.json

# Give it model invocation access
cat > bedrock-model-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/*",
                "arn:aws:bedrock:us-east-1:*:inference-profile/*"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name DataScout-BedrockAgentRole \
    --policy-name BedrockInferenceProfileAccess \
    --policy-document file://bedrock-model-policy.json
```

### Verify roles exist:

```bash
aws iam get-role --role-name DataScout-AppRunnerRole --query 'Role.Arn' --output text
aws iam get-role --role-name DataScout-BedrockAgentRole --query 'Role.Arn' --output text
```

Each should print an ARN like: `arn:aws:iam::123456789012:role/DataScout-AppRunnerRole`

> ⚠️ **If you get "NoSuchEntity":** The role wasn't created. Re-run the commands above.

---

## 8. Step 6: Enable Amazon Bedrock Model Access

> 💡 **What is Bedrock?** Amazon Bedrock gives you access to AI models (like Claude, Nova) as a managed service. You pay per use — no GPU servers to manage.

> ⚠️ **This step MUST be done in the AWS Console** — it cannot be done via CLI.

1. Go to [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Make sure you're in **us-east-1** region (check top-right dropdown)
3. In the left sidebar, click **"Model access"**
4. Click **"Manage model access"** or **"Enable all models"**
5. Find **"Anthropic"** → check **"Claude 3.5 Sonnet v2"**
6. Also check **"Amazon"** → **"Nova Pro"** (our primary model)
7. Click **"Request model access"**
8. Accept the terms and submit

**Wait time:** Usually instant, sometimes up to 24 hours for first-time users.

### Verify model access:

```bash
aws bedrock list-foundation-models \
    --query "modelSummaries[?contains(modelId, 'nova')].modelId" \
    --output text
```

**Expected:** You should see model IDs containing `nova`.

---

## 9. Step 7: Create Bedrock Agent with Code Interpreter

> 💡 **What is a Bedrock Agent?** It's an AI assistant that can understand your questions AND execute Python code to compute answers. The Code Interpreter is its "calculator" — it runs pandas, numpy, matplotlib in a secure sandbox.

### Option A: Using the Script (Recommended)

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
→ Creating production alias...
  Alias ID: XYZ789

✅ Setup Complete!
 BEDROCK_AGENT_ID=ABCDEF1234
 BEDROCK_AGENT_ALIAS_ID=XYZ789
```

> 📝 **Write down** both IDs — you need them in Step 11.

### Option B: Using AWS Console (Manual)

1. Go to [Bedrock Console → Agents](https://console.aws.amazon.com/bedrock/home#/agents)
2. Click **"Create Agent"**
3. **Agent name:** `DataScout-Analyst`
4. **Agent Resource Role:** Select **"Create and use a new service role"**
5. **Select Model:** Choose **Claude 3.5 Sonnet v2** or **Nova Pro**
   - ⚠️ Select the **Cross-region Inference Profile** if available
6. **Instructions:** Paste the following:

```
You are DataScout, an autonomous data analyst. Your role is to help users
analyze datasets by writing and executing Python code.

CRITICAL RULES:
1. NEVER guess or hallucinate numerical values
2. ALWAYS use code to compute statistics, aggregations, and insights
3. Generate clean, readable Python code using pandas and numpy
4. Validate inputs and handle errors gracefully
5. Explain your analytical approach clearly
6. Show all code to the user for transparency

AVAILABLE LIBRARIES: pandas, numpy, matplotlib, seaborn, scipy, scikit-learn
```

7. In **"Action groups"** → Click **"Add"** → Select **"Code Interpreter"** → Enable it
8. Click **"Save"**
9. Click **"Prepare"** at the top → Wait for status: **"Prepared"**
10. Scroll to **"Aliases"** → Click **"Create"**
11. Alias name: `PRODUCTION` → Click **"Create alias"**
12. Note both the **Agent ID** and **Alias ID**

### Enable Code Interpreter (if not done above):

1. Go to your agent in Bedrock Console
2. Click **"Edit in Agent builder"**
3. Find **"Action groups"** → **"Add"** → **"Code Interpreter"**
4. Enable it → **Save** → **Prepare**

### Configure Agent IAM Permissions:

> ⚠️ **This step fixes the common "AccessDeniedException"**

1. Go to [IAM Console → Roles](https://console.aws.amazon.com/iam/home#/roles)
2. Search for your agent's role (starts with `AmazonBedrockExecutionRoleForAgents_`)
3. Click the role → **"Add permissions"** → **"Create inline policy"**
4. Switch to **JSON tab** and paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/*",
                "arn:aws:bedrock:us-east-1:*:inference-profile/*"
            ]
        }
    ]
}
```

5. Name it `BedrockInferenceProfileAccess` → **Create policy**

### Verify the agent works:

```bash
aws bedrock-agent get-agent \
    --agent-id <YOUR_AGENT_ID> \
    --query 'agent.agentStatus' \
    --output text
```

**Expected:** `PREPARED`

---

## 10. Step 8: Create Amazon DynamoDB Table

> 💡 **What is DynamoDB?** It's a serverless database from AWS. Unlike traditional databases, you don't need to set up a server — just create a table and start reading/writing data. DataScout uses it to save every query and its results, so your analysis history survives app restarts.

### Option A: Using AWS CLI (Recommended)

```bash
aws dynamodb create-table \
    --table-name datascout-queries \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Project,Value=DataScout
```

**What this creates:**
- A table named `datascout-queries`
- **Partition key:** `session_id` (groups all queries from one user session)
- **Sort key:** `timestamp` (orders queries chronologically)
- **PAY_PER_REQUEST:** You only pay when you read/write (no fixed cost)

**Expected output:**
```json
{
    "TableDescription": {
        "TableName": "datascout-queries",
        "TableStatus": "CREATING",
        ...
    }
}
```

### Wait for creation to complete:

```bash
aws dynamodb wait table-exists --table-name datascout-queries
echo "✅ Table created!"
```

### Enable TTL (auto-delete old records after 7 days):

```bash
aws dynamodb update-time-to-live \
    --table-name datascout-queries \
    --time-to-live-specification \
        Enabled=true,AttributeName=ttl
```

> 💡 **Why TTL?** Old query records are automatically deleted after 7 days, keeping the table small and costs near zero.

### Option B: Using AWS Console (Manual)

1. Go to [DynamoDB Console](https://console.aws.amazon.com/dynamodbv2/)
2. Click **"Create table"**
3. **Table name:** `datascout-queries`
4. **Partition key:** `session_id` (String)
5. **Sort key:** `timestamp` (String)
6. **Table settings:** Select **"Customize settings"**
7. **Read/write capacity:** Select **"On-demand"**
8. Click **"Create table"**
9. After creation, go to the table → **"Additional settings"** tab
10. Scroll to **"Time to Live (TTL)"** → Click **"Turn on"**
11. TTL attribute name: `ttl` → Click **"Turn on TTL"**

### Verify the table:

```bash
aws dynamodb describe-table \
    --table-name datascout-queries \
    --query 'Table.TableStatus'
```

**Expected:** `"ACTIVE"`

### Test writing and reading (optional):

```bash
# Write a test item
aws dynamodb put-item \
    --table-name datascout-queries \
    --item '{
        "session_id": {"S": "test-123"},
        "timestamp": {"S": "2026-02-27T00:00:00"},
        "record_type": {"S": "QUERY"},
        "query": {"S": "What is the average revenue?"}
    }'

# Read it back
aws dynamodb get-item \
    --table-name datascout-queries \
    --key '{
        "session_id": {"S": "test-123"},
        "timestamp": {"S": "2026-02-27T00:00:00"}
    }'

# Clean up test item
aws dynamodb delete-item \
    --table-name datascout-queries \
    --key '{
        "session_id": {"S": "test-123"},
        "timestamp": {"S": "2026-02-27T00:00:00"}
    }'
```

---

## 11. Step 9: Create AWS Lambda Function

> 💡 **What is Lambda?** AWS Lambda lets you run code without managing servers. You upload your code, and AWS runs it only when someone calls it. You pay per request — pennies for thousands of calls. DataScout uses Lambda to provide a REST API that other apps can call.

### 9.1 Create the Lambda Execution Role

This role gives the Lambda function permission to access Bedrock, DynamoDB, S3, and CloudWatch:

```bash
# Create trust policy for Lambda
cat > trust-lambda.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create the role
aws iam create-role \
    --role-name DataScout-LambdaRole \
    --assume-role-policy-document file://trust-lambda.json

# Attach basic Lambda execution (CloudWatch Logs)
aws iam attach-role-policy \
    --role-name DataScout-LambdaRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Attach Bedrock access
cat > lambda-bedrock-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeAgent",
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name DataScout-LambdaRole \
    --policy-name LambdaBedrockAccess \
    --policy-document file://lambda-bedrock-policy.json

# Attach DynamoDB access
aws iam put-role-policy \
    --role-name DataScout-LambdaRole \
    --policy-name LambdaDynamoDBAccess \
    --policy-document file://dynamodb-policy.json

# Attach S3 read access
aws iam put-role-policy \
    --role-name DataScout-LambdaRole \
    --policy-name LambdaS3Access \
    --policy-document file://s3-policy.json
```

### 9.2 Package the Lambda Function

```bash
# Navigate to the lambda_function directory
cd Data_scout/lambda_function

# Create a deployment package (zip file)
zip -r ../datascout-lambda.zip handler.py

# Go back to project root
cd ..
```

### 9.3 Deploy the Lambda Function

```bash
# Get the role ARN
LAMBDA_ROLE_ARN=$(aws iam get-role \
    --role-name DataScout-LambdaRole \
    --query 'Role.Arn' --output text)

# Wait 10 seconds for IAM role to propagate
sleep 10

# Create the Lambda function
aws lambda create-function \
    --function-name datascout-api \
    --runtime python3.11 \
    --handler handler.lambda_handler \
    --role $LAMBDA_ROLE_ARN \
    --zip-file fileb://datascout-lambda.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment "Variables={
        AWS_REGION_NAME=us-east-1,
        BEDROCK_AGENT_ID=2V8KLCC97S,
        BEDROCK_AGENT_ALIAS_ID=ADO5CA4VCF,
        DYNAMODB_TABLE=datascout-queries,
        S3_BUCKET=datascout-storage
    }"
```

> ⚠️ Replace `<YOUR_AGENT_ID>` and `<YOUR_ALIAS_ID>` with the values from Step 7.

### 9.4 Test the Lambda Function

```bash
# Test the health endpoint
aws lambda invoke \
    --function-name datascout-api \
    --payload '{"httpMethod": "GET", "path": "/health"}' \
    --cli-binary-format raw-in-base64-out \
    output.json

cat output.json
```

**Expected output:**
```json
{
    "statusCode": 200,
    "body": "{\"status\": \"ok\", \"service\": \"datascout-api\", ...}"
}
```

✅ Lambda is working!

```bash
# Clean up test file
rm -f output.json
```

---

## 12. Step 10: Create Amazon API Gateway

> 💡 **What is API Gateway?** It provides HTTP endpoints (URLs) that route requests to your Lambda function. Without it, your Lambda function has no URL — API Gateway gives it one like `https://abc123.execute-api.us-east-1.amazonaws.com/prod/health`.

### 10.1 Create the REST API

```bash
# Create the API
API_ID=$(aws apigateway create-rest-api \
    --name datascout-api \
    --description "DataScout REST API — query analysis and history" \
    --endpoint-configuration types=REGIONAL \
    --query 'id' --output text)

echo "API ID: $API_ID"

# Get the root resource ID (/)
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query 'items[0].id' --output text)

echo "Root Resource ID: $ROOT_ID"
```

### 10.2 Create /health Endpoint

```bash
# Create /health resource
HEALTH_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part health \
    --query 'id' --output text)

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
    --function-name datascout-api \
    --query 'Configuration.FunctionArn' --output text)

# Add GET method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $HEALTH_ID \
    --http-method GET \
    --authorization-type NONE

# Connect to Lambda
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $HEALTH_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations"
```

### 10.3 Create /analyze Endpoint

```bash
# Create /analyze resource
ANALYZE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part analyze \
    --query 'id' --output text)

# Add POST method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $ANALYZE_ID \
    --http-method POST \
    --authorization-type NONE

# Connect to Lambda
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $ANALYZE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations"
```

### 10.4 Create /history/{session_id} Endpoint

```bash
# Create /history resource
HISTORY_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part history \
    --query 'id' --output text)

# Create /history/{session_id} resource
HISTORY_SESSION_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $HISTORY_ID \
    --path-part '{session_id}' \
    --query 'id' --output text)

# Add GET method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $HISTORY_SESSION_ID \
    --http-method GET \
    --authorization-type NONE

# Connect to Lambda
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $HISTORY_SESSION_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations"
```

### 10.5 Give API Gateway Permission to Invoke Lambda

```bash
aws lambda add-permission \
    --function-name datascout-api \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*"
```

### 10.6 Deploy the API

```bash
# Create deployment
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --description "DataScout API — production deployment"

# Print the API URL
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ API Gateway deployed!"
echo "  Base URL: https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod"
echo ""
echo "  Endpoints:"
echo "    GET  /health              → Service health check"
echo "    POST /analyze             → Run data analysis query"
echo "    GET  /history/{session}   → Retrieve query history"
echo "═══════════════════════════════════════════════════════"
```

### Test the API:

```bash
# Test health endpoint
curl -s "https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/health" | python3 -m json.tool
```

**Expected:**
```json
{
    "status": "ok",
    "service": "datascout-api",
    "region": "us-east-1",
    "timestamp": "2026-02-27T..."
}
```

✅ API Gateway + Lambda are working together!

---

## 13. Step 11: Configure Environment Variables

Now that all AWS services are created, configure your local `.env` file:

```bash
cd Data_scout
cp .env.example .env
```

Open `.env` in your editor and fill in your values:

```env
# ── AWS Configuration ────────────────────────────────────────────────────────
AWS_REGION=us-east-1
S3_BUCKET=datascout-storage              ← your bucket name from Step 4

# ── Bedrock Agent ─────────────────────────────────────────────────────────────
BEDROCK_AGENT_ID=ABCDEF1234              ← your Agent ID from Step 7
BEDROCK_AGENT_ALIAS_ID=XYZ789           ← your Alias ID from Step 7

# ── Application Settings ─────────────────────────────────────────────────────
DEBUG=false
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
MAX_FILE_SIZE_MB=100
MAX_CONCURRENT_QUERIES=5

# ── DynamoDB ─────────────────────────────────────────────────────────────────
DYNAMODB_TABLE=datascout-queries         ← your table name from Step 8
ENABLE_DYNAMODB=true

# ── API Gateway ──────────────────────────────────────────────────────────────
API_GATEWAY_URL=https://abc123.execute-api.us-east-1.amazonaws.com/prod  ← from Step 10
```

### Verify config loads:

```bash
source venv/bin/activate
python3 -c "
from streamlit_app.config import Config
print(f'Region:       {Config.AWS_REGION}')
print(f'Bucket:       {Config.S3_BUCKET}')
print(f'Agent ID:     {Config.BEDROCK_AGENT_ID}')
print(f'DynamoDB:     {Config.DYNAMODB_TABLE}')
print(f'DynamoDB On:  {Config.ENABLE_DYNAMODB}')
print('✅ All configuration loaded!')
"
```

---

## 14. Step 12: Run the App Locally & Test

### 12.1 Generate Demo Data

```bash
python3 scripts/seed_demo_data.py
```

### 12.2 Start the Application

```bash
streamlit run streamlit_app/app.py
```

**Expected:**
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

### 12.3 Test the Full Flow

1. Open **http://localhost:8501**
2. Upload `demo/datasets/sales_data.csv`
3. Ask: `"What are the top 5 products by total revenue?"`
4. Verify you see: Explanation, Results, Code, Charts tabs

### 12.4 Verify DynamoDB Persistence

After running a query, check DynamoDB has the record:

```bash
aws dynamodb scan \
    --table-name datascout-queries \
    --max-items 1 \
    --query 'Items[0].{session_id: session_id.S, query: query.S}'
```

You should see your query stored in DynamoDB! ✅

---

## 15. Step 13: Run the Test Suite

```bash
# Run ALL unit tests
pytest tests/unit/ -v
```

**Expected:** `86 passed` ✅

### Run specific test groups:

```bash
# DynamoDB handler tests (9 tests)
pytest tests/unit/test_dynamodb_handler.py -v

# Lambda handler tests (7 tests)
pytest tests/unit/test_lambda_handler.py -v

# Existing tests (70 tests)
pytest tests/unit/test_bedrock_client.py tests/unit/test_s3_handler.py tests/unit/test_session_manager.py tests/unit/test_validators.py tests/unit/test_formatters.py tests/unit/test_error_handler.py -v
```

---

## 16. Step 14: Deploy with CloudFormation

> 💡 **What is CloudFormation?** Instead of creating each service manually (Steps 4–10), CloudFormation creates ALL of them from a single YAML template file. One command = everything deployed.

### 14.1 Validate the Template

```bash
aws cloudformation validate-template \
    --template-body file://cloudformation/datascout-stack.yaml
```

**Expected:** No errors = template is valid ✅

### 14.2 Deploy the Full Stack

```bash
aws cloudformation deploy \
    --template-file cloudformation/datascout-stack.yaml \
    --stack-name datascout-prod \
    --parameter-overrides \
        BedrockAgentId=2V8KLCC97S \
        BedrockAgentAliasId=ADO5CA4VCF \
    --capabilities CAPABILITY_NAMED_IAM
```

> ⚠️ Replace `<YOUR_AGENT_ID>` and `<YOUR_ALIAS_ID>` with your values.

**Wait time:** 5–10 minutes. CloudFormation creates:

| Resource | What It Creates |
|----------|----------------|
| S3 Bucket | `datascout-storage-<account>-prod` |
| DynamoDB Table | `datascout-queries-prod` |
| IAM Roles | App Runner, Lambda, Bedrock roles |
| Lambda Function | `datascout-api-prod` |
| API Gateway | REST API with 3 endpoints |
| App Runner | Hosted Streamlit app |
| CloudWatch | Log group `/datascout/prod/app` |

### 14.3 Get the Outputs

```bash
aws cloudformation describe-stacks \
    --stack-name datascout-prod \
    --query 'Stacks[0].Outputs'
```

**Expected output:**
```json
[
    {"OutputKey": "AppUrl", "OutputValue": "abcdef.us-east-1.awsapprunner.com"},
    {"OutputKey": "ApiGatewayUrl", "OutputValue": "https://xyz.execute-api.us-east-1.amazonaws.com/prod"},
    {"OutputKey": "DynamoDBTableName", "OutputValue": "datascout-queries-prod"},
    {"OutputKey": "BucketName", "OutputValue": "datascout-storage-123456-prod"},
    {"OutputKey": "LambdaFunctionArn", "OutputValue": "arn:aws:lambda:..."}
]
```

---

## 17. Step 15: Deploy to AWS App Runner

> 💡 **What is App Runner?** It hosts your web application. You give it your code, and it builds, deploys, and scales it automatically. No Docker, no EC2 instances, no load balancers to manage.

If you deployed via CloudFormation (Step 14), App Runner is already set up. Otherwise:

### Manual App Runner Setup

1. Go to [App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Click **"Create service"**
3. **Source:** Source code repository → Connect GitHub
4. **Branch:** `main`
5. **Build settings:**
   - Runtime: **Python 3.11**
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run streamlit_app/app.py --server.port 8080 --server.address 0.0.0.0 --server.headless true`
   - Port: `8080`
6. **Instance:** 1 vCPU, 2 GB RAM
7. **Security → Instance role:** `DataScout-AppRunnerRole`
8. **Environment variables:**
   - `AWS_REGION` = `us-east-1`
   - `S3_BUCKET` = `datascout-storage`
   - `BEDROCK_AGENT_ID` = your agent ID
   - `BEDROCK_AGENT_ALIAS_ID` = your alias ID
   - `DYNAMODB_TABLE` = `datascout-queries`
   - `ENABLE_DYNAMODB` = `true`
9. Click **"Create & deploy"**
10. Wait 5–10 minutes → Status: **"Running"** ✅

---

## 18. Step 16: Set Up CloudWatch Monitoring

> 💡 **What is CloudWatch?** It collects logs and metrics from all your AWS services. Think of it as a dashboard that shows what's happening in your app — errors, timing, usage.

### 16.1 View Application Logs

```bash
# View recent logs
aws logs tail /datascout/prod/app --since 5m --follow
```

### 16.2 Create a Dashboard (Console)

1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Click **"Dashboards"** → **"Create dashboard"**
3. Name: `DataScout-Monitoring`
4. Add widgets for:
   - Lambda invocations count
   - Lambda error count
   - Lambda duration (average)
   - DynamoDB read/write capacity
   - API Gateway 4xx/5xx errors

### 16.3 Set Up Alarms (Optional)

```bash
# Alert if Lambda errors exceed 5 in 5 minutes
aws cloudwatch put-metric-alarm \
    --alarm-name datascout-lambda-errors \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --dimensions Name=FunctionName,Value=datascout-api
```

---

## 19. Step 17: Post-Deployment Verification

Run through this checklist after deployment:

### Health Checks

```bash
# 1. App Runner
curl -s https://<your-app-url>/_stcore/health

# 2. API Gateway
curl -s https://<your-api-url>/prod/health | python3 -m json.tool

# 3. S3 Bucket
aws s3 ls s3://datascout-storage/

# 4. DynamoDB
aws dynamodb describe-table --table-name datascout-queries --query 'Table.TableStatus'

# 5. Lambda
aws lambda invoke --function-name datascout-api \
    --payload '{"httpMethod":"GET","path":"/health"}' \
    --cli-binary-format raw-in-base64-out /dev/stdout

# 6. Bedrock Agent
aws bedrock-agent get-agent --agent-id <AGENT_ID> --query 'agent.agentStatus'
```

**All should return healthy/active/PREPARED** ✅

### Functional Test

1. Open the App Runner URL in your browser
2. Upload `demo/datasets/sales_data.csv`
3. Ask: `"What are the top 5 products by total revenue?"`
4. Verify: Response with Explanation, Code, Results, Charts
5. Ask 2 more follow-up questions
6. Check Query History shows all 3 queries

---

## 20. Cost Estimate

| Service | Free Tier | Monthly Cost (Light Use) |
|---------|-----------|--------------------------|
| **App Runner** | None | $5–15 |
| **Amazon Bedrock** | Pay per use | $1–10 |
| **S3** | 5 GB free | $0.01–0.50 |
| **DynamoDB** | 25 GB free, 25 WCU/RCU | $0 (free tier) |
| **Lambda** | 1M requests/month free | $0 (free tier) |
| **API Gateway** | 1M calls/month free | $0 (free tier) |
| **CloudWatch** | 5 GB logs free | $0–1 |
| **CloudFormation** | Free | $0 |
| **Total** | | **$6–27/month** |

> 💡 **To minimize costs:** Pause App Runner when not in use. DynamoDB, Lambda, and API Gateway are practically free at hackathon scale.

---

## 21. Teardown

To delete ALL AWS resources:

### Using CloudFormation (Recommended)

```bash
# Empty S3 bucket first (CloudFormation can't delete non-empty buckets)
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name datascout-prod \
    --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
    --output text)

aws s3 rm s3://$BUCKET_NAME --recursive

# Delete the entire stack
aws cloudformation delete-stack --stack-name datascout-prod

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name datascout-prod
echo "✅ All resources deleted!"
```

### Manual Teardown

```bash
# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id <API_ID>

# Delete Lambda
aws lambda delete-function --function-name datascout-api

# Delete DynamoDB table
aws dynamodb delete-table --table-name datascout-queries

# Empty and delete S3
aws s3 rm s3://datascout-storage --recursive
aws s3 rb s3://datascout-storage

# Delete Bedrock Agent
aws bedrock-agent delete-agent-alias --agent-id <ID> --agent-alias-id <ALIAS>
aws bedrock-agent delete-agent --agent-id <ID>

# Delete IAM roles
aws iam delete-role-policy --role-name DataScout-LambdaRole --policy-name LambdaBedrockAccess
aws iam delete-role-policy --role-name DataScout-LambdaRole --policy-name LambdaDynamoDBAccess
aws iam delete-role-policy --role-name DataScout-LambdaRole --policy-name LambdaS3Access
aws iam detach-role-policy --role-name DataScout-LambdaRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name DataScout-LambdaRole

aws iam delete-role-policy --role-name DataScout-AppRunnerRole --policy-name DataScoutS3Access
aws iam delete-role-policy --role-name DataScout-AppRunnerRole --policy-name DataScoutDynamoDB
aws iam delete-role-policy --role-name DataScout-AppRunnerRole --policy-name DataScoutCloudWatch
aws iam detach-role-policy --role-name DataScout-AppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
aws iam delete-role --role-name DataScout-AppRunnerRole

aws iam delete-role-policy --role-name DataScout-BedrockAgentRole --policy-name BedrockS3Access
aws iam delete-role-policy --role-name DataScout-BedrockAgentRole --policy-name BedrockInferenceProfileAccess
aws iam delete-role --role-name DataScout-BedrockAgentRole

# Delete CloudWatch log group
aws logs delete-log-group --log-group-name /datascout/prod/app

# Delete App Runner (if created manually)
aws apprunner delete-service --service-arn <SERVICE_ARN>
```

---

## 22. Troubleshooting

| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | `aws configure` — command not found | AWS CLI not installed | Go to Step 1.3 |
| 2 | `aws sts get-caller-identity` — error | Bad credentials | Re-run `aws configure` |
| 3 | `BucketAlreadyExists` | Bucket name taken globally | Add suffix: `datascout-storage-pk123` |
| 4 | `AccessDeniedException` on Bedrock | Model access not granted or agent role missing permissions | Complete Step 6 and Step 7 IAM section |
| 5 | `ResourceNotFoundException` on Agent | Agent not prepared | Bedrock Console → Agent → Click "Prepare" |
| 6 | `Missing required env vars` | `.env` not configured | Complete Step 11 |
| 7 | `ModuleNotFoundError: streamlit` | venv not activated | Run `source venv/bin/activate` |
| 8 | `Table does not exist` on DynamoDB | Table not created or wrong name | Re-run Step 8, check table name in `.env` |
| 9 | Lambda `Task timed out` | Query too complex or Bedrock slow | Increase Lambda timeout to 120s |
| 10 | API Gateway `500 Internal Server Error` | Lambda permission missing | Re-run Step 10.5 (add-permission) |
| 11 | API Gateway `403 Forbidden` | API not deployed | Re-run Step 10.6 (create-deployment) |
| 12 | CloudFormation `ROLLBACK_COMPLETE` | A resource failed to create | Check Events tab in CloudFormation console |
| 13 | App Runner stuck on "Deploying" | Build error | Check App Runner logs in console |
| 14 | DynamoDB `ConditionalCheckFailedException` | Item already exists | Safe to ignore — retry will work |
| 15 | `No code generated` by agent | Query too vague | Be specific: "What is the average X by Y?" |
| 16 | Port 8501 already in use | Another Streamlit running | `lsof -ti:8501 | xargs kill` |
| 17 | High AWS bill | App Runner running 24/7 | Pause service when not in use |
| 18 | `pip install` fails | Python version mismatch | Use Python 3.9–3.11 |
| 19 | DynamoDB `ENABLE_DYNAMODB=false` | Disabled in config | Set `ENABLE_DYNAMODB=true` in `.env` |
| 20 | Lambda `Import Error` | Wrong handler path | Ensure handler is `handler.lambda_handler` |

---

## Quick Reference — All Services at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    9 AWS Services Summary                        │
├──────────────┬──────────────────────────────────────────────────┤
│ Service      │ What to remember                                 │
├──────────────┼──────────────────────────────────────────────────┤
│ S3           │ Bucket name goes in .env as S3_BUCKET            │
│ Bedrock      │ Agent ID + Alias ID go in .env                   │
│ DynamoDB     │ Table name goes in .env as DYNAMODB_TABLE        │
│ Lambda       │ Function name: datascout-api                     │
│ API Gateway  │ URL goes in .env as API_GATEWAY_URL              │
│ IAM          │ 3 roles: AppRunner, Bedrock, Lambda              │
│ CloudWatch   │ Log group: /datascout/prod/app                   │
│ App Runner   │ Uses DataScout-AppRunnerRole                     │
│ CloudFormation│ Template: cloudformation/datascout-stack.yaml   │
└──────────────┴──────────────────────────────────────────────────┘
```

---

**🎉 Congratulations!** You've deployed DataScout with 9 AWS services!

For day-to-day usage, see [guide.md](guide.md).  
For the hackathon presentation, see [hackathon_presentation_guide.md](hackathon_presentation_guide.md).

---

**Document Generated:** February 27, 2026  
**Author:** DataScout Development Team
