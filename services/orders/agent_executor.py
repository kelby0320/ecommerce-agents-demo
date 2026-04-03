from __future__ import annotations

import decimal
import json
import re
import uuid
from datetime import datetime, timezone

import anthropic

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

from db import get_agent_connection, get_connection

_anthropic = anthropic.AsyncAnthropic()

_SYSTEM_PROMPT = """You are an assistant for a PostgreSQL orders database.

Schema:
  orders(
    order_id   UUID PRIMARY KEY,
    user_id    UUID,
    status     VARCHAR,
    total      NUMERIC,
    created_at TIMESTAMPTZ
  )
  order_items(
    id        UUID PRIMARY KEY,
    order_id  UUID REFERENCES orders(order_id),
    name      VARCHAR,
    quantity  INTEGER,
    price     NUMERIC
  )

The user wants to either read order information or create a new order.

If the user wants to READ orders (list, check status, find order, etc.):
  Generate a single SELECT query. Join order_items when item details are needed.
  Rules: SELECT only. No semicolons. Do NOT add user_id conditions — RLS handles that.
  Return ONLY the SQL.

If the user wants to CREATE an order:
  Return JSON exactly like this (no explanation):
  {"action": "create_order", "items": [{"name": "item name", "quantity": 1, "price": 0.0}]}"""


def _parse_message(text: str) -> tuple[str, str]:
    """Return (user_id, query). user_id is '' if not present."""
    if text.startswith("[user_id:"):
        end = text.index("]")
        return text[9:end], text[end + 2:]
    return "", text


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

        user_id, query = _parse_message(user_text)

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

        try:
            response = await _anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": query}],
            )
            llm_output = response.content[0].text.strip()
            # Strip markdown code fences if present
            llm_output = re.sub(r"```\w*\n?", "", llm_output).strip()

            # Find SELECT or JSON regardless of any preamble the LLM adds
            upper = llm_output.upper()
            select_idx = upper.find("SELECT")
            json_idx = llm_output.find("{")
            is_sql = select_idx != -1 and (json_idx == -1 or select_idx < json_idx)

            if is_sql:
                sql = llm_output[select_idx:].strip().rstrip(";")
                async with get_agent_connection(user_id) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(sql)
                        rows = await cur.fetchall()
                result = json.dumps(rows, default=lambda o: float(o) if isinstance(o, decimal.Decimal) else str(o))
            else:
                json_str = llm_output[json_idx:] if json_idx != -1 else llm_output
                parsed = json.loads(json_str)
                if parsed.get("action") == "create_order":
                    items = parsed.get("items", [])
                    order_id = str(uuid.uuid4())
                    total = sum(
                        float(i.get("price", 0)) * int(i.get("quantity", 1))
                        for i in items
                    )
                    created_at = datetime.now(timezone.utc)

                    with get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """INSERT INTO orders (order_id, user_id, status, total, created_at)
                                   VALUES (%s, %s, 'pending', %s, %s)""",
                                [order_id, user_id or str(uuid.uuid4()), round(total, 2), created_at],
                            )
                            for item in items:
                                cur.execute(
                                    """INSERT INTO order_items (order_id, name, quantity, price)
                                       VALUES (%s, %s, %s, %s)""",
                                    [order_id, item["name"], item.get("quantity", 1), item.get("price", 0)],
                                )

                    result = json.dumps({
                        "order_id": order_id,
                        "items": items,
                        "status": "pending",
                        "total": round(total, 2),
                        "created_at": created_at.isoformat(),
                    })
                else:
                    result = json.dumps({"error": "Unexpected LLM response", "raw": llm_output[:200]})
        except Exception as exc:
            result = json.dumps({"error": str(exc)})

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
