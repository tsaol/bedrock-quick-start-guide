import base64
import boto3
import json
import os
import random

# 填写region
client = boto3.client("bedrock-runtime", region_name="us-east-1")

# model id
model_id = "stability.stable-diffusion-xl-v1"

#  prompt
prompt = "a blue sky"

# Generate a random seed.
seed = random.randint(0, 4294967295)

# Format the request payload using the model's native structure.
native_request = {
    "text_prompts": [{"text": prompt}],
    "style_preset": "photographic",
    "seed": seed,
    "cfg_scale": 10,
    "steps": 30,
}

request = json.dumps(native_request)
response = client.invoke_model(modelId=model_id, body=request)
model_response = json.loads(response["body"].read())
base64_image_data = model_response["artifacts"][0]["base64"]

# 保存图片到output 目录.
i, output_dir = 1, "output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
while os.path.exists(os.path.join(output_dir, f"stability_{i}.png")):
    i += 1

image_data = base64.b64decode(base64_image_data)

image_path = os.path.join(output_dir, f"stability_{i}.png")
with open(image_path, "wb") as file:
    file.write(image_data)

print(f"The generated image has been saved to {image_path}")

