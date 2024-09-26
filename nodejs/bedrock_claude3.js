import { fileURLToPath } from "url";
import { BedrockRuntimeClient, InvokeModelCommand, InvokeModelWithResponseStreamCommand } from "@aws-sdk/client-bedrock-runtime";

const FoundationModels = {
  CLAUDE_3_HAIKU: {
    modelId: "anthropic.claude-3-haiku-20240307-v1:0"
  }
};

/**
 * Invokes Anthropic Claude 3 using the Messages API.
 *
 * @param {string} prompt - The input text prompt for the model to complete.
 * @param {string} [modelId] - The ID of the model to use. Defaults to "anthropic.claude-3-haiku-20240307-v1:0".
 * @returns {Promise<string>} The model's response.
 */
export const invokeModel = async (
  prompt,
  modelId = "anthropic.claude-3-haiku-20240307-v1:0"
) => {
  const client = new BedrockRuntimeClient({ region: "us-east-1" });

  const payload = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 1000,
    messages: [
      {
        role: "user",
        content: [{ type: "text", text: prompt }],
      },
    ],
  };

  const command = new InvokeModelCommand({
    contentType: "application/json",
    body: JSON.stringify(payload),
    modelId,
  });

  const apiResponse = await client.send(command);
  const responseBody = JSON.parse(new TextDecoder().decode(apiResponse.body));
  return responseBody.content[0].text;
};

/**
 * Invokes Anthropic Claude 3 and processes the response stream.
 *
 * @param {string} prompt - The input text prompt for the model to complete.
 * @param {string} [modelId] - The ID of the model to use. Defaults to "anthropic.claude-3-haiku-20240307-v1:0".
 * @returns {Promise<string>} The complete message from the model.
 */
export const invokeModelWithResponseStream = async (
  prompt,
  modelId = "anthropic.claude-3-haiku-20240307-v1:0"
) => {
  const client = new BedrockRuntimeClient({ region: "us-east-1" });

  const payload = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 1000,
    messages: [
      {
        role: "user",
        content: [{ type: "text", text: prompt }],
      },
    ],
  };

  const command = new InvokeModelWithResponseStreamCommand({
    contentType: "application/json",
    body: JSON.stringify(payload),
    modelId,
  });

  const apiResponse = await client.send(command);
  let completeMessage = "";

  for await (const chunk of apiResponse.body) {
    const parsedChunk = JSON.parse(new TextDecoder().decode(chunk.chunk?.bytes));
    if (parsedChunk.type === "content_block_delta") {
      const text = parsedChunk.delta.text;
      completeMessage += text;
      process.stdout.write(text);
    }
  }

  return completeMessage;
};

// Main execution
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const prompt = 'Write a paragraph starting with: "Once upon a time..."';
  const modelId = FoundationModels.CLAUDE_3_HAIKU.modelId;
  console.log(`Prompt: ${prompt}`);
  console.log(`Model ID: ${modelId}`);

  (async () => {
    try {
      console.log("-".repeat(53));
      const response = await invokeModel(prompt, modelId);
      console.log("\n" + "-".repeat(53));
      console.log("Final structured response:");
      console.log(response);
    } catch (err) {
      console.log(`\n${err}`);
    }
  })();
}