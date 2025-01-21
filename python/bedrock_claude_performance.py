"""
File: bedrock_claude_performance.py
Author: Cao Liu
Created: 12/20/2024
Description: This script tests the performance metrics of Bedrock Claude 3 Sonnet model
- Time to First Token (TTFT)
- Output Tokens per Second  
- Total Response Time
"""

import boto3
import json
import time
import tiktoken

def count_tokens(text):
    """计算文本的token数量"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def create_bedrock_client():
    """创建Bedrock运行时客户端"""
    return boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'
    )

def invoke_model(client, prompt, max_tokens=100):
    """调用模型并返回响应和性能指标"""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }

    start_time = time.time()
    first_token_time = None
    response_text = ""
    
    response = client.invoke_model_with_response_stream(
        body=json.dumps(body).encode('utf-8'),
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json",
        accept="application/json"
    )


    for event in response.get('body'):
        chunk = event.get('chunk')
        if chunk:
            chunk_obj = json.loads(chunk.get('bytes').decode())
            if chunk_obj['type'] == 'content_block_delta':
                if first_token_time is None:
                    first_token_time = time.time()
                response_text += chunk_obj['delta']['text']
    
    end_time = time.time()
    
    # 计算性能指标
    ttft = first_token_time - start_time
    total_time = end_time - start_time
    output_tokens = count_tokens(response_text)
    tokens_per_second = output_tokens / (end_time - first_token_time) if first_token_time else 0
    
    return {
        'text': response_text,
        'ttft': ttft,
        'total_time': total_time,
        'tokens_per_second': tokens_per_second,
        'output_tokens': output_tokens
    }

def generate_input_text(target_tokens=1000):
    """生成指定token数量的输入文本"""
    base_text = "请详细描述人工智能在现代社会中的应用，包括但不限于以下方面：医疗保健、教育、金融、交通、制造业等。"
    while count_tokens(base_text) < target_tokens:
        base_text += " " + base_text
    return base_text[:target_tokens]

def run_performance_tests():
    """运行性能测试"""
    client = create_bedrock_client()
    
    print("开始Claude 3 Sonnet模型性能测试...\n")
    print("配置：")
    print("- 目标输入tokens：1000")
    print("- 目标输出tokens：100")
    print("-" * 50)
    
    # 生成1000 tokens的输入文本
    input_text = generate_input_text(1000)
    input_tokens = count_tokens(input_text)
    print(f"实际输入tokens：{input_tokens}")
    
    # 运行测试
    results = []
    for i in range(3):  # 运行3次测试取平均值
        print(f"\n运行测试 #{i+1}")
        print("\n输入文本:")
        print("="*80)
        print(input_text)
        print("="*80)
        
        response = invoke_model(client, input_text)
        
        print("\n模型输出:")
        print("="*80)
        print(response['text'])
        print("="*80)
        results.append(response)
        
        print(f"TTFT: {response['ttft']:.3f} 秒")
        print(f"输出速度: {response['tokens_per_second']:.2f} tokens/秒")
        print(f"总响应时间: {response['total_time']:.3f} 秒")
        print(f"输出tokens: {response['output_tokens']}")
    
    # 计算平均值
    avg_ttft = sum(r['ttft'] for r in results) / len(results)
    avg_tokens_per_second = sum(r['tokens_per_second'] for r in results) / len(results)
    avg_total_time = sum(r['total_time'] for r in results) / len(results)
    
    print("\n性能测试结果（平均值）：")
    print(f"Time to First Token: {avg_ttft:.3f} 秒")
    print(f"Output Tokens per Second: {avg_tokens_per_second:.2f} tokens/秒")
    print(f"Total Response Time: {avg_total_time:.3f} 秒")

if __name__ == "__main__":
    try:
        run_performance_tests()
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
