"""
文件名: bedrock_marketplace_deepseek.py
作者: Cao Liu
创建日期: 2/6/2025
最后修改日期: 2/8/2025

描述:
这个脚本展示如何使用 Amazon Bedrock 调用MarketPlace上的模型进行推理。
主要功能包括:
1. 支持多种聊天模板格式 (LLAMA, QWEN, DEEPSEEK)
2. 提供格式化提示词的功能
3. 实现了带有参数控制的模型调用
4. 包含输入输出的格式控制

使用方法:
1. 设置正确的region_name和model_id
2. 选择合适的聊天模板
3. 通过invoke_deepseek_model函数调用模型

"""

import boto3
import json
from enum import Enum


# replace with your region
region_name = "us-west-2"  
# replace with your model ARN
model_id = "arn:aws:sagemaker:us-west-2:342367142984:endpoint/endpoint-br-mp-ds-llama-8b"  

bedrock_runtime = boto3.client("bedrock-runtime", region_name= region_name)

class ChatTemplate(Enum):
    LLAMA = "llama"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
def format_prompt(prompt, template):
    """Format prompt according to model chat template"""
    templates = {
        ChatTemplate.LLAMA: f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a helpful assistant<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>""",

        ChatTemplate.QWEN: f"""<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant""",
        ChatTemplate.DEEPSEEK: f"""You are a helpful assistant <｜User｜>{prompt}<｜Assistant｜>"""
    }
    return templates[template]

def invoke_deepseek_model(prompt, template=ChatTemplate.DEEPSEEK, max_tokens=1000, temperature=0.6, top_p=0.9):
    """
    Invoke Bedrock model with input and output guardrails
    """

    # Format prompt with selected template
    formatted_prompt = format_prompt(prompt, template)

    # Prepare model input
    request_body = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "top_p": top_p,
            "temperature": temperature
        }
    }

    # Invoke model
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(request_body)
    )

    # Parse model response
    model_output = json.loads(response['body'].read())['generated_text']
    return model_output

# Example usage
if __name__ == "__main__":
    prompt = "What's 1+1?"
    result = invoke_deepseek_model(prompt, template=ChatTemplate.LLAMA)
    print(result)
