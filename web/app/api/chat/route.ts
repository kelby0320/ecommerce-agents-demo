import { streamText, convertToModelMessages, stepCountIs } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { getSystemPrompt, tools } from "@/lib/agent";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const systemPrompt = await getSystemPrompt();

  const result = streamText({
    model: anthropic("claude-sonnet-4-5"),
    system: systemPrompt,
    messages: await convertToModelMessages(messages),
    tools,
    stopWhen: stepCountIs(5),
  });

  return result.toUIMessageStreamResponse();
}
