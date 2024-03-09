import boto3
import json
import base64

#多模态需要将文件以base64的形式输入给大模型
with open("aws.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read())
    base64_string = encoded_string.decode('utf-8')

# Create a BedrockRuntime client
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1', aws_access_key_id='ACCESS_KEY',
    aws_secret_access_key='SECRET_KEY')

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
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_string
                        }
                    },
                    {
                        "type": "text",
                        "text": "告诉我图片中有什么内容"
                    }
                ]
            }
        ]
    }
}


body_bytes = json.dumps(payload['body']).encode('utf-8')

response = bedrock_runtime.invoke_model(
    body=body_bytes,
    contentType=payload['contentType'],
    accept=payload['accept'],
    modelId=payload['modelId']
)

response_body = response['body'].read().decode('utf-8')
print(response_body)
