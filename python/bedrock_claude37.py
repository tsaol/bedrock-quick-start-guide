"""
文件名: bedrock_claude37.py
作者: Cao Liu
创建日期: 2025-03-12
最后修改日期: 2025-03-17

描述：演示如何使用  Bedrock Claude 3.7 Sonnet 模型进行推理

功能：
    - 使用 Claude 3.7 Sonnet 模型进行文本生成
    - 展示模型的思考过程和最终答案
    - 支持128k上下文窗口
    
参数说明：
    - model_id: Claude 3.7 Sonnet 模型ID
    - system_prompt: 系统提示词，用于设置模型角色
    - thinking: 控制模型思考过程的输出
        - type: enabled/disabled 是否启用思考过程输出
        - budget_tokens: 思考过程允许使用的最大 token 数
    - max_tokens: 响应生成的最大 token 数
    
使用示例：
    python bedrock_claude37.py
"""

import boto3
import json

def claude_reasoning():
    # Initialize Bedrock client for AWS region us-west-2
    bedrock = boto3.client(service_name='bedrock-runtime', 
                          region_name='us-west-2')

    # Set up the model ID for Claude 3.7 Sonnet
    model_id = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    
    # Define the system prompt for setting the assistant's role
    system_prompt = "You are a smart assistant."

    # Define the test query for demonstrating multi-step reasoning
    user_query = "输出《咏鹅》100 遍，并在每一次输出中打上计数tag，不可以少输出"
    


    # Prepare the request payload with model parameters
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "anthropic_beta": ["output-128k-2025-02-19"],
        "max_tokens": 81920,
        "thinking": {
            "type": "enabled",
            "budget_tokens": 2000,
        },
        "system": system_prompt,
        "messages": [{
            "role": "user",
            "content": user_query
        }]
    })

    # Make API call to Bedrock service
    response = bedrock.invoke_model(
        body=body,
        modelId=model_id,
        contentType='application/json'
    )

    # Parse and process the model's response
    response_body = json.loads(response['body'].read())
    
    # Display the model's step-by-step reasoning process with tags
    print("Reasoning Process:")
    thinking_output = ""
    for content in response_body['content']:
        if content['type'] == 'thinking':
            thinking_output += content['thinking']

    # add <thinking> tag
    xml_output = f"<thinking>{thinking_output}</thinking>"
    print(xml_output)
    
    # Display the model's final response
    print("\n  ------ Final Answer: ------\n")
    for content in response_body['content']:
        if content['type'] == 'text':
            print(content['text'])

    # # 发起流式请求（移除 headers 参数）
    # response = bedrock.invoke_model_with_response_stream(
    #     modelId=model_id,
    #     body=body,
    # )

    # stream = response.get("body")
    # if stream:
    #     for event in stream:
    #         chunk = event.get("chunk")
    #         if chunk:
    #             # Print the response chunk
    #             chunk_json = json.loads(chunk.get("bytes").decode())
    #             print(chunk_json)
    # else:
    #     print("No response stream received.")


if __name__ == "__main__":
    claude_reasoning()
