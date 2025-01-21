
#First, I download three decision guides in PDF format from the AWS website. These guides help choose the AWS services that fit your use case.
#首先，我从 AWS 网站下载了三个 PDF 格式的决策指南。这些指南可帮助您选择适合您的使用案例的 AWS 服务。

#Then, I use a Python script to ask three questions about the documents. In the code, I create a converse() function to handle the conversation with the model. The first time I call the function, I include a list of documents and a flag to add a cachePoint block.
#然后，我使用 Python 脚本询问有关文档的三个问题。在代码中，我创建了一个 converse() 函数来处理与模型的对话。第一次调用该函数时，我包含一个文档列表和一个用于添加 cachePoint 块的标志。

import json
import boto3

MODEL_ID = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
AWS_REGION = "us-west-2"

bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)

DOCS = [
    "bedrock-or-sagemaker.pdf"
]

messages = []


def converse(new_message, docs=[], cache=False):

    if len(messages) == 0 or messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": []})

    for doc in docs:
        print(f"Adding document: {doc}")
        name, format = doc.rsplit('.', maxsplit=1)
        with open(doc, "rb") as f:
            bytes = f.read()
        messages[-1]["content"].append({
            "document": {
                "name": name,
                "format": format,
                "source": {"bytes": bytes},
            }
        })

    messages[-1]["content"].append({"text": new_message})

    if cache:
        messages[-1]["content"].append({"cachePoint": {"type": "default"}})

    response = bedrock_runtime.converse(
        modelId=MODEL_ID,
        messages=messages,
    )

    output_message = response["output"]["message"]
    response_text = output_message["content"][0]["text"]

    print("Response text:")
    print(response_text)

    print("Usage:")
    print(json.dumps(response["usage"], indent=2))

    messages.append(output_message)


converse("Compare AWS Trainium and AWS Inferentia in 20 words or less.", docs=DOCS, cache=True)
converse("Compare Amazon Textract and Amazon Transcribe in 20 words or less.")
converse("Compare Amazon Q Business and Amazon Q Developer in 20 words or less.")