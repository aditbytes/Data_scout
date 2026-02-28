# DataScout — Deployment Guide

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Deployment Overview

DataScout uses a fully serverless architecture on AWS with three main deployment targets:

```
┌─────────────────────────────────────────────────────┐
│                DEPLOYMENT TARGETS                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. AWS App Runner  → Streamlit Frontend            │
│  2. Amazon Bedrock  → Agent + Code Interpreter      │
│  3. Amazon S3       → Data & Artifact Storage       │
│                                                      │
│  Supporting Services:                                │
│  - AWS IAM          → Authentication & Authorization│
│  - CloudWatch       → Logging & Monitoring          │
│  - AWS CloudFormation / CDK → Infrastructure as Code│
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### 2.1 Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| AWS CLI | v2.x | AWS service management |
| Python | 3.9+ | Application runtime |
| pip | Latest | Package management |
| Docker | 20.x+ | Container builds (App Runner) |
| Git | 2.x+ | Source control |
| AWS CDK (optional) | 2.x | Infrastructure as Code |

### 2.2 AWS Account Setup

```bash
# 1. Install AWS CLI
brew install awscli       # macOS
# OR
pip install awscli        # Any OS

# 2. Configure credentials
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: us-east-1
# Default output format: json

# 3. Verify access
aws sts get-caller-identity
```

### 2.3 Required AWS Permissions

The deploying IAM user/role needs these managed policies:
- `AmazonBedrockFullAccess`
- `AmazonS3FullAccess`
- `AWSAppRunnerFullAccess`
- `IAMFullAccess` (for creating roles)
- `CloudWatchFullAccess`

---

## 3. Infrastructure Deployment

### 3.1 S3 Bucket Setup

```bash
# Create the main storage bucket
aws s3 mb s3://datascout-storage --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket datascout-storage \
    --versioning-configuration Status=Enabled

# Enable server-side encryption
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

# Block public access
aws s3api put-public-access-block \
    --bucket datascout-storage \
    --public-access-block-configuration \
        BlockPublicAcls=true,\
        IgnorePublicAcls=true,\
        BlockPublicPolicy=true,\
        RestrictPublicBuckets=true

# Set lifecycle policy (auto-delete after 7 days)
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
            },
            {
                "ID": "ArchiveLogs",
                "Filter": {"Prefix": "logs/"},
                "Status": "Enabled",
                "Transitions": [{
                    "Days": 7,
                    "StorageClass": "GLACIER"
                }],
                "Expiration": {"Days": 90}
            }
        ]
    }'
```

### 3.2 IAM Roles

#### App Runner Execution Role

```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
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
    --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Create custom S3 policy
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

# CloudWatch logging policy
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

#### Bedrock Agent Role

```bash
# Trust policy for Bedrock
cat > bedrock-trust.json << 'EOF'
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
    --assume-role-policy-document file://bedrock-trust.json

# Attach S3 read access for Code Interpreter
aws iam put-role-policy \
    --role-name DataScout-BedrockAgentRole \
    --policy-name BedrockS3Access \
    --policy-document file://s3-policy.json
```

### 3.3 Bedrock Agent Setup

```bash
# Step 1: Create the agent
AGENT_INSTRUCTIONS=$(cat << 'EOF'
You are DataScout, an autonomous data analyst. Your role is to help users 
analyze datasets by writing and executing Python code.

CRITICAL RULES:
1. NEVER guess or hallucinate numerical values
2. ALWAYS use code to compute statistics, aggregations, and insights
3. Generate clean, readable Python code using pandas and numpy
4. Validate inputs and handle errors gracefully
5. Explain your analytical approach clearly
6. Show all code to the user for transparency

WORKFLOW:
1. Understand the user's analytical question
2. Plan the analysis steps
3. Write Python code to perform the analysis
4. Execute the code using the Code Interpreter tool
5. Validate the results
6. Create visualizations if helpful
7. Present results with explanations

AVAILABLE LIBRARIES:
- pandas, numpy, matplotlib, seaborn, scipy, scikit-learn

RESPONSE FORMAT:
1. Brief explanation of analysis approach
2. Generated Python code (in code block)
3. Results (tables, statistics, insights)
4. Visualizations (if created)
5. Summary and next steps
EOF
)

aws bedrock-agent create-agent \
    --agent-name DataScout-Analyst \
    --foundation-model anthropic.claude-3-5-sonnet-20241022-v2:0 \
    --instruction "$AGENT_INSTRUCTIONS" \
    --agent-resource-role-arn arn:aws:iam::ACCOUNT:role/DataScout-BedrockAgentRole \
    --idle-session-ttl-in-seconds 600

# Step 2: Note the agentId from the output
# AGENT_ID=<returned-agent-id>

# Step 3: Enable Code Interpreter tool
aws bedrock-agent associate-agent-knowledge-base \
    --agent-id $AGENT_ID \
    --agent-version DRAFT \
    --knowledge-base-id code-interpreter

# Step 4: Prepare the agent
aws bedrock-agent prepare-agent --agent-id $AGENT_ID

# Step 5: Create an alias for production use
aws bedrock-agent create-agent-alias \
    --agent-id $AGENT_ID \
    --agent-alias-name PRODUCTION
```

