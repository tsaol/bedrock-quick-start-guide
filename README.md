# AWS Bedrock Quick Start Guide 快速上手指南
欢迎使用AWS Bedrock快速上手指南。本指南提供了如何快速设置和开始使用AWS Bedrock的说明以及必要的代码。

如果你需要更多的功能以及了解更多的细节，请参考AWS官方文档
[AWS Bedrock Official Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)

## 前置条件
在代码的运营环境安装boto3 (注意boto3 版本需要在1.28.59以上)
```
pip install boto3>=1.28.59
```

## 代码
以下是一段可以快速执行的python代码

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
