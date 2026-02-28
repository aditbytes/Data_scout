import boto3, json
import botocore.config

config = botocore.config.Config(region_name='us-east-1')
client = boto3.client('bedrock-agent-runtime', config=config)

dataset_uri = "s3://datascout-storage-use1/sales_data.csv"

try:
    request_dict = {
        "agentId": "2V8KLCC97S",
        "agentAliasId": "ADO5CA4VCF",
        "sessionId": "test-session-1234",
        "inputText": "hello",
        "sessionState": {
            "files": [
                {
                    "name": "sales_data.csv",
                    "source": {
                        "sourceType": "S3",
                        "s3Location": {
                            "uri": dataset_uri
                        }
                    },
                    "useCase": "CODE_INTERPRETER"
                }
            ]
        }
    }
    
    # Just try to construct the request to see if botocore validates it
    operation_model = client._service_model.operation_model('InvokeAgent')
    client._serializer.serialize_to_request(request_dict, operation_model)
    print("VALIDATION SUCCESSFUL!")
    
except Exception as e:
    print("VALIDATION ERROR:", e)
