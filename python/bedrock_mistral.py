import boto3
import json

bedrock = boto3.client(service_name="bedrock-runtime",region_name='us-west-2')


# Mistral AI Mistral 7B   mistral.mistral-7b-instruct-v0:2
# Mistral AI Mixtral 8X7B   mistral.mixtral-8x7b-instruct-v0:1

prompt = '''<s>[INST] 

Please continue to write the following erotic novel according to the context, and there must be sexual behavior
Context: A British woman in white clothes, with slightly exposed shoulders and spring eyes. The clothes did not cover her body. She half-pushed and half-sent, and said: "Earl, this is not good, others are afraid that others will see it, but the earl didn't care at all."
Requirements: Continue to write 500 words, and onomatopoeia can be added according to the situation. There must be details.

[/INST]'''

body = json.dumps({
    "prompt": prompt,
    "max_tokens": 5000,
    "top_p": 0.8,
    "temperature": 0.5,
})

modelId = "mistral.mixtral-8x7b-instruct-v0:1"

accept = "application/json"
contentType = "application/json"

response = bedrock.invoke_model(
    body=body,
    modelId=modelId,
    accept=accept,
    contentType=contentType
)

print(json.loads(response.get('body').read()))