"""DataScout Services — AWS integration layer."""

# Submodules are imported directly by callers (e.g. app.py).
# Keeping this __init__ import-free avoids eagerly loading boto3/botocore
# when the package is first touched (e.g. by unittest.mock.patch path resolution).

__all__ = ['BedrockAgentClient', 'S3Handler', 'SessionManager', 'DynamoDBHandler']
