# AWS Bedrock Quick Start Guide 快速上手指南
欢迎使用AWS Bedrock快速上手指南。本指南提供了如何快速设置和开始使用AWS Bedrock的说明以及必要的代码。

如果你需要更多的功能以及了解更多的细节，请参考AWS官方文档
[AWS Bedrock Official Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)

## 前置条件
在代码的运营环境安装boto3 (注意boto3 版本需要在1.28.59以上)
```
pip install boto3>=1.28.59
```
## Claude3 代码 
以下是一段可以快速执行的Claude3 python代码
```
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
                        "type": "text",
                        "text": "告诉我你是谁"
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

```
* 是使用Claude3文生文的参考代码 `/python/bedrock_claude3.py`
* 是使用Claude3图片视觉的参考代码（多模态）  `/python/bedrock_claude3_vision.py`


## Claude2 代码 
以下是一段可以快速执行的Claude2 python代码

```
import boto3
import json

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1', aws_access_key_id='ACCESS_KEY',
    aws_secret_access_key='SECRET_KEY')


def main():
    #提示词
    input = '''
        \n\nHuman: who are you
        \n\nAssistant:
    '''
    print('input is %s' % input)
    #组装body
    body = json.dumps({"prompt": input, "max_tokens_to_sample": 800, "temperature": 1, "top_p": 0.99, "top_k": 250})
    # https://docs.aws.amazon.com/zh_cn/bedrock/latest/userguide/model-ids.html
    #bedrock通过在这里输入不同的模型ID，来切换模型
    modelId = 'anthropic.claude-v2'
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock_client.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    print('response_body is %s' % response_body.get('completion'))


if __name__ == '__main__':
    main()
```

* 以上是直接响应的代码 `/python/bedrock_101.py`
* 如果大模型生成的内容比较长，采用流式的返回。可以参考 `/python/bedrock_201.py`, 


## Thanks
Thank you for using AWS Bedrock!
