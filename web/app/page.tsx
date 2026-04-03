"use client";

import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { OrderWidget } from "@/components/OrderWidget";
import type { OrderWidgetProps } from "@/components/OrderWidget";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useState } from "react";

const transport = new DefaultChatTransport({
  api: "/api/chat",
  headers: { "X-User-ID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890" },
});

// Maps widgetName values to their React components
const widgetRegistry: Record<
  string,
  React.ComponentType<OrderWidgetProps>
> = {
  OrderWidget,
};

export default function Home() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status } = useChat({ transport });
  const isLoading = status === "streaming" || status === "submitted";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage({ text: input });
    setInput("");
  };

  return (
    <div className="flex min-h-screen flex-col items-center bg-zinc-950">
      <header className="w-full border-b border-zinc-800 px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold">
            A2A
          </div>
          <div>
            <h1 className="text-lg font-semibold text-zinc-100">
              E-Commerce Agent Demo
            </h1>
            <p className="text-xs text-zinc-500">Powered by A2A Protocol</p>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-6">
        <div className="flex-1 space-y-4 overflow-y-auto pb-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-4 pt-24 text-center">
              <p className="text-zinc-500">
                Ask about products, check stock, or place an order.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  "What products do you have?",
                  "Is the mechanical keyboard in stock?",
                  "Order 2 wireless mice",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => sendMessage({ text: suggestion })}
                    className="rounded-full border border-zinc-700 px-4 py-2 text-sm text-zinc-400 transition-colors hover:border-zinc-500 hover:text-zinc-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <Message key={message.id} from={message.role}>
              {message.parts.map((part, i) => {
                if (part.type === "text") {
                  return (
                    <MessageContent
                      key={i}
                      className={
                        message.role === "user"
                          ? "group-[.is-user]:bg-indigo-600 group-[.is-user]:rounded-2xl group-[.is-user]:text-white"
                          : undefined
                      }
                    >
                      {message.role === "user" ? (
                        <span className="whitespace-pre-wrap leading-relaxed">
                          {part.text}
                        </span>
                      ) : (
                        <MessageResponse
                          isAnimating={
                            status === "streaming" &&
                            message.id === messages[messages.length - 1]?.id
                          }
                        >
                          {part.text}
                        </MessageResponse>
                      )}
                    </MessageContent>
                  );
                }

                // Tool invocation parts: type is "tool-{toolName}" in AI SDK v6
                const partType = part.type as string;
                if (partType.startsWith("tool-")) {
                  const toolPart = part as any;
                  const toolName = partType.slice(5); // strip "tool-" prefix

                  // Render widget when output is available and widgetName is set
                  if (
                    toolPart.state === "output-available" &&
                    toolPart.output?.widgetName
                  ) {
                    const Widget = widgetRegistry[toolPart.output.widgetName];
                    if (Widget) {
                      return <Widget key={i} {...toolPart.output.widgetProps} />;
                    }
                  }

                  // Default tool call badge
                  return (
                    <div
                      key={i}
                      className="my-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs"
                    >
                      <span className="font-mono text-indigo-400">
                        {toolName}
                      </span>
                      <span className="text-zinc-500">
                        {toolPart.state === "output-available"
                          ? " completed"
                          : " called"}
                      </span>
                    </div>
                  );
                }

                return null;
              })}
            </Message>
          ))}

          {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
            <Message from="assistant">
              <MessageContent>
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500 [animation-delay:0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500 [animation-delay:0.3s]" />
                </div>
              </MessageContent>
            </Message>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex items-center gap-3 border-t border-zinc-800 pt-4"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about products or place an order..."
            className="flex-1 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-indigo-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600"
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
