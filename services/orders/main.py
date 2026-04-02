import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import OrdersAgentExecutor

agent_card = AgentCard(
    name="Orders Agent",
    description="Manages customer orders. Can create new orders, retrieve order details, and list all orders.",
    url="http://localhost:9002",
    version="0.1.0",
    skills=[
        AgentSkill(
            id="create_order",
            name="Create Order",
            description="Create a new order with specified items and quantities.",
            tags=["orders", "create", "purchase"],
            examples=[
                "Order 2 wireless mice",
                "Place an order for 1 USB-C hub and 1 webcam",
                "Buy 3 laptop stands",
            ],
        ),
        AgentSkill(
            id="get_order",
            name="Get Order",
            description="Retrieve details of a specific order by its order ID.",
            tags=["orders", "status", "lookup"],
            examples=[
                "What's the status of order ORD-ABC12345?",
                "Get order ORD-ABC12345",
            ],
        ),
        AgentSkill(
            id="list_orders",
            name="List Orders",
            description="List all orders that have been placed.",
            tags=["orders", "list", "history"],
            examples=[
                "Show me all orders",
                "List my orders",
                "What orders have been placed?",
            ],
        ),
    ],
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text"],
    default_output_modes=["text"],
)

request_handler = DefaultRequestHandler(
    agent_executor=OrdersAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

if __name__ == "__main__":
    uvicorn.run(app.build(), host="0.0.0.0", port=9002)
