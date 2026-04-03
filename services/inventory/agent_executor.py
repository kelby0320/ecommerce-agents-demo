from __future__ import annotations

import decimal
import json
import re

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

from db import get_agent_connection

_anthropic = anthropic.AsyncAnthropic()

_SYSTEM_PROMPT = """You are a SQL query generator for a PostgreSQL inventory database.

Schema:
  products(
    sku       VARCHAR PRIMARY KEY,
    name      VARCHAR,
    price     NUMERIC,
    stock     INTEGER,
    category  VARCHAR
  )

Generate a single SELECT query answering the user's question.
Rules:
- SELECT only. No INSERT, UPDATE, DELETE, DROP, or other mutations.
- No semicolons at the end.
Return ONLY the SQL query, no explanation or markdown."""


class InventoryAgentExecutor(AgentExecutor):
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

        query = user_text

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                final=False,
                status=TaskStatus(
                    state=TaskState.working,
                    message=new_agent_text_message("Generating SQL query..."),
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
            raw = response.content[0].text.strip()
            # Strip markdown code fences if present
            raw = re.sub(r"```\w*\n?", "", raw).strip()
            select_idx = raw.upper().find("SELECT")
            if select_idx == -1:
                raise ValueError(f"Expected SELECT, got: {raw[:100]}")
            sql = raw[select_idx:].strip().rstrip(";")

            async with get_agent_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    rows = await cur.fetchall()

            result = json.dumps(rows, default=lambda o: float(o) if isinstance(o, decimal.Decimal) else str(o))
        except Exception as exc:
            result = json.dumps({"error": str(exc)})

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
