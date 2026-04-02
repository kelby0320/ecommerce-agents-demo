from __future__ import annotations

import json

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

PRODUCTS: dict[str, dict] = {
    "SKU001": {
        "name": "Wireless Mouse",
        "price": 29.99,
        "stock": 150,
        "category": "electronics",
    },
    "SKU002": {
        "name": "USB-C Hub",
        "price": 49.99,
        "stock": 45,
        "category": "electronics",
    },
    "SKU003": {
        "name": "Mechanical Keyboard",
        "price": 89.99,
        "stock": 0,
        "category": "electronics",
    },
    "SKU004": {
        "name": "Laptop Stand",
        "price": 39.99,
        "stock": 73,
        "category": "accessories",
    },
    "SKU005": {
        "name": "Webcam HD",
        "price": 59.99,
        "stock": 22,
        "category": "electronics",
    },
}


def search_products(query: str) -> str:
    query_lower = query.lower()
    matches = []
    for sku, product in PRODUCTS.items():
        if (
            query_lower in product["name"].lower()
            or query_lower in product["category"].lower()
            or query_lower in sku.lower()
        ):
            matches.append({"sku": sku, **product})

    if not matches:
        # Return all products if no specific match
        matches = [{"sku": sku, **p} for sku, p in PRODUCTS.items()]

    return json.dumps(matches, indent=2)


def check_stock(sku: str) -> str:
    sku_upper = sku.upper()
    if sku_upper in PRODUCTS:
        p = PRODUCTS[sku_upper]
        in_stock = p["stock"] > 0
        return json.dumps(
            {
                "sku": sku_upper,
                "name": p["name"],
                "stock": p["stock"],
                "in_stock": in_stock,
                "price": p["price"],
            }
        )
    return json.dumps({"error": f"Product {sku} not found"})


def get_product(sku: str) -> str:
    sku_upper = sku.upper()
    if sku_upper in PRODUCTS:
        return json.dumps({"sku": sku_upper, **PRODUCTS[sku_upper]})
    return json.dumps({"error": f"Product {sku} not found"})


class InventoryAgentExecutor(AgentExecutor):
    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)

        # Extract text from the incoming message
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
                    message=new_agent_text_message(
                        "Looking up inventory..."
                    ),
                ),
            )
        )

        # Simple intent parsing
        text_lower = user_text.lower()
        if "stock" in text_lower or "available" in text_lower:
            # Try to find a SKU or product name
            for sku in PRODUCTS:
                if sku.lower() in text_lower:
                    result = check_stock(sku)
                    break
            else:
                # Search by product name keywords
                for sku, p in PRODUCTS.items():
                    if p["name"].lower().split()[0].lower() in text_lower:
                        result = check_stock(sku)
                        break
                else:
                    result = search_products(user_text)
        elif "product" in text_lower and any(
            sku.lower() in text_lower for sku in PRODUCTS
        ):
            for sku in PRODUCTS:
                if sku.lower() in text_lower:
                    result = get_product(sku)
                    break
        else:
            result = search_products(user_text)

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=new_text_artifact(name="inventory_result", text=result),
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
