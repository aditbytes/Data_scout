#!/bin/bash
# =============================================================================
# DataScout — IAM Role Creation Script
# =============================================================================
# Creates all required IAM roles and policies for DataScout:
# - App Runner execution role (Bedrock + S3 + CloudWatch)
# - Bedrock Agent role (S3 access for Code Interpreter)
# =============================================================================
set -euo pipefail

BUCKET_NAME="${1:-datascout-storage}"

echo "═══════════════════════════════════════════════════════"
echo " DataScout — IAM Role Setup"
echo "═══════════════════════════════════════════════════════"

# ── App Runner Execution Role ────────────────────────────────────────────────
echo "→ Creating App Runner execution role..."
aws iam create-role \
    --role-name DataScout-AppRunnerRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "tasks.apprunner.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || echo "  Role already exists."

echo "→ Attaching Bedrock access..."
aws iam attach-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess 2>/dev/null || true

echo "→ Attaching S3 access policy..."
aws iam put-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-name DataScoutS3Access \
    --policy-document "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
            \"Effect\": \"Allow\",
            \"Action\": [
                \"s3:PutObject\", \"s3:GetObject\", \"s3:DeleteObject\",
                \"s3:HeadObject\", \"s3:ListBucket\"
            ],
            \"Resource\": [
                \"arn:aws:s3:::${BUCKET_NAME}\",
                \"arn:aws:s3:::${BUCKET_NAME}/*\"
            ]
        }]
    }"

echo "→ Attaching CloudWatch policy..."
aws iam put-role-policy \
    --role-name DataScout-AppRunnerRole \
    --policy-name DataScoutCloudWatch \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup", "logs:CreateLogStream",
                "logs:PutLogEvents", "cloudwatch:PutMetricData"
            ],
            "Resource": "*"
        }]
    }'

# ── Bedrock Agent Role ───────────────────────────────────────────────────────
echo "→ Creating Bedrock Agent role..."
aws iam create-role \
    --role-name DataScout-BedrockAgentRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || echo "  Role already exists."

echo "→ Attaching S3 read access for Code Interpreter..."
aws iam put-role-policy \
    --role-name DataScout-BedrockAgentRole \
    --policy-name BedrockS3Access \
    --policy-document "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
            \"Effect\": \"Allow\",
            \"Action\": [\"s3:GetObject\", \"s3:ListBucket\"],
            \"Resource\": [
                \"arn:aws:s3:::${BUCKET_NAME}\",
                \"arn:aws:s3:::${BUCKET_NAME}/*\"
            ]
        }]
    }"

echo ""
echo "✅ IAM roles created successfully!"
