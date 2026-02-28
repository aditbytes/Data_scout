#!/bin/bash
# =============================================================================
# DataScout — CloudFormation Stack Teardown Script
# =============================================================================
set -euo pipefail

STACK_NAME="${1:-datascout-prod}"

echo "═══════════════════════════════════════════════════════"
echo " DataScout — Tearing Down Stack: ${STACK_NAME}"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "⚠️  WARNING: This will DELETE all resources in the stack!"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Empty S3 bucket first (required before deletion)
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$BUCKET_NAME" ] && [ "$BUCKET_NAME" != "None" ]; then
    echo "→ Emptying S3 bucket: ${BUCKET_NAME}..."
    aws s3 rm s3://${BUCKET_NAME} --recursive
fi

# Delete stack
echo "→ Deleting CloudFormation stack..."
aws cloudformation delete-stack --stack-name ${STACK_NAME}

echo "→ Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}

echo ""
echo "✅ Stack '${STACK_NAME}' deleted successfully."
