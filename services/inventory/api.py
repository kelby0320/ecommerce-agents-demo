from fastapi import FastAPI, HTTPException

from db import get_connection

api_app = FastAPI(title="Inventory API", version="0.1.0")


@api_app.get("/products")
def get_products(q: str = ""):
    """Search the product catalog. Returns all products when no query is given."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if q:
                cur.execute(
                    "SELECT * FROM products WHERE name ILIKE %s OR category ILIKE %s OR sku ILIKE %s ORDER BY name",
                    [f"%{q}%", f"%{q}%", f"%{q}%"],
                )
            else:
                cur.execute("SELECT * FROM products ORDER BY name")
            return cur.fetchall()


@api_app.get("/products/{sku}")
def get_product_by_sku(sku: str):
    """Get full details for a product by SKU."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE sku = %s", [sku.upper()])
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Product {sku} not found")
    return row


@api_app.get("/products/{sku}/stock")
def get_stock(sku: str):
    """Check stock availability for a product by SKU."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sku, name, stock, price, stock > 0 AS in_stock FROM products WHERE sku = %s",
                [sku.upper()],
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Product {sku} not found")
    return row