---

## 4. Application Deployment

### 4.1 Local Development Setup

```bash
# Clone the repository
git clone https://github.com/org/datascout.git
cd datascout

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
AWS_REGION=us-east-1
S3_BUCKET=datascout-storage
BEDROCK_AGENT_ID=<your-agent-id>
BEDROCK_AGENT_ALIAS_ID=<your-alias-id>
DEBUG=true
LOG_LEVEL=DEBUG
SESSION_TIMEOUT_MINUTES=30
EOF

# Run locally
streamlit run streamlit_app/app.py --server.port 8501

# Access at http://localhost:8501
```

### 4.2 Docker Build

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY streamlit_app/ ./streamlit_app/
COPY config.py .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
```

```bash
# Build Docker image
docker build -t datascout-frontend:latest .

# Test locally
docker run -p 8501:8501 \
    -e AWS_REGION=us-east-1 \
    -e S3_BUCKET=datascout-storage \
    -e BEDROCK_AGENT_ID=<agent-id> \
    -e BEDROCK_AGENT_ALIAS_ID=<alias-id> \
    datascout-frontend:latest
```

### 4.3 AWS App Runner Deployment

#### Option A: From Source Repository (Recommended)

```bash
# Create App Runner service from GitHub
aws apprunner create-service \
    --service-name datascout-frontend \
    --source-configuration '{
        "CodeRepository": {
            "RepositoryUrl": "https://github.com/org/datascout",
            "SourceCodeVersion": {
                "Type": "BRANCH",
                "Value": "main"
            },
            "CodeConfiguration": {
                "ConfigurationSource": "API",
                "CodeConfigurationValues": {
                    "Runtime": "PYTHON_311",
                    "BuildCommand": "pip install -r requirements.txt",
                    "StartCommand": "streamlit run streamlit_app/app.py --server.port 8080 --server.address 0.0.0.0 --server.headless true",
                    "Port": "8080",
                    "RuntimeEnvironmentVariables": {
                        "AWS_REGION": "us-east-1",
                        "S3_BUCKET": "datascout-storage",
                        "BEDROCK_AGENT_ID": "<agent-id>",
                        "BEDROCK_AGENT_ALIAS_ID": "<alias-id>"
                    }
                }
            }
        },
        "AutoDeploymentsEnabled": true
    }' \
    --instance-configuration '{
        "Cpu": "1024",
        "Memory": "2048",
        "InstanceRoleArn": "arn:aws:iam::ACCOUNT:role/DataScout-AppRunnerRole"
    }' \
    --health-check-configuration '{
        "Protocol": "HTTP",
        "Path": "/_stcore/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    }'
```

#### Option B: From Docker Image (ECR)

```bash
# Create ECR repository
aws ecr create-repository --repository-name datascout-frontend

# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Tag and push image
docker tag datascout-frontend:latest \
    ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/datascout-frontend:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/datascout-frontend:latest

# Create App Runner service from ECR
aws apprunner create-service \
    --service-name datascout-frontend \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/datascout-frontend:latest",
            "ImageRepositoryType": "ECR",
            "ImageConfiguration": {
                "Port": "8501",
                "RuntimeEnvironmentVariables": {
                    "AWS_REGION": "us-east-1",
                    "S3_BUCKET": "datascout-storage",
                    "BEDROCK_AGENT_ID": "<agent-id>",
                    "BEDROCK_AGENT_ALIAS_ID": "<alias-id>"
                }
            }
        }
    }' \
    --instance-configuration '{
        "Cpu": "1024",
        "Memory": "2048",
        "InstanceRoleArn": "arn:aws:iam::ACCOUNT:role/DataScout-AppRunnerRole"
    }'
```

---

## 5. CloudFormation Template (IaC)

```yaml
# cloudformation/datascout-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: DataScout - Autonomous Enterprise Data Analyst

