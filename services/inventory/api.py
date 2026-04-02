import json

from fastapi import FastAPI, HTTPException

from agent_executor import check_stock, get_product, search_products

api_app = FastAPI(title="Inventory API", version="0.1.0")


@api_app.get("/products")
def get_products(q: str = ""):
    """Search the product catalog. Returns all products when no query is given."""
    return json.loads(search_products(q))


@api_app.get("/products/{sku}")
def get_product_by_sku(sku: str):
    """Get full details for a product by SKU."""
    result = json.loads(get_product(sku))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@api_app.get("/products/{sku}/stock")
def get_stock(sku: str):
    """Check stock availability for a product by SKU."""
    result = json.loads(check_stock(sku))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
