import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from db import get_connection

api_app = FastAPI(title="Orders API", version="0.1.0")


class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float = 0.0


class CreateOrderRequest(BaseModel):
    items: list[OrderItem]
    user_id: str = "00000000-0000-0000-0000-000000000000"


@api_app.post("/orders", status_code=201)
def post_order(body: CreateOrderRequest):
    """Create a new order."""
    items = [item.model_dump() for item in body.items]
    order_id = str(uuid.uuid4())
    total = sum(i["price"] * i["quantity"] for i in items)
    created_at = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO orders (order_id, user_id, status, total, created_at)
                   VALUES (%s, %s, 'pending', %s, %s)""",
                [order_id, body.user_id, round(total, 2), created_at],
            )
            for item in items:
                cur.execute(
                    """INSERT INTO order_items (order_id, name, quantity, price)
                       VALUES (%s, %s, %s, %s)""",
                    [order_id, item["name"], item["quantity"], item["price"]],
                )

    return {
        "order_id": order_id,
        "items": items,
        "status": "pending",
        "total": round(total, 2),
        "created_at": created_at.isoformat(),
    }


@api_app.get("/orders")
def get_orders():
    """List all orders with their items."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT o.order_id, o.user_id, o.status, o.total, o.created_at,
                          COALESCE(
                            json_agg(
                              json_build_object('name', oi.name, 'quantity', oi.quantity, 'price', oi.price)
                            ) FILTER (WHERE oi.id IS NOT NULL),
                            '[]'
                          ) AS items
                   FROM orders o
                   LEFT JOIN order_items oi ON o.order_id = oi.order_id
                   GROUP BY o.order_id, o.user_id, o.status, o.total, o.created_at
                   ORDER BY o.created_at DESC"""
            )
            rows = cur.fetchall()
    return {"orders": rows, "total_count": len(rows)}


@api_app.get("/orders/{order_id}")
def get_order_by_id(order_id: str):
    """Get a specific order by ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE order_id = %s", [order_id])
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            cur.execute(
                "SELECT name, quantity, price FROM order_items WHERE order_id = %s ORDER BY name",
                [order_id],
            )
            order["items"] = cur.fetchall()
    return order
