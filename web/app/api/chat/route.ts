import { streamText, convertToModelMessages, stepCountIs } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { getSystemPrompt, createTools } from "@/lib/agent";

export async function POST(req: Request) {
  const userId =
    req.headers.get("x-user-id") ?? "a1b2c3d4-e5f6-7890-abcd-ef1234567890";
  const { messages } = await req.json();
  const systemPrompt = await getSystemPrompt();

  const result = streamText({
    model: anthropic("claude-sonnet-4-6"),
    system: systemPrompt,
    messages: await convertToModelMessages(messages),
    tools: createTools(userId),
    stopWhen: stepCountIs(5),
  });

  return result.toUIMessageStreamResponse();
}
