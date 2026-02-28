#!/bin/bash
# =============================================================================
# DataScout — CloudFormation Deployment Script
# =============================================================================
set -euo pipefail

STACK_NAME="${1:-datascout-prod}"
ENVIRONMENT="${2:-prod}"
TEMPLATE="cloudformation/datascout-stack.yaml"
PARAMS_FILE="cloudformation/parameters/${ENVIRONMENT}.json"

echo "═══════════════════════════════════════════════════════"
echo " DataScout — Deploying Stack: ${STACK_NAME}"
echo " Environment: ${ENVIRONMENT}"
echo "═══════════════════════════════════════════════════════"

# Validate template
echo "→ Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://${TEMPLATE}

# Deploy
echo "→ Deploying stack..."
aws cloudformation deploy \
    --template-file ${TEMPLATE} \
    --stack-name ${STACK_NAME} \
    --parameter-overrides file://${PARAMS_FILE} \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

# Get outputs
echo ""
echo "→ Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo "✅ Deployment complete!"
