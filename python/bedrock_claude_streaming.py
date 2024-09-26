


import boto3
import json
import base64
import pprint


bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
    
    
payload = {
    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
    "contentType": "application/json",
    "accept": "application/json",
    "body": {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "给我创作一首周杰伦风格的歌-铁拳"
                    }
                ]
            }
        ]
    }
}


body_bytes = json.dumps(payload['body']).encode('utf-8')



# Invoke the model
response = bedrock_runtime.invoke_model_with_response_stream(
   body=body_bytes,
    contentType=payload['contentType'],
    accept=payload['accept'],
    modelId=payload['modelId']
)

stream = response.get('body')
chunk_obj = {}
    
if stream:
    for event in stream:
        chunk = event.get('chunk')
        if chunk:
            chunk_obj = json.loads(chunk.get('bytes').decode())
            pprint.pprint(chunk_obj)