Parameters:
  BedrockAgentId:
    Type: String
    Description: ID of the pre-configured Bedrock Agent
  BedrockAgentAliasId:
    Type: String
    Description: Alias ID of the Bedrock Agent
  GitHubRepoUrl:
    Type: String
    Default: https://github.com/org/datascout

Resources:
  # S3 Storage Bucket
  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'datascout-storage-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        IgnorePublicAcls: true
        BlockPublicPolicy: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: DeleteSessionData
            Prefix: datasets/
            Status: Enabled
            ExpirationInDays: 7
          - Id: DeleteArtifacts
            Prefix: artifacts/
            Status: Enabled
            ExpirationInDays: 7
          - Id: ArchiveLogs
            Prefix: logs/
            Status: Enabled
            Transitions:
              - TransitionInDays: 7
                StorageClass: GLACIER
            ExpirationInDays: 90

  # IAM Role for App Runner
  AppRunnerRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: DataScout-AppRunnerRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: tasks.apprunner.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonBedrockFullAccess
      Policies:
        - PolicyName: S3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:PutObject
                  - s3:GetObject
                  - s3:DeleteObject
                  - s3:HeadObject
                  - s3:ListBucket
                Resource:
                  - !GetAtt DataBucket.Arn
                  - !Sub '${DataBucket.Arn}/*'
        - PolicyName: CloudWatchAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - cloudwatch:PutMetricData
                Resource: '*'

  # App Runner Service
  AppRunnerService:
    Type: AWS::AppRunner::Service
    Properties:
      ServiceName: datascout-frontend
      SourceConfiguration:
        AutoDeploymentsEnabled: true
        CodeRepository:
          RepositoryUrl: !Ref GitHubRepoUrl
          SourceCodeVersion:
            Type: BRANCH
            Value: main
          CodeConfiguration:
            ConfigurationSource: API
            CodeConfigurationValues:
              Runtime: PYTHON_311
              BuildCommand: pip install -r requirements.txt
              StartCommand: !Sub >-
                streamlit run streamlit_app/app.py
                --server.port 8080
                --server.address 0.0.0.0
                --server.headless true
              Port: '8080'
              RuntimeEnvironmentVariables:
                AWS_REGION: !Ref 'AWS::Region'
                S3_BUCKET: !Ref DataBucket
                BEDROCK_AGENT_ID: !Ref BedrockAgentId
                BEDROCK_AGENT_ALIAS_ID: !Ref BedrockAgentAliasId
      InstanceConfiguration:
        Cpu: '1024'
        Memory: '2048'
        InstanceRoleArn: !GetAtt AppRunnerRole.Arn
      HealthCheckConfiguration:
        Protocol: HTTP
        Path: /_stcore/health
        Interval: 10
        Timeout: 5
        HealthyThreshold: 1
        UnhealthyThreshold: 5

  # CloudWatch Log Group
  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /datascout/app
      RetentionInDays: 30

Outputs:
  AppUrl:
    Description: DataScout application URL
    Value: !GetAtt AppRunnerService.ServiceUrl
  BucketName:
    Description: S3 storage bucket name
    Value: !Ref DataBucket
  AppRunnerRoleArn:
    Description: App Runner execution role ARN
    Value: !GetAtt AppRunnerRole.Arn
```

### Deploy with CloudFormation

```bash
aws cloudformation deploy \
    --template-file cloudformation/datascout-stack.yaml \
    --stack-name datascout-prod \
    --parameter-overrides \
        BedrockAgentId=<agent-id> \
        BedrockAgentAliasId=<alias-id> \
    --capabilities CAPABILITY_NAMED_IAM
```

---

## 6. Environment Configuration

### 6.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | Yes | `us-east-1` | AWS region for all services |
| `S3_BUCKET` | Yes | `datascout-storage` | S3 bucket name |
| `BEDROCK_AGENT_ID` | Yes | — | Bedrock Agent ID |
| `BEDROCK_AGENT_ALIAS_ID` | Yes | — | Bedrock Agent Alias ID |
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `SESSION_TIMEOUT_MINUTES` | No | `30` | Session inactivity timeout |
| `MAX_FILE_SIZE_MB` | No | `100` | Max upload file size |
| `MAX_CONCURRENT_QUERIES` | No | `5` | Max concurrent queries |

### 6.2 Configuration File

```python
# config.py
import os

