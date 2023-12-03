import json
import os
import sys
import boto3

BEDROCK_REGION = "us-west-2"  # E.g. "us-east-1"
BEDROCK_ENDPOINT_URL = "YOU_ENDPOINT_RUL"  


def lambda_handler(event, context):
    # TODO implement
    
    boto3_bedrock = boto3.client(service_name='bedrock',
        endpoint_url=BEDROCK_ENDPOINT_URL,
        region_name=BEDROCK_REGION
    )
    
    test = boto3_bedrock.list_foundation_models()
    print('----------------invoke titan--------------------')
    kwargs = {
      "modelId": "amazon.titan-tg1-large",
      "contentType": "application/json",
      "accept": "*/*",
      "body": "{\"inputText\":\"once upon a time\",\"textGenerationConfig\":{\"maxTokenCount\":512,\"stopSequences\":[],\"temperature\":0,\"topP\":0.9}}",
    }
    
    response = boto3_bedrock.invoke_model(
        **kwargs
    )
    response_body = json.loads(response.get('body').read())
    print(response_body.get('results')[0].get('outputText'))
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }





