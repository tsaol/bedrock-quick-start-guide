"""
文件名: bedrock_marketplace_deepseek.py
作者: Cao Liu
创建日期: 2/6/2025
最后修改日期: 2/8/2025

描述:
这个脚本展示如何使用 Amazon Bedrock 调用MarketPlace上的模型进行推理。
主要功能包括:
1. 提供格式化提示词的功能
2. 实现了带有参数控制的模型调用
3. 支持流式输出和非流式输出两种方式
4. 包含输入输出的格式控制

使用方法:
1. 设置正确的region_name和model_id
2. 通过invoke_deepseek_model函数调用模型:
   - 普通调用: invoke_deepseek_model(prompt)
   - 流式调用: invoke_deepseek_model(prompt, stream=True)

"""

import boto3
import json
from enum import Enum


# replace with your region
region_name = "us-west-2"  
# replace with your model ARN
model_id = "arn:aws:sagemaker:us-west-2:xxx:endpoint/endpoint-bk-mp-qwen-7b"
bedrock_runtime = boto3.client("bedrock-runtime", region_name= region_name)

def invoke_deepseek_model(prompt, max_tokens=1000, temperature=0.6, top_p=0.9, stream=False):
    # Format prompt with unified template
    formatted_prompt = f"""<|begin_of_sentence|><|User|>{prompt}<|Assistant|>"""

    # Prepare model input
    request_body = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "top_p": top_p,
            "temperature": temperature
        }
    }

    if not stream:
        # 非流式输出
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        model_output = json.loads(response['body'].read())['generated_text']
        return model_output
    
        # response_body = json.loads(response.get('body').read()) 
        # model_output=  response_body.get('choices')[0]["text"]
        # return model_output

    else:
        # 流式输出
        response = bedrock_runtime.invoke_model_with_response_stream(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        

        stream = response.get("body")
        if stream:
            for event in stream:
                chunk = event.get("chunk")
                if chunk:
                    # Print the response chunk
                    chunk_json = json.loads(chunk.get("bytes").decode())
                    print(chunk_json)
        else:
            print("No response stream received.")

# Example usage
if __name__ == "__main__":
    prompt = "hello, who are you?"
    print("非流式输出示例:")
    result = invoke_deepseek_model(prompt)
    print(result)
    
    # print("\n流式输出示例:")
    # invoke_deepseek_model(prompt, stream=True)
