import { tool } from "ai";
import { z } from "zod";
import {
  fetchAgentCards,
  queryInventoryAgent,
  queryOrdersAgent,
} from "./a2a-client";

export async function getSystemPrompt(): Promise<string> {
  const { inventory, orders } = await fetchAgentCards();

  const formatSkills = (card: typeof inventory) =>
    card.skills
      .map(
        (s) =>
          `  - ${s.name}: ${s.description}${
            s.examples?.length ? `\n    Examples: ${s.examples.join(", ")}` : ""
          }`
      )
      .join("\n");

  return `You are an e-commerce assistant that helps customers with product inquiries and orders.

You have access to two specialized agents via the A2A (Agent-to-Agent) protocol:

## ${inventory.name}
${inventory.description}
Skills:
${formatSkills(inventory)}

## ${orders.name}
${orders.description}
Skills:
${formatSkills(orders)}

When a user asks about products, availability, or inventory, use the query_inventory tool.
When a user wants to place an order, check order status, or list orders, use the manage_orders tool.
You can call both tools in sequence if needed (e.g., check stock before placing an order).

Always be helpful and provide clear, concise responses based on the data returned by the agents.
When a tool result includes a "widgetName" field, the UI renders a visual widget for it — give a brief conversational summary rather than repeating the raw data.`;
}

export const tools = {
  query_inventory: tool({
    description:
      "Query the inventory agent to search products, check stock levels, or get product details.",
    inputSchema: z.object({
      query: z
        .string()
        .describe(
          "The query to send to the inventory agent, e.g. 'search for electronics' or 'check stock for SKU001'"
        ),
    }),
    execute: async ({ query }) => {
      const result = await queryInventoryAgent(query);
      return result;
    },
  }),
  manage_orders: tool({
    description:
      "Query the orders agent to create orders, get order status, or list all orders.",
    inputSchema: z.object({
      query: z
        .string()
        .describe(
          "The query to send to the orders agent, e.g. 'order 2 wireless mice' or 'list all orders'"
        ),
    }),
    execute: async ({ query }) => {
      const result = await queryOrdersAgent(query);
      try {
        const parsed = JSON.parse(result);
        if (parsed.order_id) {
          return {
            widgetName: "OrderWidget",
            widgetProps: { order: parsed },
            text: `Order ${parsed.order_id} — status: ${parsed.status}`,
          };
        }
        if (Array.isArray(parsed.orders)) {
          const count = parsed.total_count ?? parsed.orders.length;
          return {
            widgetName: "OrderWidget",
            widgetProps: { orders: parsed.orders, totalCount: count },
            text: `Found ${count} order(s).`,
          };
        }
      } catch {
        // Not parseable JSON or unrecognized shape — fall through to raw text
      }
      return result;
    },
  }),
};
