import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.applications import Starlette
from starlette.routing import Mount

import db
from agent_executor import InventoryAgentExecutor
from api import api_app

db.init_db(os.environ["DATABASE_URL"])

agent_card = AgentCard(
    name="Inventory Agent",
    description="Manages product inventory. Can search products, check stock levels, and retrieve product details.",
    url="http://localhost:9001/a2a",
    version="0.1.0",
    skills=[
        AgentSkill(
            id="search_products",
            name="Search Products",
            description="Search the product catalog by name, category, or SKU. Returns matching products with price and stock info.",
            tags=["inventory", "search", "products"],
            examples=[
                "Show me all electronics",
                "Search for mouse",
                "What products do you have?",
            ],
        ),
        AgentSkill(
            id="check_stock",
            name="Check Stock",
            description="Check if a specific product is in stock and how many units are available.",
            tags=["inventory", "stock", "availability"],
            examples=[
                "Is the mechanical keyboard in stock?",
                "How many wireless mice are available?",
                "Check stock for SKU001",
            ],
        ),
    ],
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text"],
    default_output_modes=["text"],
)

request_handler = DefaultRequestHandler(
    agent_executor=InventoryAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

a2a_app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

app = Starlette(
    routes=[
        Mount("/api", app=api_app),
        Mount("/a2a", app=a2a_app.build()),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)