class Config:
    """Application configuration from environment variables."""

    # AWS
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET = os.getenv('S3_BUCKET', 'datascout-storage')
    BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID')
    BEDROCK_AGENT_ALIAS_ID = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'PRODUCTION')

    # Application
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xls', '.json']
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))

    # Performance
    CODE_EXECUTION_TIMEOUT = 30  # seconds
    MAX_CONCURRENT_QUERIES = int(os.getenv('MAX_CONCURRENT_QUERIES', '5'))

    # Feature Flags
    ENABLE_VISUALIZATIONS = True
    ENABLE_ADVANCED_STATS = True
    DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

    @classmethod
    def validate(cls):
        """Validate all required configs are set."""
        required = ['BEDROCK_AGENT_ID']
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise ValueError(f"Missing required env vars: {missing}")
```

---

## 7. CI/CD Pipeline

### 7.1 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy DataScout

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run linter
        run: flake8 streamlit_app/ --max-line-length 120

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=streamlit_app

      - name: Run integration tests
        if: github.event_name == 'push'
        env:
          BEDROCK_AGENT_ID: ${{ secrets.BEDROCK_AGENT_ID }}
          BEDROCK_AGENT_ALIAS_ID: ${{ secrets.BEDROCK_AGENT_ALIAS_ID }}
        run: pytest tests/integration/ -v -m integration

  deploy:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to App Runner
        run: |
          aws apprunner start-deployment \
            --service-arn ${{ secrets.APP_RUNNER_SERVICE_ARN }}
```

---

## 8. Monitoring & Health Checks

### 8.1 Health Check Endpoint

Streamlit provides a built-in health check at `/_stcore/health`. App Runner is configured to poll this endpoint every 10 seconds.

### 8.2 Post-Deployment Verification

```bash
# 1. Check App Runner service status
aws apprunner describe-service \
    --service-arn <service-arn> \
    --query 'Service.Status'

# 2. Check application URL
SERVICE_URL=$(aws apprunner describe-service \
    --service-arn <service-arn> \
    --query 'Service.ServiceUrl' --output text)
curl -f https://$SERVICE_URL/_stcore/health

# 3. Verify S3 bucket access
aws s3 ls s3://datascout-storage/

# 4. Test Bedrock Agent
aws bedrock-agent-runtime invoke-agent \
    --agent-id <agent-id> \
    --agent-alias-id <alias-id> \
    --session-id test-deploy \
    --input-text "Hello, are you ready?"

# 5. Check CloudWatch logs
aws logs tail /datascout/app --follow
```

### 8.3 Rollback Procedure

```bash
# If deployment fails, App Runner auto-rolls back
# For manual rollback:

# 1. List previous deployments
aws apprunner list-operations \
    --service-arn <service-arn>

# 2. Redeploy previous version (from Git)
git revert HEAD
git push origin main
# App Runner auto-deploys from main branch
```

---

## 9. Cost Estimation

### 9.1 Estimated Monthly Costs (MVP)

| Service | Usage Estimate | Cost/Month |
|---------|---------------|------------|
| App Runner | 1 vCPU, 2GB, ~720 hrs | ~$30 |
| Bedrock (Claude 3.5 Sonnet) | ~10,000 queries | ~$50–100 |
| S3 Standard | ~10 GB storage | ~$0.25 |
| CloudWatch Logs | ~5 GB/month | ~$2.50 |
| Data Transfer | ~10 GB | ~$0.90 |
| **Total** | | **~$85–135/month** |

### 9.2 Cost Optimization Tips
- Use App Runner auto-scaling (scale to zero when idle)
- Set S3 lifecycle policies to auto-delete old data
- Use CloudWatch log retention limits
- Monitor Bedrock token usage and set budget alerts

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| App Runner deploy fails | Build error | Check build logs in App Runner console |
| Agent returns empty response | Missing Code Interpreter | Verify agent tool configuration |
| S3 access denied | IAM policy mismatch | Verify role ARN and bucket policy |
| Streamlit won't start | Port conflict | Ensure port 8080 (App Runner) or 8501 (local) |
| Timeout on queries | Large dataset | Reduce dataset size or optimize query |
| CORS errors | App Runner config | Add `--server.enableCORS false` to Streamlit |

### 10.2 Debug Commands

```bash
# View App Runner service logs
aws apprunner describe-service --service-arn <arn> --query 'Service'

# View CloudWatch application logs
aws logs get-log-events \
    --log-group-name /datascout/app \
    --log-stream-name "$(aws logs describe-log-streams \
        --log-group-name /datascout/app \
        --query 'logStreams[0].logStreamName' --output text)"

# Test Bedrock Agent directly
python -c "
import boto3
client = boto3.client('bedrock-agent-runtime')
response = client.invoke_agent(
    agentId='AGENT_ID',
    agentAliasId='ALIAS_ID',
    sessionId='debug-session',
    inputText='What libraries are available?'
)
for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode())
"
```

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
