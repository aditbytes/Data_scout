#!/bin/bash
# =============================================================================
# DataScout — S3 Bucket Creation Script
# =============================================================================
# Creates and configures the S3 storage bucket with encryption, versioning,
# public access blocking, and lifecycle policies.
# =============================================================================
set -euo pipefail

BUCKET_NAME="${1:-datascout-storage}"
REGION="${2:-us-east-1}"

echo "═══════════════════════════════════════════════════════"
echo " DataScout — S3 Bucket Setup"
echo " Bucket: ${BUCKET_NAME}"
echo " Region: ${REGION}"
echo "═══════════════════════════════════════════════════════"

# Create bucket
echo "→ Creating S3 bucket..."
CREATE_OUTPUT=""
if [ "${REGION}" = "us-east-1" ]; then
    CREATE_OUTPUT=$(aws s3api create-bucket \
        --bucket "${BUCKET_NAME}" \
        --region "${REGION}" 2>&1) && echo "  Bucket created."
else
    CREATE_OUTPUT=$(aws s3api create-bucket \
        --bucket "${BUCKET_NAME}" \
        --region "${REGION}" \
        --create-bucket-configuration LocationConstraint="${REGION}" 2>&1) && echo "  Bucket created."
fi

# Handle result
if echo "${CREATE_OUTPUT}" | grep -q "BucketAlreadyOwnedByYou"; then
    echo "  Bucket already exists (owned by you). ✅"
elif echo "${CREATE_OUTPUT}" | grep -q "error\|Error"; then
    echo "  ${CREATE_OUTPUT}"
    echo "  ❌ Failed to create bucket."
    exit 1
fi

# Enable versioning
echo "→ Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "${BUCKET_NAME}" \
    --versioning-configuration Status=Enabled

# Enable encryption
echo "→ Enabling server-side encryption..."
aws s3api put-bucket-encryption \
    --bucket "${BUCKET_NAME}" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }'

# Block public access
echo "→ Blocking public access..."
aws s3api put-public-access-block \
    --bucket "${BUCKET_NAME}" \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,\
BlockPublicPolicy=true,RestrictPublicBuckets=true

# Set lifecycle rules
echo "→ Setting lifecycle rules..."
aws s3api put-bucket-lifecycle-configuration \
    --bucket "${BUCKET_NAME}" \
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
                "Transitions": [{"Days": 7, "StorageClass": "GLACIER"}],
                "Expiration": {"Days": 90}
            }
        ]
    }'

echo ""
echo "✅ S3 bucket '${BUCKET_NAME}' setup complete!"
