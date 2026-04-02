from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils.artifact import new_text_artifact
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import new_task

ORDERS: dict[str, dict] = {}


def create_order(items: list[dict]) -> str:
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
    order = {
        "order_id": order_id,
        "items": items,
        "status": "pending",
        "total": round(total, 2),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ORDERS[order_id] = order
    return json.dumps(order, indent=2)


def get_order(order_id: str) -> str:
    order_id = order_id.upper()
    if order_id in ORDERS:
        return json.dumps(ORDERS[order_id], indent=2)
    return json.dumps({"error": f"Order {order_id} not found"})


def list_orders() -> str:
    if not ORDERS:
        return json.dumps({"message": "No orders found", "orders": []})
    return json.dumps(
        {"orders": list(ORDERS.values()), "total_count": len(ORDERS)},
        indent=2,
    )


def _parse_order_items(text: str) -> list[dict]:
    """Best-effort extraction of items from natural language."""
    items = []
    # Look for patterns like "2 wireless mice" or "1 usb-c hub"
    import re

    # Simple quantity + product name pattern
    patterns = re.findall(r"(\d+)\s+(.+?)(?:,|\band\b|$)", text, re.IGNORECASE)
    if patterns:
        for qty_str, name in patterns:
            items.append(
                {
                    "name": name.strip().rstrip("."),
                    "quantity": int(qty_str),
                    "price": 0,  # Price will be noted as "to be confirmed"
                }
            )
    if not items:
        # Fallback: treat the whole text as a single item
        items.append({"name": text.strip(), "quantity": 1, "price": 0})
    return items


class OrdersAgentExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)

        user_text = ""
        for part in context.message.parts:
            if hasattr(part.root, "text"):
                user_text = part.root.text
                break

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                final=False,
                status=TaskStatus(
                    state=TaskState.working,
                    message=new_agent_text_message("Processing order request..."),
                ),
            )
        )

        text_lower = user_text.lower()

        if "list" in text_lower or "all orders" in text_lower or "my orders" in text_lower:
            result = list_orders()
        elif "status" in text_lower or "get order" in text_lower or "find order" in text_lower:
            # Extract order ID
            import re
            match = re.search(r"ORD-[A-Za-z0-9]+", user_text, re.IGNORECASE)
            if match:
                result = get_order(match.group())
            else:
                result = json.dumps({"error": "Please provide an order ID (e.g., ORD-XXXXXXXX)"})
        elif "order" in text_lower or "place" in text_lower or "buy" in text_lower or "purchase" in text_lower:
            items = _parse_order_items(user_text)
            result = create_order(items)
        else:
            result = json.dumps({
                "message": "I can help with orders. Try: create an order, list orders, or check order status.",
                "available_commands": ["create order", "list orders", "get order <ORDER_ID>"],
            })

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=new_text_artifact(name="order_result", text=result),
            )
        )

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                final=True,
                status=TaskStatus(state=TaskState.completed),
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception("cancel not supported")
