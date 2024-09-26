"""
文件名: bedrock_claude3_cross_region_inference.py
作者: Cao Liu
创建日期: 9/18/2024
最后修改日期: 9/23/2024

描述:
这个脚本用户展示如何进行bedrock 的跨区域推理
# 要开始跨区域推理，您可以使用Amazon Bedrock 中的预配置的推理配置文件。
# 模型的推理配置文件配置来自各个 AWS 区域的不同模型 ARN，并将它们抽象为统一的模型标识符（id 和 ARN）。
# 只需将此新推理配置文件标识符与InvokeModel或ConverseAPI 结合使用，即可使用跨区域推理功能。
"""


import boto3
import json
import base64
import pprint

bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

# List available inference profiles
bedrock = boto3.client(service_name='bedrock', region_name='us-east-1')
inference_profiles = bedrock.list_inference_profiles()
print(inference_profiles)

# Find the appropriate inference profile for Claude 3 Sonnet
#'inferenceProfileArn': 'arn:aws:bedrock:us-east-1:342367142984:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0',
#'inferenceProfileId': 'us.anthropic.claude-3-5-sonnet-20240620-v1:0',
inference_profile_id= 'us.anthropic.claude-3-5-sonnet-20240620-v1:0'


payload = {
    "modelId": inference_profile_id,  # Use the inference profile ID instead of the specific model ID
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
