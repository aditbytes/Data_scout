# DataScout — AWS Infrastructure Reference

> **Last Updated:** 2026-02-28 22:19 IST
> **AWS Account:** 466492745516
> **Region:** us-east-1

---

## IAM User (Step 2)
| Field | Value |
|-------|-------|
| Username | `datascout-developer` |
| Account ID | `466492745516` |
| ARN | `arn:aws:iam::466492745516:user/datascout-developer` |

## Amazon S3 (Step 4)
| Field | Value |
|-------|-------|
| Bucket Name | `datascout-storage` |
| Encryption | AES-256 (SSE-S3) |
| Public Access | Blocked |
| Lifecycle | 7-day expiration on `datasets/` and `artifacts/` |

## IAM Roles (Step 5)
| Role | ARN |
|------|-----|
| AppRunner Role | `DataScout-AppRunnerRole` |
| Bedrock Agent Role | `DataScout-BedrockAgentRole` |
| Lambda Role | `arn:aws:iam::466492745516:role/DataScout-LambdaRole` |

## Amazon Bedrock Agent (Step 7)
| Field | Value |
|-------|-------|
| Agent ID | `2V8KLCC97S` |
| Alias ID | `ADO5CA4VCF` |
| Agent Status | PREPARED ✅ |
| Model | Amazon Nova Pro (Cross-region Inference) |

## Amazon DynamoDB (Step 8)
| Field | Value |
|-------|-------|
| Table Name | `datascout-queries` |
| Partition Key | `session_id` (String) |
| Sort Key | `timestamp` (String) |
| Billing Mode | PAY_PER_REQUEST |
| TTL Attribute | `ttl` |

## AWS Lambda (Step 9)
| Field | Value |
|-------|-------|
| Function Name | `datascout-api` |
| Function ARN | `arn:aws:lambda:us-east-1:466492745516:function:datascout-api` |
| Runtime | Python 3.11 |
| Timeout | 60s |
| Memory | 256 MB |
| Role ARN | `arn:aws:iam::466492745516:role/DataScout-LambdaRole` |

## Amazon API Gateway (Step 10)
| Field | Value |
|-------|-------|
| API ID | `r19ewjwx53` |
| Root Resource ID | `toyw6fx73e` |
| Base URL | `https://r19ewjwx53.execute-api.us-east-1.amazonaws.com/prod` |
| Stage | `prod` |

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| POST | `/analyze` | Run data analysis query |
| GET | `/history/{session_id}` | Retrieve query history |

## Environment Variables (.env) (Step 11)
| Variable | Value |
|----------|-------|
| `AWS_REGION` | `us-east-1` |
| `S3_BUCKET` | `datascout-storage` |
| `BEDROCK_AGENT_ID` | `2V8KLCC97S` |
| `BEDROCK_AGENT_ALIAS_ID` | `ADO5CA4VCF` |
| `DYNAMODB_TABLE` | `datascout-queries` |
| `ENABLE_DYNAMODB` | `true` |
| `API_GATEWAY_URL` | `https://r19ewjwx53.execute-api.us-east-1.amazonaws.com/prod` |

## Local Run Verification (Step 12) ✅
- **Local URL:** `http://localhost:8501`
- **DynamoDB Persistence:** Verified ✅
  - **Session ID:** `ab3e47cd-56e0-4326-85a4-75c61c9c56ea`
  - **Query Sample:** `"Top 10 by customer_id"`
- **Chart Generation:** Working (`top_10_customers.png`)
- **Query Execution Time:** ~40 seconds

---

## Deployment Progress

| Step | Description | Status |
|------|-------------|--------|
| 1 | Prerequisites | ✅ Done |
| 2 | AWS Account & IAM User | ✅ Done |
| 3 | Configure AWS CLI | ✅ Done |
| 4 | Create S3 Bucket | ✅ Done |
| 5 | Create IAM Roles & Policies | ✅ Done |
| 6 | Enable Bedrock Model Access | ✅ Done |
| 7 | Create Bedrock Agent | ✅ Done |
| 8 | Create DynamoDB Table | ✅ Done |
| 9 | Create Lambda Function | ✅ Done |
| 10 | Create API Gateway | ✅ Done |
| 11 | Configure Environment Variables | ✅ Done |
| 12 | Run App Locally & Test | ✅ Done |
| 13 | Run Test Suite | ✅ Done |
| 14 | Deploy with CloudFormation | ⏭️ Skipped (Manual infrastructure already built) |
| 15 | Deploy to App Runner | ⬜ Pending |
| 16 | Set Up CloudWatch Monitoring | ⬜ Pending |
| 17 | Post-Deployment Verification | ⬜ Pending |


Instructions for Step 15
Go to the App Runner Console: Open Amazon App Runner in your browser.
Create Service: Click the orange Create service button.
Repository type: Select Source code repository.
Connect GitHub: Click Add new (if not already connected) and authorize AWS App Runner to access your GitHub account. Select your DataScout repository and the main branch.
Deployment Settings: Select Automatic (so it deploys automatically when you push git push). Click Next.
Build Settings:
Runtime: Python 3.11
Build command: pip install -r requirements.txt
Start command: streamlit run streamlit_app/app.py --server.port 8080 --server.address 0.0.0.0 --server.headless true
Port: 8080
Click Next.
Configure service (Service name): Call it datascout-frontend-prod.
Virtual CPU & Memory: Use the default or 1 vCPU, 2 GB RAM.
Environment variables: Add the following to match your 

.env
:
AWS_REGION: us-east-1
S3_BUCKET: datascout-storage
BEDROCK_AGENT_ID: 2V8KLCC97S
BEDROCK_AGENT_ALIAS_ID: ADO5CA4VCF
DYNAMODB_TABLE: datascout-queries
ENABLE_DYNAMODB: true
API_GATEWAY_URL: https://r19ewjwx53.execute-api.us-east-1.amazonaws.com/prod
Security → Instance role: This is crucial! Select the DataScout-AppRunnerRole we created in Step 5.
Click Next, then Create & deploy.