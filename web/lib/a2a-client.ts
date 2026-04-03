const INVENTORY_URL = process.env.INVENTORY_AGENT_URL || "http://localhost:9001";
const ORDERS_URL = process.env.ORDERS_AGENT_URL || "http://localhost:9002";

export interface AgentCardData {
  name: string;
  description: string;
  skills: Array<{
    id: string;
    name: string;
    description: string;
    examples?: string[];
  }>;
}

let inventoryCard: AgentCardData | null = null;
let ordersCard: AgentCardData | null = null;

export async function fetchAgentCards(): Promise<{
  inventory: AgentCardData;
  orders: AgentCardData;
}> {
  if (inventoryCard && ordersCard) {
    return { inventory: inventoryCard, orders: ordersCard };
  }

  const [invRes, ordRes] = await Promise.all([
    fetch(`${INVENTORY_URL}/a2a/.well-known/agent-card.json`),
    fetch(`${ORDERS_URL}/a2a/.well-known/agent-card.json`),
  ]);

  if (!invRes.ok) throw new Error(`Failed to fetch inventory agent card: ${invRes.status}`);
  if (!ordRes.ok) throw new Error(`Failed to fetch orders agent card: ${ordRes.status}`);

  inventoryCard = await invRes.json();
  ordersCard = await ordRes.json();

  console.log(`[A2A] Discovered agents: "${inventoryCard!.name}", "${ordersCard!.name}"`);

  return { inventory: inventoryCard!, orders: ordersCard! };
}

async function sendA2AMessage(baseUrl: string, text: string, userId?: string): Promise<string> {
  const messageId = crypto.randomUUID();
  const contextId = crypto.randomUUID();
  const fullText = userId ? `[user_id:${userId}]\n${text}` : text;

  const body = {
    jsonrpc: "2.0",
    id: messageId,
    method: "message/send",
    params: {
      message: {
        kind: "message",
        messageId,
        role: "user",
        parts: [{ kind: "text", text: fullText }],
        contextId,
      },
    },
  };

  const res = await fetch(`${baseUrl}/a2a/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`A2A request failed: ${res.status} ${await res.text()}`);
  }

  const json = await res.json();

  // Extract text from the task result
  const result = json.result;
  if (!result) {
    return JSON.stringify(json);
  }

  // Check artifacts for text content
  if (result.artifacts?.length) {
    const texts: string[] = [];
    for (const artifact of result.artifacts) {
      for (const part of artifact.parts || []) {
        if (part.kind === "text" || part.text) {
          texts.push(part.text);
        }
      }
    }
    if (texts.length) return texts.join("\n");
  }

  // Check history for agent messages
  if (result.history?.length) {
    const agentMessages = result.history.filter(
      (m: any) => m.role === "agent"
    );
    const texts: string[] = [];
    for (const msg of agentMessages) {
      for (const part of msg.parts || []) {
        if (part.kind === "text" || part.text) {
          texts.push(part.text);
        }
      }
    }
    if (texts.length) return texts.join("\n");
  }

  return JSON.stringify(result);
}

export async function queryInventoryAgent(query: string, userId?: string): Promise<string> {
  return sendA2AMessage(INVENTORY_URL, query, userId);
}

export async function queryOrdersAgent(query: string, userId?: string): Promise<string> {
  return sendA2AMessage(ORDERS_URL, query, userId);
}
