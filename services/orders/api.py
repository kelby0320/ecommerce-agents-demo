import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent_executor import create_order, get_order, list_orders

api_app = FastAPI(title="Orders API", version="0.1.0")


class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float = 0.0


class CreateOrderRequest(BaseModel):
    items: list[OrderItem]


@api_app.post("/orders", status_code=201)
def post_order(body: CreateOrderRequest):
    """Create a new order."""
    items = [item.model_dump() for item in body.items]
    return json.loads(create_order(items))


@api_app.get("/orders")
def get_orders():
    """List all orders."""
    return json.loads(list_orders())


@api_app.get("/orders/{order_id}")
def get_order_by_id(order_id: str):
    """Get a specific order by ID."""
    result = json.loads(get_order(order_id))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
