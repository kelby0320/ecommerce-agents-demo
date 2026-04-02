"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useState } from "react";

const transport = new DefaultChatTransport({ api: "/api/chat" });

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
            <p className="text-xs text-zinc-500">
              Powered by A2A Protocol
            </p>
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
                    onClick={() => {
                      sendMessage({ text: suggestion });
                    }}
                    className="rounded-full border border-zinc-700 px-4 py-2 text-sm text-zinc-400 transition-colors hover:border-zinc-500 hover:text-zinc-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  message.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-zinc-800 text-zinc-200"
                }`}
              >
                {message.parts.map((part, i) => {
                  if (part.type === "text") {
                    return (
                      <p key={i} className="whitespace-pre-wrap text-sm leading-relaxed">
                        {part.text}
                      </p>
                    );
                  }
                  if ("toolName" in part) {
                    return (
                      <div
                        key={i}
                        className="my-2 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs"
                      >
                        <span className="font-mono text-indigo-400">
                          {part.toolName}
                        </span>
                        <span className="text-zinc-500"> called</span>
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            </div>
          ))}

          {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-zinc-800 px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500 [animation-delay:0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500 [animation-delay:0.3s]" />
                </div>
              </div>
            </div>
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
